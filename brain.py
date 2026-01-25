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
    # workspace_path = "/home/code/workspace"  # Forcing to default workspace for now

    
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
async def manage_file(path: str, content: str = None, action: str = "write"):
    """
    Manages files - read or write operations.
    
    IMPORTANT: For 'write' action, changes are APPLIED DIRECTLY to the file!
    The changes will be tracked and shown in the sidebar with diff view and revert options.
    
    Args:
        path: File path (relative or absolute)
        content: Content to write (required for write action)
        action: 'write' to apply file changes, 'read' to read file contents
    
    Returns: Success message for write, file contents for read, or error message
    """
    try:
        # Resolve path relative to workspace
        workspace_path = get_workspace_path()
        original_path = path
        if not os.path.isabs(path):
            path = os.path.join(workspace_path, path)
        
        file_name = os.path.basename(path)
        
        if action == "write":
            if content is None:
                return "Error: content parameter is required for write action"
            
            # Check if file exists to determine if it's an edit or new file
            file_exists = os.path.exists(path)
            
            if file_exists:
                # Notify UI about editing
                await broadcast_log(f"✏️ Editing: {file_name}")
                
                # Read existing content for diff and backup
                with open(path, "r") as f:
                    old_content = f.read()
                
                # Check if content is actually different
                if old_content == content:
                    return f"✅ No changes needed - {path} already has this content"
                
                # Generate diff preview
                import difflib
                diff_lines = list(difflib.unified_diff(
                    old_content.splitlines(keepends=True),
                    content.splitlines(keepends=True),
                    fromfile=f"{path} (original)",
                    tofile=f"{path} (modified)",
                    lineterm=''
                ))
                diff_text = '\n'.join(diff_lines)
                
                # APPLY THE CHANGE DIRECTLY
                with open(path, "w") as f:
                    f.write(content)
                
                # Store for tracking and potential revert
                from utils import store_applied_change, notify_applied_change, broadcast_applied_change
                change_id = store_applied_change(path, old_content, content, diff_text, is_new_file=False)
                
                # Broadcast immediately (async)
                await broadcast_applied_change(change_id)
                
                await broadcast_log(f"✅ Edited: {file_name}")
                
                return f"✅ File updated: {path}\n\n📝 Changes applied! You can view diff or revert in the sidebar.\n\nDiff preview:\n{diff_text[:500]}{'...' if len(diff_text) > 500 else ''}"
            
            else:
                # Notify UI about creating
                await broadcast_log(f"📄 Creating: {file_name}")
                
                # New file - create directory if needed
                dir_path = os.path.dirname(path)
                if dir_path and not os.path.exists(dir_path):
                    os.makedirs(dir_path, exist_ok=True)
                
                # CREATE THE FILE DIRECTLY
                with open(path, "w") as f:
                    f.write(content)
                
                # Store for tracking
                from utils import store_applied_change, broadcast_applied_change
                change_id = store_applied_change(path, "", content, f"New file created: {path}", is_new_file=True)
                
                # Broadcast immediately (async)
                await broadcast_applied_change(change_id)
                
                await broadcast_log(f"✅ Created: {file_name}")
                
                preview = content[:300] + ("..." if len(content) > 300 else "")
                return f"✅ File created: {path}\n\n📝 New file created! You can view or delete in the sidebar.\n\nPreview:\n{preview}"

        elif action == "read":
            if not os.path.exists(path):
                return f"❌ Error: File '{path}' does not exist"
            
            # Notify UI about reading
            await broadcast_log(f"📖 Reading: {file_name}")
            
            with open(path, "r") as f:
                content = f.read()
            
            await broadcast_log(f"✓ Read: {file_name} ({len(content)} chars)")
            
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

# System prompt for fully autonomous execution - understand and execute
SYSTEM_PROMPT = """You are a fully autonomous coding assistant. You understand what the user wants and execute immediately.

🧠 UNDERSTAND FIRST, THEN ACT:
1. Parse the user's request
2. State your understanding: "🎯 I understand you want me to [action]"
3. Execute immediately without asking
4. Report results

📋 RESPONSE FORMAT:
"🎯 I understand you want me to [what user wants].

📋 Proceeding with:
• Step 1
• Step 2
• Step 3

[Execute all steps]

✅ Done: [summary of what was completed]"

⚡ EXECUTION RULES:
- NEVER ask questions
- NEVER wait for confirmation
- NEVER ask "Should I proceed?"
- Just understand → plan → execute → report

🔍 UNDERSTANDING USER INTENT:

"run app.py" → User wants to execute the Python script
"create react app" → User wants a new React project set up
"add login" → User wants authentication functionality
"fix the bug" → User wants the error resolved
"make it faster" → User wants performance optimization
"delete temp" → User wants the temp folder removed
"show files" → User wants to see directory contents
"install dependencies" → User wants packages installed

📝 FILE & COMMAND EXECUTION:
- All file operations → Execute directly
- All commands → Run directly  
- Scripts needing input → Pipe defaults automatically
- Errors → Fix and retry automatically

🏗️ PROJECT ACTIONS:
After understanding what user wants:
1. Execute all necessary steps
2. Handle dependencies automatically
3. Run build/start if appropriate
4. Report completion

❌ ERROR AUTO-FIX:
1. Understand the error
2. Fix silently
3. Retry
4. Report final result

📚 EXAMPLES:

User: "create a react app"
You: "🎯 I understand you want me to create a new React application.

📋 Proceeding with:
• Creating React app with Vite
• Installing dependencies
• Starting development server"
[Execute all steps]
"✅ Done: React app created at ./my-app and running on http://localhost:5173"

User: "run the calculator"
You: "🎯 I understand you want me to run calculator.py.

📋 Proceeding with:
• Reading calculator.py to check requirements
• Running with sample inputs (10, 20)"
[Execute]
"✅ Done: Calculator output: 10 + 20 = 30"

User: "add a dark mode toggle"
You: "🎯 I understand you want me to add dark mode functionality.

📋 Proceeding with:
• Creating theme toggle component
• Adding CSS variables for dark/light themes
• Updating App.js with theme state"
[Execute all file operations]
"✅ Done: Dark mode toggle added to the application"

User: "fix the error"
You: "🎯 I understand you want me to fix the error in the code.

📋 Proceeding with:
• Analyzing the error
• Applying fix to line 42
• Re-running to verify"
[Execute]
"✅ Done: Fixed TypeError - added null check on line 42"

User: "list all python files"
You: "🎯 I understand you want me to find all Python files.

📋 Proceeding with:
• Searching for *.py files"
[Execute: find . -name "*.py"]
"✅ Done: Found 5 Python files: app.py, utils.py, config.py, test.py, main.py"

REMEMBER: 
- Understand what user wants
- State your understanding clearly  
- Execute immediately
- Never ask questions
- Report results

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
