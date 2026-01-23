import os
import subprocess
import asyncio
from typing import Annotated, TypedDict, List

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

# Import broadcast_log, workspace path, and process tracking from utils
from utils import broadcast_log, get_workspace_path as _get_workspace_path, running_processes

# -------------------------------------------------
# 1. Define Tools
# -------------------------------------------------
# @tool
# def execute_terminal(command: str):
#     """Executes a shell command and returns the output."""
#     try:
#         result = subprocess.run(
#             command,
#             shell=True,
#             capture_output=True,
#             text=True,
#             timeout=30
#         )
#         return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
#     except Exception as e:
#         return f"Error: {str(e)}"

def get_workspace_path():
    """Get the current workspace path from utils (set by server.py)"""
    workspace = _get_workspace_path()
    if workspace and os.path.exists(workspace):
        return workspace
    return os.getcwd()

@tool
async def execute_terminal(command: str):
    """
    Executes a shell command and streams stdout/stderr to the UI.
    Supports interactive input - use the input field in the terminal UI to send input.
    
    CRITICAL RULES:
    1. This tool should ONLY be called AFTER user confirmation
    2. The agent must have already READ any script files being executed
    3. The agent must have analyzed input requirements
    4. The command may include piped input: echo 'data' | python3 script.py
    
    The agent must THINK and PLAN before calling this tool.
    """
    import uuid
    process_id = str(uuid.uuid4())[:8]
    
    # Get workspace path from VS Code
    workspace_path = get_workspace_path()
    
    await broadcast_log(f"▶️ Executing: {command}")
    await broadcast_log(f"📂 In directory: {workspace_path}")
    await broadcast_log(f"🆔 Process ID: {process_id}")
    
    # Create process with stdin support for interactive commands
    process = await asyncio.create_subprocess_shell(
        command,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=workspace_path
    )
    
    # Store process info for input/kill support
    running_processes[process_id] = {
        "process": process,
        "command": command,
        "workspace": workspace_path
    }
    
    # Notify UI that process started (for showing input controls)
    await broadcast_process_event("start", process_id, command)

    stdout_lines = []
    stderr_lines = []
    
    # Read stdout
    async def read_stdout():
        while True:
            try:
                line = await process.stdout.readline()
                if not line:
                    break
                msg = line.decode().strip()
                if msg:
                    stdout_lines.append(msg)
                    await broadcast_log(f"  {msg}")
            except Exception:
                break
    
    # Read stderr
    async def read_stderr():
        while True:
            try:
                line = await process.stderr.readline()
                if not line:
                    break
                msg = line.decode().strip()
                if msg:
                    stderr_lines.append(msg)
                    await broadcast_log(f"  ❌ {msg}")
            except Exception:
                break
    
    # Run both simultaneously
    try:
        await asyncio.gather(read_stdout(), read_stderr())
        await process.wait()
    except Exception as e:
        await broadcast_log(f"⚠️ Process error: {e}")
    
    # Clean up process tracking
    if process_id in running_processes:
        del running_processes[process_id]
    
    # Notify UI that process ended
    await broadcast_process_event("end", process_id, command)
    
    # Prepare result
    exit_code = process.returncode if process.returncode is not None else -1
    result = {
        "stdout": "\n".join(stdout_lines) if stdout_lines else "",
        "stderr": "\n".join(stderr_lines) if stderr_lines else "",
        "exit_code": exit_code
    }
    
    if exit_code == 0:
        await broadcast_log(f"✅ Command completed successfully: {command}")
        if stdout_lines:
            return f"Command executed successfully.\nOutput:\n{result['stdout']}"
        else:
            return "Command executed successfully (no output produced)."
    elif exit_code == -15 or exit_code == 130:  # SIGTERM or SIGINT
        await broadcast_log(f"🛑 Command was terminated: {command}")
        return "Command was terminated by user."
    else:
        await broadcast_log(f"❌ Command failed with exit code {exit_code}: {command}")
        error_msg = f"Command failed with exit code {exit_code}.\n"
        if stderr_lines:
            error_msg += f"Error:\n{result['stderr']}\n"
        if stdout_lines:
            error_msg += f"Output:\n{result['stdout']}"
        return error_msg


async def broadcast_process_event(event_type: str, process_id: str, command: str):
    """Broadcast process start/end events to UI"""
    from utils import connected_clients
    
    message = {
        "type": f"process_{event_type}",
        "process_id": process_id,
        "command": command
    }
    
    for ws in connected_clients:
        try:
            await ws.send_json(message)
        except Exception:
            pass



