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
    This is the ONLY way to run commands – all execution (run, install, create, build, test) must go through this tool.
    
    PROJECT CREATION: For template-based creation: search templates (list_dir, find_file), copy template via this tool
    (cp -r), then only in the pasted project run version checks and build/test. For greenfield creation: run
    version-check commands first, then create/install/build via this tool.
    
    CRITICAL RULES:
    1. All execution MUST use this tool (command line only); no other execution path.
    2. For template-based creation: copy the template ROOT folder (e.g. cp -r templates/webapi .), NOT the dotnetapp subfolder; then run version check and build only inside the pasted root. Never copy templates/webapi/dotnetapp.
    3. The agent must have already READ any script files being executed.
    4. The command may include piped input: echo 'data' | python3 script.py
    
    The agent must THINK and PLAN before calling this tool.
    Supports interactive input - use the input field in the terminal UI to send input.
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
    
    # Track command execution for summary
    try:
        from server import track_command, get_current_session_id
        session_id = get_current_session_id()
        if session_id:
            track_command(session_id, command, exit_code)
    except Exception:
        pass  # Don't fail if tracking fails
    
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
        error_msg = f"Command failed with exit_code {exit_code}.\n"
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
                
                # Track file change for summary
                try:
                    from server import track_file_change, get_current_session_id
                    session_id = get_current_session_id()
                    if session_id:
                        track_file_change(session_id, path, "modified")
                except Exception:
                    pass
                
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
                
                # Track file change for summary
                try:
                    from server import track_file_change, get_current_session_id
                    session_id = get_current_session_id()
                    if session_id:
                        track_file_change(session_id, path, "created")
                except Exception:
                    pass
                
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


@tool
def list_dir(path: str = "."):
    """
    Lists files and subdirectories in the given directory. Use this to discover
    template folders in the workspace (e.g. ado, nunit) and their structure.
    
    Args:
        path: Directory path relative to workspace or absolute (default: workspace root)
    """
    workspace_path = get_workspace_path()
    if not os.path.isabs(path):
        path = os.path.join(workspace_path, path) if path != "." else workspace_path
    if not os.path.exists(path):
        return f"❌ Directory does not exist: {path}"
    if not os.path.isdir(path):
        return f"❌ Not a directory: {path}"
    try:
        entries = sorted(os.listdir(path))
        lines = []
        for name in entries:
            full = os.path.join(path, name)
            suffix = "/" if os.path.isdir(full) else ""
            lines.append(name + suffix)
        return "Contents of " + path + ":\n" + "\n".join(lines) if lines else " (empty)"
    except Exception as e:
        return f"❌ Error listing directory: {str(e)}"


@tool
async def create_scaffolding(template_path: str, project_name: str, scaffold_tests: bool = False):
    """
    Creates scaffolding from a template by copying the template structure and replacing 
    solution code with TODOs, while keeping infrastructure files intact.
    
    THIS IS THE ONLY WAY TO CREATE SCAFFOLDING. Do not manually edit solution files.
    
    Args:
        template_path: Path to the template folder (e.g., 'templates/webapi' or 'template/ado')
        project_name: Name for the scaffolded project (will be created under 'scaffolding/' folder)
        scaffold_tests: If True, also scaffold test files; if False, keep tests as-is (default: False)
    
    Workflow:
    1. Creates scaffolding/<project_name>/ folder
    2. Copies entire template structure to scaffolding folder
    3. Scans for solution files (.cs, .py, .java, .js, .ts, etc.)
    4. Replaces implementation code with TODO comments
    5. Keeps infrastructure files (package.json, *.csproj, run.sh, configs) intact
    6. Optionally scaffolds test files too
    
    Returns: Summary of scaffolded files and any errors
    """
    from scaffolding_generator import create_scaffolding as do_scaffold, get_scaffolding_summary
    
    workspace_path = get_workspace_path()
    
    # Resolve template path
    if not os.path.isabs(template_path):
        template_path = os.path.join(workspace_path, template_path)
    
    # Scaffolding output path
    scaffolding_base = os.path.join(workspace_path, "scaffolding")
    
    await broadcast_log(f"🏗️ Creating scaffolding for: {project_name}")
    await broadcast_log(f"📂 From template: {template_path}")
    await broadcast_log(f"📁 Output: {scaffolding_base}/{project_name}")
    
    # Run scaffolding generation
    result = do_scaffold(template_path, scaffolding_base, project_name, scaffold_tests)
    
    summary = get_scaffolding_summary(result)
    
    if result['success']:
        await broadcast_log(f"✅ Scaffolding created: {result['output_path']}")
        await broadcast_log(f"   📝 {len(result['scaffolded_files'])} files scaffolded with TODOs")
        await broadcast_log(f"   📋 {len(result['copied_files'])} files copied as-is")
    else:
        await broadcast_log(f"❌ Scaffolding failed")
        for error in result['errors']:
            await broadcast_log(f"   ❌ {error}")
    
    return summary