@tool
def manage_file(path: str, content: str = None, action: str = "write"):
    """
    Manages files - read or write operations.
    
    IMPORTANT: For 'write' action, this will PROPOSE changes that need user approval!
    The changes will be shown as a diff with accept/reject options.
    
    Args:
        path: File path (relative or absolute)
        content: Content to write (required for write action)
        action: 'write' to propose file changes, 'read' to read file contents
    
    Returns: Success message for write, file contents for read, or error message
    """
    try:
        # Resolve path relative to workspace
        workspace_path = get_workspace_path()
        if not os.path.isabs(path):
            path = os.path.join(workspace_path, path)
        
        if action == "write":
            if content is None:
                return "Error: content parameter is required for write action"
            
            # Check if file exists to determine if it's an edit or new file
            file_exists = os.path.exists(path)
            
            if file_exists:
                # Read existing content for diff
                with open(path, "r") as f:
                    old_content = f.read()
                
                # Generate diff preview
                import difflib
                diff_lines = list(difflib.unified_diff(
                    old_content.splitlines(keepends=True),
                    content.splitlines(keepends=True),
                    fromfile=f"{path} (current)",
                    tofile=f"{path} (proposed)",
                    lineterm=''
                ))
                
                if not diff_lines:
                    return f"✅ No changes needed - {path} already has this content"
                
                diff_text = '\n'.join(diff_lines)
                
                # Store pending change for approval
                from utils import store_pending_change, notify_file_change
                change_id = store_pending_change(path, old_content, content, diff_text)
                
                # Notify about pending change (sync version)
                notify_file_change(change_id, path)
                
                return f"📝 File edit proposed for {path}\n\nDiff preview:\n{diff_text}\n\n⚠️ This change requires your approval. Please review the diff in the UI."
            
            else:
                # New file - create directory if needed
                dir_path = os.path.dirname(path)
                if dir_path and not os.path.exists(dir_path):
                    os.makedirs(dir_path, exist_ok=True)
                
                # For new files, store as pending change too
                from utils import store_pending_change, notify_file_change
                change_id = store_pending_change(path, "", content, f"New file: {path}")
                
                # Notify about pending change (sync version)
                notify_file_change(change_id, path, is_new=True)
                
                preview = content[:500] + ("..." if len(content) > 500 else "")
                return f"📝 New file proposed: {path}\n\nPreview:\n{preview}\n\n⚠️ This change requires your approval."

        elif action == "read":
            if not os.path.exists(path):
                return f"❌ Error: File '{path}' does not exist"
            
            with open(path, "r") as f:
                content = f.read()
            return content if content else "(File is empty)"
        
        else:
            return f"❌ Error: Invalid action '{action}'. Use 'read' or 'write'"
    
    except Exception as e:
        return f"❌ Error: {str(e)}"


@tool
def find_file(filename: str, search_dir: str = "."):
    """
    Searches for a file by name in the given directory and its subdirectories.
    Returns the full path(s) if found, or a message if not found.
    
    Args:
        filename: Name of the file to search for (e.g., 'app.py')
        search_dir: Directory to start the search from (default is current directory)
    """
    import glob
    
    # Make search_dir absolute relative to workspace
    workspace_path = get_workspace_path()
    if not os.path.isabs(search_dir):
        search_dir = os.path.join(workspace_path, search_dir) if search_dir != "." else workspace_path
    
    # Search for the file recursively
    pattern = os.path.join(search_dir, "**", filename)
    matches = glob.glob(pattern, recursive=True)
    
    if matches:
        return f"Found file(s):\n" + "\n".join(matches)
    else:
        return f"File '{filename}' not found in '{search_dir}' or its subdirectories."


tools = [execute_terminal, manage_file, find_file]
tool_node = ToolNode(tools)

# -------------------------------------------------
# 2. State Definition
# -------------------------------------------------
class State(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]


# -------------------------------------------------
# 3. Azure OpenAI Configuration
# -------------------------------------------------
AZURE_ENDPOINT = os.getenv(
    "AZURE_OPENAI_ENDPOINT",
    "https://iamneo-qb.openai.azure.com/"
)

AZURE_API_KEY = os.getenv(
    "AZURE_OPENAI_API_KEY",
    "BseWgixIxbzsRMTI9XcdwIS39aVLQT791lDu1gi3rBBFngSSOH7vJQQJ99BIACYeBjFXJ3w3AAABACOGv3VO"
)

AZURE_DEPLOYMENT = os.getenv(
    "AZURE_OPENAI_DEPLOYMENT",
    "gpt-5-mini"
)

AZURE_API_VERSION = "2024-12-01-preview"


# -------------------------------------------------
# 4. Create Azure LLM (Tool-Enabled)
# -------------------------------------------------

# System prompt to enforce thinking, planning, and smart execution
SYSTEM_PROMPT = """You are a highly intelligent coding assistant with access to terminal commands and file operations.

🧠 THINKING & PLANNING PHASE (ALWAYS START HERE):
Before taking ANY action, you MUST think through the task:

1. **Analyze the Request**: What is the user asking for?
2. **Plan the Approach**: What steps are needed?
3. **Identify Risks**: What could go wrong?
4. **Explain Your Plan**: Tell the user what you're going to do

Format your thinking like this:
"🤔 **Thinking & Planning:**
- Task: [what user wants]
- Approach: [your strategy]
- Steps: [numbered list of steps]
- Considerations: [potential issues]

📋 **My Plan:**
1. [Step 1]
2. [Step 2]
3. [Step 3]"

🔍 SMART FILE EXECUTION WORKFLOW:
Before running ANY Python/script file, you MUST:

1. **Read the file first** using manage_file(action="read")
2. **Analyze the code**:
   - Does it use input(), raw_input(), or sys.stdin.read()?
   - Does it require command-line arguments?
   - Does it need environment variables?
   - Are there any dependencies that might be missing?
3. **Handle Input Requirements**:
   - If file needs input: Ask user "What values should I provide for [input prompt]?"
   - If user provides values: Use echo to pipe input → "echo 'value' | python3 script.py"
   - If multiple inputs: Use "echo -e 'val1\\nval2' | python3 script.py"
4. **Then ask permission** to run with proper input handling

🔗 CASCADING FILE CHANGES (CRITICAL!):
After editing ANY file, you MUST:

1. **Identify Related Files**:
   - If editing a component: Check files that import/use it
   - If editing an interface/type: Check all implementations
   - If editing a config file: Check files that use those configs
   - If editing a function: Check all callers of that function
   - If editing package.json/requirements.txt: Note new dependencies

2. **Analyze Impact**:
   - Read each related file
   - Check if changes are needed (imports, function calls, types, etc.)
   - List what needs to be updated

3. **Apply Cascading Changes**:
   - Edit each affected file
   - Explain: "📝 Also updating [file] because [reason]"
   - Continue until all related files are consistent

4. **Example Related Files by Type**:
   - React component → Check parent components, routes, tests
   - Python module → Check files with `from module import` or `import module`
   - TypeScript interface → Check all files using that interface
   - CSS/styles → Check components using those styles
   - API endpoint → Check frontend calls, tests
   - Database model → Check migrations, queries, API handlers

🏗️ BUILD & RUN WORKFLOW (After File Changes):
After completing file edits, ALWAYS:

1. **Detect Project Type** (check for these files):
   - package.json → Node.js/React/Vue project
   - requirements.txt/setup.py → Python project
   - Cargo.toml → Rust project
   - go.mod → Go project
   - pom.xml/build.gradle → Java project
   - Makefile → Check make targets

2. **Suggest Appropriate Build Command**:
   - Node.js: `npm install && npm run build` or `npm start`
   - Python: `pip install -r requirements.txt` then `python app.py`
   - React: `npm install && npm start` or `npm run dev`
   - TypeScript: `npm run compile` or `tsc`

3. **Ask for Build/Run Approval**:
   "✅ Files updated successfully!

   📦 **Build Step Available:**
   I can run: `[build command]`
   
   This will: [explain what the command does]
   
   Should I proceed with the build? (yes/no)"

4. **On Build Errors - AUTO-FIX LOOP**:
   If build/run fails:
   a) **Analyze the error** - identify root cause
   b) **Fix automatically** - edit the problematic file(s)
   c) **Report**: "🔧 Fixed: [brief description of fix]"
   d) **Ask to retry**: "Should I run the build again? (yes/no)"
   e) **Repeat** until success or user cancels

⚙️ COMMAND EXECUTION WORKFLOW:
1. **Think & Plan** (explain your approach)
2. **Read file if executing script** (understand what it does)
3. **Check for input needs** (prepare stdin if needed)
4. **Ask permission**: "I need to run: `command`. Should I proceed? (yes/no)"
5. **Wait for "yes"**
6. **THEN call execute_terminal** with proper command

❌ ERROR HANDLING & AUTO-FIX:
When ANY command fails:

1. **Parse the Error**:
   - Syntax error → Identify file and line
   - Import error → Identify missing module
   - Type error → Identify type mismatch
   - Build error → Identify failing file

2. **Auto-Fix Without Asking**:
   - Read the problematic file
   - Apply the fix using manage_file
   - Report: "🔧 Fixed [error type] in [file]"

3. **Ask to Retry**:
   "Fixed! Should I run `[command]` again? (yes/no)"

4. **Common Error Fixes**:
   - ModuleNotFoundError → `pip install [module]`
   - SyntaxError → Fix the syntax in the file
   - ImportError → Add missing import or install package
   - TypeError → Fix type mismatch in code
   - FileNotFoundError → Create the missing file
   - NameError → Add missing variable/import
   - npm ERR! → `npm install` missing deps

📝 FILE OPERATIONS (No confirmation needed):
- manage_file action="read" - proceed directly
- manage_file action="write" - proceed directly  
- find_file - proceed directly

⚠️ CRITICAL RULES:
- ALWAYS think and plan first
- ALWAYS read script files before executing
- ALWAYS check for input requirements
- ALWAYS check related files after editing
- ALWAYS suggest build command after file changes
- ALWAYS auto-fix errors and ask to retry
- NEVER call execute_terminal until user confirms
- NEVER run scripts blind without understanding them
- NEVER leave related files inconsistent

📚 EXAMPLE: COMPLETE EDIT → BUILD → FIX FLOW:

User: "Add a new utility function to utils.py"

You: "🤔 **Thinking & Planning:**
- Task: Add new utility function
- Approach: Add function, check for files using utils.py, suggest running tests
- Related files to check: Any file importing from utils.py

Let me first read utils.py..."

[Read utils.py, add function]

You: "✅ Added new function `calculate_total()` to utils.py

🔍 **Checking Related Files...**
Found 3 files that import from utils.py:
- main.py
- api/handlers.py
- tests/test_utils.py

Let me check if they need updates..."

[Read and update related files as needed]

You: "📝 Updated related files:
- tests/test_utils.py - Added test for new function

✅ All files updated!

📦 **Build/Test Available:**
I can run: `python -m pytest tests/`

This will verify everything works correctly.

Should I run the tests? (yes/no)"

User: "yes"

[Run tests, if error occurs:]

You: "❌ Test failed: NameError in test_utils.py line 45

🔧 **Auto-fixing...**
The test was missing an import. Fixed!

Should I run the tests again? (yes/no)"

---

REMEMBER: Think → Plan → Edit → Check Related → Build → Fix → Retry
"""