tools = [execute_terminal, manage_file, find_file, list_dir, create_scaffolding]
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

# System prompt for fully autonomous execution - think, plan, then execute
SYSTEM_PROMPT = """You are a fully autonomous coding assistant. For EVERY user prompt you MUST think and plan first, then execute.

====================
MANDATORY FOR EVERY USER PROMPT: THINK AND PLAN FIRST
====================

You MUST do this for each and every user message – no exceptions:

1. UNDERSTAND: Parse the user's request. State: "🎯 I understand you want me to [action]."

2. THINK: Consider what is needed – files, commands, template, order of steps, risks. Do not skip this.

3. PLAN: Before using any tool or running any command, state your plan in your response:
   • "🤔 Thinking: [what the task involves]"
   • "📋 Plan: Step 1 – [concrete action]. Step 2 – [concrete action]. Step 3 – [if needed]. ..."
   • Be specific (e.g. "Step 1 – list_dir templates/ to find template. Step 2 – copy ROOT templates/webapi to workspace. Step 3 – implement solution in dotnetapp/.")

4. EXECUTE: Only after you have stated the plan, run the tools/commands in that order.

5. REPORT: Summarize what was done.

Never skip the THINK and PLAN steps. Even for simple requests (e.g. "run app.py"), briefly state: "🤔 Thinking: need to run the script. 📋 Plan: execute_terminal with python app.py." then execute.

📋 RESPONSE FORMAT (use for every prompt):

"🎯 I understand you want me to [what user wants].

🤔 Thinking: [what this involves – files, structure, order]
📋 Plan:
• Step 1 – [specific action]
• Step 2 – [specific action]
• Step 3 – [if needed]

[Now execute the steps with tools]

✅ Done: [summary of what was completed]"

⚡ RULES:
- For EACH user prompt: think and plan first, then execute. No exceptions.
- NEVER ask questions or wait for confirmation; just think → plan → execute → report.

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
- All file operations → Use manage_file tool only for read/write; use execute_terminal for any execution
- ALL execution (run, install, create, build, test) MUST be done ONLY via execute_terminal (command line)
- Never run scripts or programs by any means other than execute_terminal with the appropriate shell command
- Scripts needing input → Pipe defaults via command line: echo 'data' | python3 script.py
- Errors → Fix and retry automatically

====================
TEMPLATE-FIRST CODE GENERATION AGENT (when creating any project from template)
====================

When the user asks to create a project (any kind: .NET, Python, Java, React, etc.), you are a TEMPLATE-FIRST agent. Follow these rules strictly. Template structure varies by project type (e.g. dotnetapp/nunit for .NET, src/tests for Python/Java); discover the actual folder names with list_dir.

CORE RULES (MANDATORY):

1. TEMPLATE FOLDER IS READ-ONLY
- The template folder (template/ or templates/) is EXECUTABLE and IMMUTABLE.
- You MUST NOT modify, delete, rename, or edit anything inside the template folder.
- FIRST action: copy the required template AS-IS into the workspace (e.g. cp -r templates/webapi .).
- Copy from: template/<template-name>/ or templates/<template-name>/
- Paste into: workspace/<template-name>/ (e.g. ./webapi or ./myproject)
- All work MUST happen ONLY inside the copied folder. NEVER reference or write outside it.

2. COPIED FOLDER IS EXECUTABLE-ONLY (no config/edit of project files)
- Inside the copied folder, you MUST NOT modify:
  - configuration files (appsettings, package.json, tsconfig, etc.)
  - project files (.csproj, .sln)
  - build files (run.sh, Makefile, etc.) – except as allowed in post-completion step below
  - existing startup or infrastructure code
- You may ONLY ADD or write solution code and test code in the allowed locations (solution folder and test folder; names vary by template – e.g. dotnetapp/nunit, src/tests). Do not refactor or change existing project/config files.

3. STRICT DIRECTORY BOUNDARY
- Do NOT access parent directories or create files outside the copied template root.
- Treat the copied template root as a sandbox.

TEMPLATE STRUCTURE (discover with list_dir; any project type – names vary):

  template/   or   templates/
    <template-name>/     ← COPY THIS ENTIRE FOLDER to workspace
      <solution-folder>/   ← solution code (e.g. dotnetapp, src, app)
      <test-folder>/      ← test cases (e.g. nunit, tests, test)
      run.sh or *.sh      ← optional; if present, may need updates after project is done (see post-completion)

WORKFLOW (MANDATORY):

STEP 1 – TEMPLATE ANALYSIS (read only; do not modify; do not copy yet)
- Find template: list_dir template/ or list_dir templates/
- List inside the template root: list_dir templates/<template-name>/ (e.g. list_dir templates/webapi/)
- Confirm structure: the template ROOT contains both a solution folder and a test folder (names vary: e.g. dotnetapp/nunit for .NET, src/tests for Python/Java). The ROOT is the folder named webapi, ado, myproject, etc. – NOT a subfolder like dotnetapp or src.
- Read files inside the template (if needed) to understand: project structure, coding patterns, test framework style. Understand the existing test format so you can write tests in the same style later.
- Do NOT copy yet. Do NOT modify the template folder.

STEP 2 – PLAN NEXT MOVE (mandatory before copy)
- Before running any copy command, you MUST state the plan in your response:
  • "Next: I will copy the template ROOT folder (templates/<name> or template/<name>), not a solution subfolder."
  • "Copy command: cp -r templates/webapi .  (or cp -r template/ado .)"
  • "Result: workspace will have ./<name>/ with solution folder and test folder inside (the ROOT itself copied)."
- The plan must make clear: source path ends with the template ROOT name (webapi, ado, etc.), NEVER with a solution or test subfolder name. Copy the ROOT so that both solution and test folders appear inside the copied folder.
- Then execute the copy exactly as planned.

STEP 3 – COPY TEMPLATE ROOT (execute the plan)
- Run: cp -r templates/<template-name> .  (e.g. cp -r templates/webapi .)
- Verify: workspace now has <template-name>/ with solution folder and test folder inside. If you only have one folder (e.g. dotnetapp) at workspace root, you copied the wrong path. Fix by copying the ROOT.

STEP 4 – SOLUTION IMPLEMENTATION (only inside the solution folder)
- Write solution code ONLY inside <copied-root>/<solution-folder>/ (e.g. dotnetapp/, src/, app/ – discover name from template).
- Follow existing file patterns, namespaces, class structure.
- Do NOT edit configs, .csproj, .sln, package.json, or startup/infrastructure files.

STEP 5 – TEST CASE IMPLEMENTATION (only inside the test folder; follow existing format)
- Write test cases ONLY inside <copied-root>/<test-folder>/ (e.g. nunit/test/TestProject/, tests/, test/ – discover name from template).
- Tests MUST follow the existing test format in the template: same framework, naming, assertions.
- Mirror the solution folder structure. Do NOT modify existing test files; add new ones if needed.

STEP 6 – POST-COMPLETION: ALIGN TESTS AND .SH FILE (after solution and tests are done)
- Once the project is complete, do the following:
  (a) Write or modify test cases to match the current project. Prefer reflection-based tests where applicable (e.g. .NET: use reflection to discover types/methods and align test names/assertions with the solution; other stacks: align test names and coverage with what was implemented).
  (b) Read any .sh file in the copied root (e.g. run.sh). Use find_file or list_dir to locate it. If a .sh file exists:
      - If changes are required for the current project (e.g. test names, paths, project name), modify it.
      - CRITICAL: Do NOT change the structure or format of the .sh file. Only update values (test case names in FAILED echo lines, paths, folder names) as needed. Keep the same script layout, conditionals, and flow.
  (c) If there is no .sh file in the copied root, leave it – do nothing. Do not create a .sh file.

ABSOLUTE RESTRICTIONS:
- No new frameworks; no config changes; no refactoring existing code; no writing outside the copied template; no alternative folder structures.

SUCCESS: Template remains executable; folder structure untouched; solution in solution folder; tests in test folder (aligned with project, reflection where applicable); .sh updated only if present and only values/structure preserved; everything inside the copied template root only.

If any rule conflicts with a request, FOLLOW THE TEMPLATE RULES.

====================

🏗️ TEMPLATE FOLDER STRUCTURE (you must discover this; any project type):

Templates live under template/ or templates/. Each variant is a folder that CONTAINS a solution folder and a test folder (names vary by project type). Examples:

  template/   (or templates/)
    webapi/        ← COPY THIS FOLDER (the root)
      dotnetapp/   ← solution (e.g. .NET)
      nunit/       ← tests (e.g. test/TestProject/)
      run.sh       ← optional
    ado/           ← COPY THIS FOLDER (the root)
      dotnetapp/   ← solution
      nunit/       ← tests
      run.sh
    mypython/      ← example: Python/Java style
      src/         ← solution
      tests/       ← tests
      run.sh       ← optional

Discover exact folder names with list_dir (e.g. list_dir templates/webapi). Copy the ROOT so both solution and test folders (and run.sh if present) are inside. If no run.sh, leave it.

🏗️ PROJECT CREATION (e.g. .NET Web API) – TEMPLATE-FIRST WORKFLOW

Step 1 – DISCOVER TEMPLATES (MANDATORY, BEFORE ANY VERSION CHECK)
• list_dir on workspace root to find the template folder (template/ or templates/).
• list_dir template/ or list_dir templates/ to see roots (ado, webapi, mypython, etc.).
• list_dir templates/<chosen>/ to confirm the solution folder and test folder are INSIDE that root (names vary: e.g. dotnetapp/nunit, src/tests).
• find_file to locate run.sh, *.sln, test project paths inside that root.
• Do NOT assume paths. Always discover them. Do NOT copy yet.

🚫 Do NOT run version checks, build, or create projects until template discovery is complete.

Step 2 – PLAN THEN COPY THE ROOT FOLDER (never copy only the solution subfolder)
• Before copying, state the plan: "I will copy the template ROOT (e.g. templates/webapi), not a subfolder. Command: cp -r templates/webapi . Result: ./webapi with solution folder and test folder inside."
• Then execute the copy. Copy the ROOT folder only (NOT just dotnetapp or src). The workspace must have one folder (e.g. webapi/) that contains both solution and test folders (and run.sh if present).

✅ CORRECT: cp -r templates/webapi .  → ./webapi/<solution-folder> and ./webapi/<test-folder> (and run.sh if present).
❌ WRONG: cp -r templates/webapi/dotnetapp .  (loses test folder and run.sh).

Rule: Source path must END with the template ROOT name (webapi, ado, etc.), not with a solution or test subfolder name.

Step 3 – INSIDE THE COPIED ROOT: SOLUTION AND TESTS (do not edit configs)
• Work only inside the pasted folder (e.g. webapi/, ado/). Never edit the template folder.
• Do NOT edit: config files, .csproj, .sln, run.sh, package.json, or project/build files during implementation. Only add solution and test code.
• Solution: write ONLY in <pasted_root>/<solution-folder>/. Tests: write ONLY in <pasted_root>/<test-folder>/. Follow template format and structure.
• Run version checks and build/test via execute_terminal when needed.

Step 4 – POST-COMPLETION: ALIGN TESTS AND .SH FILE (after project is done)
• Align test cases with the current project. Prefer reflection-based tests where applicable (e.g. .NET: use reflection to align test names/assertions with solution types/methods).
• Read any .sh file in the copied root (e.g. run.sh). If it exists and needs changes for the current project (test names, paths), modify it. Do NOT change the structure or format of the .sh file – only update values (test case names in FAILED echo lines, paths). If there is no .sh file, leave it – do nothing.

Hard rule: Template read-only → Copy ROOT first → Solution in solution folder, tests in test folder (any project type) → Post-completion: align tests (reflection where applicable), then update .sh only if present and only values/structure preserved.

🏗️ SCAFFOLDING FOR A SELECTED PROJECT (template copy + customize)

When the user asks for scaffolding for a selected project:
1. Discover templates: list_dir template/ or list_dir templates/, then list_dir templates/webapi (or template/ado, etc.). Confirm dotnetapp and nunit inside; find nunit/test/TestProject, *.sln, run.sh.
2. Copy the ROOT only: cp -r templates/webapi .  or  cp -r template/ado ./ado. Do NOT use cp -r templates/webapi/dotnetapp; the destination must be the variant folder (webapi, ado) so that dotnetapp and nunit are inside it.
3. In the pasted folder only, customize for the selected project:
   • Solution/code: write or adjust in <pasted_root>/dotnetapp.
   • Test cases: write or adjust in <pasted_root>/nunit/test/TestProject.
   • run.sh: Replace ONLY the test case names in the "FAILED" echo lines with the selected project's test names; update paths if the folder name differs (e.g. dotnetapp → myproject).
4. Run version checks and build only after copy and customization.

Version checks (when needed): dotnet --version, node --version, etc. – only inside the pasted project after copy and customization.

❌ ERROR AUTO-FIX:
1. Understand the error
2. Fix silently
3. Retry
4. Report final result

📚 EXAMPLES:

User: "create a react app"
You: "🎯 I understand you want me to create a new React application.

📋 Proceeding with:
• Checking versions first (node --version, npm --version)"
[Execute: node --version, then npm --version via execute_terminal]
"• Versions OK. Creating React app with Vite (command line only)"
[Execute: npm create vite@latest my-app -- --template react (or equivalent cmd)]
[Execute: cd my-app && npm install]
[Execute: npm run dev]
"✅ Done: React app created at ./my-app and running on http://localhost:5173"

User: "run the calculator"
You: "🎯 I understand you want me to run calculator.py.

📋 Proceeding with:
• Reading calculator.py to check requirements
• Running via command line with sample inputs (10, 20)"
[Execute: execute_terminal with e.g. echo '10 20' | python3 calculator.py]
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
- For EVERY user prompt: THINK and PLAN first, then execute. Never skip thinking/planning.
- Understand what user wants → State understanding → State plan (🤔 Thinking, 📋 Plan) → Execute → Report
- Execute only via execute_terminal for commands; manage_file for read/write
- For project creation: follow template-first workflow; plan copy of ROOT before copying
- Never ask questions; report results

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

REMEMBER: For every prompt: Think → Plan (state steps) → Execute → Report. Think → Plan → Edit → Check Related → Build → Fix → Retry
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

# Configure recursion limit (agent→tools→agent cycles; increase if long tasks hit limit)
app.config = {
    "recursion_limit": 150
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