llm = AzureChatOpenAI(
    azure_endpoint=AZURE_ENDPOINT,
    api_key=AZURE_API_KEY,
    azure_deployment=AZURE_DEPLOYMENT,
    api_version=AZURE_API_VERSION,
    # temperature=0
).bind_tools(tools)


def call_model(state: State):
    # Add system prompt on first message
    messages = state["messages"]
    if len(messages) == 1:  # First user message
        from langchain_core.messages import SystemMessage
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    
    return {"messages": [llm.invoke(messages)]}


# -------------------------------------------------
# 5. Build LangGraph Workflow
# -------------------------------------------------
workflow = StateGraph(State)

workflow.add_node("agent", call_model)
workflow.add_node("action", tool_node)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges(
    "agent",
    tools_condition,
    {
        "tools": "action",
        END: END
    }
)
workflow.add_edge("action", "agent")

app = workflow.compile(
    # Increase recursion limit to prevent GraphRecursionError
    checkpointer=None,
    debug=False
)

# Configure recursion limit
# from langgraph.pregel import RetryPolicy
app.config = {
    "recursion_limit": 50  # Increased from default 25
}

# -------------------------------------------------
# 6. Local Test
# -------------------------------------------------
if __name__ == "__main__":
    test_input = {
        "messages": [
            HumanMessage(
                content=(
                    "Create a directory called 'project_beta', "
                    "add a python file 'app.py' inside it that write a code for printing prime no., and then run it."
                )
            )
        ]
    }

    for output in app.stream(test_input):
        print(output)
