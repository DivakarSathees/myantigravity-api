from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
import json
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from brain import app as agent_app  # Import your LangGraph app
from langchain_core.messages import HumanMessage, AIMessage
from typing import Dict, List
from uuid import uuid4

# Import shared utilities
from utils import (
    broadcast_log, connected_clients, pending_changes, broadcast_file_change, 
    process_file_change_queue, set_workspace_path, running_processes,
    start_progress_session, end_progress_session, add_progress_task, update_progress_task,
    # New applied changes system
    applied_changes, session_changes, process_applied_change_queue, 
    clear_session_changes, update_change_status, get_all_session_changes, get_applied_change
)
import os
import signal
from datetime import datetime
import re

# Session tracking for markdown generation
session_activities = {}  # session_id -> {files_changed: [], commands_run: [], request: str, response: str}
current_session_id = None  # Track current active session

def get_current_session_id():
    """Get the current active session ID"""
    return current_session_id

def sanitize_filename(text: str) -> str:
    """Convert text to a safe filename"""
    # Remove or replace unsafe characters
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '_', text)
    return text[:50]  # Limit length

def create_request_summary_markdown(session_id: str, request_text: str, response_text: str, workspace_path: str = None):
    """Create a markdown file documenting the request and changes made"""
    try:
        # Get session activities
        activities = session_activities.get(session_id, {
            'files_changed': [],
            'commands_run': [],
            'request': request_text,
            'response': response_text
        })
        
        # Create markdown content
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create filename from request
        filename_base = sanitize_filename(request_text)
        filename = f"{date_str}_{filename_base}.md"
        
        # Determine where to save
        if workspace_path and os.path.exists(workspace_path):
            summary_dir = os.path.join(workspace_path, ".neuralstack_logs")
        else:
            summary_dir = ".neuralstack_logs"
        
        os.makedirs(summary_dir, exist_ok=True)
        filepath = os.path.join(summary_dir, filename)
        
        # Build markdown content
        md_content = f"""# Request Summary

**Date:** {timestamp}  
**Session ID:** {session_id}

---

## 📝 User Request

```
{request_text}
```

---

## 🤖 Agent Response

{response_text}

---

## 📁 Files Changed

"""
        
        if activities.get('files_changed'):
            for file_change in activities['files_changed']:
                action = file_change.get('action', 'modified')
                path = file_change.get('path', 'unknown')
                md_content += f"- **{action.upper()}**: `{path}`\n"
        else:
            md_content += "*No files were modified*\n"
        
        md_content += "\n---\n\n## 🖥️ Commands Executed\n\n"
        
        if activities.get('commands_run'):
            for i, cmd in enumerate(activities['commands_run'], 1):
                command = cmd.get('command', '')
                exit_code = cmd.get('exit_code', 'N/A')
                md_content += f"{i}. **Command:** `{command}`\n"
                md_content += f"   - Exit Code: {exit_code}\n\n"
        else:
            md_content += "*No commands were executed*\n"
        
        md_content += "\n---\n\n## 📊 Summary\n\n"
        md_content += f"- **Files Modified:** {len(activities.get('files_changed', []))}\n"
        md_content += f"- **Commands Run:** {len(activities.get('commands_run', []))}\n"
        md_content += f"- **Session:** {session_id[:8]}...\n"
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"📄 Created summary: {filepath}")
        return filepath
    
    except Exception as e:
        print(f"❌ Error creating summary markdown: {e}")
        return None

def track_file_change(session_id: str, file_path: str, action: str = "modified"):
    """Track a file change for the session"""
    if session_id not in session_activities:
        session_activities[session_id] = {'files_changed': [], 'commands_run': []}
    
    session_activities[session_id]['files_changed'].append({
        'path': file_path,
        'action': action,
        'timestamp': datetime.now().isoformat()
    })

def track_command(session_id: str, command: str, exit_code: int = None):
    """Track a command execution for the session"""
    if session_id not in session_activities:
        session_activities[session_id] = {'files_changed': [], 'commands_run': []}
    
    session_activities[session_id]['commands_run'].append({
        'command': command,
        'exit_code': exit_code,
        'timestamp': datetime.now().isoformat()
    })

# Debug: Log when pending_changes is accessed
def debug_pending_changes():
    print(f"📊 Current pending changes: {list(pending_changes.keys())}")
    return pending_changes

app = FastAPI()

# Allow VS Code (which runs on a different port) to talk to this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chat history storage (session_id -> session data)
chat_sessions: Dict[str, dict] = {}

def get_or_create_session(session_id: str = None):
    """Get existing session or create new one"""
    if not session_id:
        session_id = str(uuid4())
    
    if session_id not in chat_sessions:
        chat_sessions[session_id] = {
            "id": session_id,
            "messages": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "title": "New Chat"  # Will be updated based on first message
        }
    
    return session_id, chat_sessions[session_id]

class ChatRequest(BaseModel):
    message: str
    session_id: str = None  # Optional session ID for maintaining history
    workspace_path: str = None  # VS Code workspace folder path (or scope folder when scope_path set)
    scope_path: str = None  # When set, use this folder as workspace for this request (read/list/run in this folder)

# @app.post("/chat")
# async def chat(request: ChatRequest):
#     # Initialize the agent state with the user message
#     inputs = {"messages": [HumanMessage(content=request.message)]}
    
#     # Run the agent and collect the final response
#     final_response = ""
#     async for output in agent_app.astream(inputs):
#         for key, value in output.items():
#             if key == "agent":
#                 # Get the last message content from the agent
#                 final_response = value["messages"][-1].content
    
#     return {"response": final_response}

@app.post("/chat")
async def chat(request: ChatRequest):
    global current_session_id
    
    # Get or create session
    session_id, session = get_or_create_session(request.session_id)
    
    # Set current session ID for tracking
    current_session_id = session_id
    
    # Scaffolding: use workspace root so agent can read templates; target folder is scope_path
    message_to_store = request.message
    is_scaffolding = (
        request.scope_path
        and request.workspace_path
        and "scaffolding" in (request.message or "").lower()
    )
    if is_scaffolding:
        effective_workspace = request.workspace_path
        set_workspace_path(effective_workspace)
        message_to_store = (
            f"TARGET FOLDER FOR SCAFFOLDING (create all scaffolding files here – use this absolute path when writing): {request.scope_path}\n\n"
            + request.message
        )
        await broadcast_log(f"📁 Scaffolding: using workspace for templates, target folder: {request.scope_path}")
    else:
        # Use scope_path (folder selected for / prompt) as workspace for this request so agent reads/runs in that folder
        effective_workspace = request.scope_path or request.workspace_path
        if effective_workspace:
            set_workspace_path(effective_workspace)
            if request.scope_path:
                await broadcast_log(f"📁 Working in selected folder: {request.scope_path}")
            else:
                await broadcast_log(f"📁 Working in: {request.workspace_path}")

    # Start progress tracking session
    await start_progress_session()

    # Add initial task
    analyze_task = await add_progress_task("Analyzing request", "Understanding what you need...")

    # Add user message to history
    session["messages"].append(HumanMessage(content=message_to_store))
    session["updated_at"] = datetime.now().isoformat()
    
    # Update title based on first message
    if len(session["messages"]) == 1:
        # Use first 50 chars of message as title
        session["title"] = request.message[:50] + ("..." if len(request.message) > 50 else "")
    
    await update_progress_task(analyze_task, "completed", "Request analyzed")
    
    # Create inputs with full conversation history and recursion limit
    inputs = {"messages": session["messages"].copy()}
    config = {"recursion_limit": 150}  # Allow longer agent→tool→agent chains before stopping
    final_response = ""
    
    # Track current task for updates
    current_task_id = await add_progress_task("Processing", "Agent is thinking...")
    tool_count = 0

    async for output in agent_app.astream(inputs, config=config):
        for key, value in output.items():

            # Stream agent messages
            if key == "agent":
                msg = value["messages"][-1].content
                await broadcast_log(f"🤖 Agent: {msg}")
                final_response = msg
                
                # Update progress based on message content
                if "thinking" in msg.lower() or "planning" in msg.lower():
                    await update_progress_task(current_task_id, "in_progress", "Planning approach...")
                elif "reading" in msg.lower() or "analyzing" in msg.lower():
                    await update_progress_task(current_task_id, "in_progress", "Analyzing files...")
                elif "should i proceed" in msg.lower() or "(yes/no)" in msg.lower():
                    await update_progress_task(current_task_id, "completed", "Waiting for confirmation")
                    current_task_id = await add_progress_task("Awaiting confirmation", "Please confirm the action")

            # Stream tool execution
            if key == "action":
                tool_count += 1
                tool_messages = value.get("messages", [])
                
                # Get tool name from the message
                tool_name = "Tool"
                tool_result = ""
                if tool_messages:
                    last_msg = tool_messages[-1]
                    if hasattr(last_msg, 'name'):
                        tool_name = last_msg.name
                    if hasattr(last_msg, 'content'):
                        tool_result = str(last_msg.content)[:100]
                
                await update_progress_task(current_task_id, "completed", f"Completed: {tool_name}")
                
                # Create new task for next action
                if "execute_terminal" in str(tool_name):
                    current_task_id = await add_progress_task("Running command", "Executing terminal command...")
                elif "manage_file" in str(tool_name):
                    current_task_id = await add_progress_task("File operation", "Managing files...")
                elif "find_file" in str(tool_name):
                    current_task_id = await add_progress_task("Searching files", "Looking for files...")
                else:
                    current_task_id = await add_progress_task("Processing", "Continuing...")
                
                await broadcast_log("⚙️ Tool executed")
                # Process any queued file changes (both pending and applied)
                await process_file_change_queue()
                await process_applied_change_queue()

    # Mark final task as complete
    await update_progress_task(current_task_id, "completed", "Done")
    
    # End progress session
    await end_progress_session()

    # Add agent response to history
    if final_response:
        session["messages"].append(AIMessage(content=final_response))
        session["updated_at"] = datetime.now().isoformat()
    
    # Create markdown summary of this request
    summary_path = create_request_summary_markdown(
        session_id=session_id,
        request_text=request.message,
        response_text=final_response,
        workspace_path=request.workspace_path
    )
    
    if summary_path:
        await broadcast_log(f"📄 Summary saved: {os.path.basename(summary_path)}")
    
    return {
        "response": final_response,
        "session_id": session_id,
        "session_title": session["title"],
        "summary_file": summary_path
    }


# @app.websocket("/ws/logs")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     try:
#         while True:
#             # This is where we will 'listen' for new logs from your agent
#             # For now, we'll keep the connection open
#             data = await websocket.receive_text()
#             print(f"Received from VS Code: {data}")
#     except WebSocketDisconnect:
#         print("Client disconnected")

@app.post("/test-log")
async def test_log():
    await broadcast_log("🔥 Test log from FastAPI")
    return {"ok": True}

@app.post("/test-file-change")
async def test_file_change():
    """Test endpoint to simulate a file change notification"""
    from utils import store_applied_change, broadcast_applied_change, session_changes, applied_changes
    
    # Create a test change
    test_change_id = store_applied_change(
        file_path="/test/example.py",
        old_content="# old content",
        new_content="# new content\nprint('hello')",
        diff="--- old\n+++ new\n-# old content\n+# new content\n+print('hello')",
        is_new_file=False
    )
    
    # Broadcast it directly
    await broadcast_applied_change(test_change_id)
    
    return {
        "ok": True, 
        "change_id": test_change_id,
        "session_changes_count": len(session_changes),
        "applied_changes_count": len(applied_changes)
    }


@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    print(f"✅ WebSocket client connected. Total clients: {len(connected_clients)}")
    
    try:
        # Keep connection alive and allow client to send ping/pong
        while True:
            try:
                # Wait for any message from client (ping) or timeout
                await asyncio.wait_for(websocket.receive_text(), timeout=60)
            except asyncio.TimeoutError:
                # Send a ping to keep connection alive
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    break
    except WebSocketDisconnect:
        print("❌ WebSocket client disconnected")
    except Exception as e:
        print(f"⚠️ WebSocket error: {e}")
    finally:
        connected_clients.discard(websocket)
        print(f"📊 Remaining clients: {len(connected_clients)}")

@app.post("/emit-test-log")
async def emit_test_log():
    for ws in connected_clients:
        await ws.send_json({
            "type": "log",
            "content": "🔥 Test log from FastAPI"
        })
    return {"ok": True}

@app.post("/clear-history")
async def clear_history(session_id: str = None):
    """Clear chat history for a session or all sessions"""
    if session_id:
        if session_id in chat_sessions:
            chat_sessions[session_id]["messages"] = []
            chat_sessions[session_id]["updated_at"] = datetime.now().isoformat()
            return {"ok": True, "message": f"History cleared for session {session_id}"}
        return {"ok": False, "message": "Session not found"}
    else:
        chat_sessions.clear()
        return {"ok": True, "message": "All chat history cleared"}

@app.get("/sessions")
async def get_sessions():
    """Get list of all chat sessions"""
    sessions_list = [
        {
            "id": sid,
            "title": session["title"],
            "created_at": session["created_at"],
            "updated_at": session["updated_at"],
            "message_count": len(session["messages"])
        }
        for sid, session in chat_sessions.items()
    ]
    # Sort by updated_at (most recent first)
    sessions_list.sort(key=lambda x: x["updated_at"], reverse=True)
    return {"ok": True, "sessions": sessions_list}

@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get full session history"""
    if session_id not in chat_sessions:
        return {"ok": False, "error": "Session not found"}
    
    session = chat_sessions[session_id]
    messages = []
    for msg in session["messages"]:
        messages.append({
            "role": "user" if isinstance(msg, HumanMessage) else "agent",
            "content": msg.content
        })
    
    return {
        "ok": True,
        "session": {
            "id": session_id,
            "title": session["title"],
            "created_at": session["created_at"],
            "updated_at": session["updated_at"],
            "messages": messages
        }
    }

@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a chat session"""
    if session_id in chat_sessions:
        del chat_sessions[session_id]
        return {"ok": True, "message": f"Session {session_id} deleted"}
    return {"ok": False, "error": "Session not found"}

@app.get("/get-pending-change/{change_id}")
async def get_pending_change(change_id: str):
    """Get details of a pending file change"""
    print(f"🔍 Looking for pending change: {change_id}")
    print(f"📊 Available changes: {list(pending_changes.keys())}")
    
    if change_id not in pending_changes:
        print(f"❌ Change {change_id} not found in pending_changes")
        return {"ok": False, "error": f"Change not found. Available: {list(pending_changes.keys())}"}
    
    print(f"✅ Found change {change_id}")
    return {
        "ok": True,
        "change": pending_changes[change_id]
    }

class FileChangeApproval(BaseModel):
    change_id: str
    approved: bool

@app.post("/approve-file-change")
async def approve_file_change(approval: FileChangeApproval):
    """Approve or reject a file change"""
    change_id = approval.change_id
    
    if change_id not in pending_changes:
        return {"ok": False, "message": "Change not found"}
    
    change = pending_changes[change_id]
    
    if approval.approved:
        try:
            # Apply the change
            file_path = change["file_path"]
            new_content = change["new_content"]
            
            # Create directory if needed
            dir_path = os.path.dirname(file_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
            
            # Write the file
            with open(file_path, "w") as f:
                f.write(new_content)
            
            # Remove from pending
            del pending_changes[change_id]
            
            await broadcast_log(f"✅ File change accepted: {file_path}")
            
            return {
                "ok": True, 
                "message": f"Changes applied to {file_path}",
                "file_path": file_path
            }
        except Exception as e:
            return {"ok": False, "message": f"Error applying changes: {str(e)}"}
    else:
        # Rejected
        file_path = change["file_path"]
        del pending_changes[change_id]
        
        await broadcast_log(f"❌ File change rejected: {file_path}")
        
        return {
            "ok": True,
            "message": f"Changes rejected for {file_path}",
            "file_path": file_path
        }

@app.get("/pending-changes")
async def get_pending_changes():
    """Get all pending file changes"""
    return {
        "ok": True,
        "changes": [
            {
                "change_id": change_id,
                "file_path": change["file_path"],
                "is_new_file": change["is_new_file"]
            }
            for change_id, change in pending_changes.items()
        ]
    }

# =============================================
# Applied File Changes Endpoints (New Workflow)
# =============================================

@app.get("/session-changes")
async def get_session_changes():
    """Get all file changes in current session (for sidebar)"""
    changes = get_all_session_changes()
    return {
        "ok": True,
        "changes": changes
    }

@app.get("/applied-change/{change_id}")
async def get_applied_change_details(change_id: str):
    """Get details of an applied file change"""
    change = get_applied_change(change_id)
    if not change:
        return {"ok": False, "message": "Change not found"}
    
    return {
        "ok": True,
        "change": change
    }

class RevertChangeRequest(BaseModel):
    change_id: str

@app.post("/revert-change")
async def revert_file_change(request: RevertChangeRequest):
    """Revert an applied file change back to original content"""
    change_id = request.change_id
    change = get_applied_change(change_id)
    
    if not change:
        return {"ok": False, "message": "Change not found"}
    
    if change["status"] == "reverted":
        return {"ok": False, "message": "Change already reverted"}
    
    try:
        file_path = change["file_path"]
        
        if change["is_new_file"]:
            # Delete the new file
            if os.path.exists(file_path):
                os.remove(file_path)
            await broadcast_log(f"🗑️ File deleted (reverted): {file_path}")
        else:
            # Restore original content
            with open(file_path, "w") as f:
                f.write(change["old_content"])
            await broadcast_log(f"↩️ File reverted: {file_path}")
        
        # Update status
        update_change_status(change_id, "reverted")
        
        # Broadcast update to all clients
        await broadcast_session_changes_update()
        
        return {
            "ok": True,
            "message": f"Reverted: {file_path}",
            "file_path": file_path
        }
    except Exception as e:
        return {"ok": False, "message": f"Error reverting: {str(e)}"}

@app.post("/accept-change")
async def accept_file_change(request: RevertChangeRequest):
    """Accept an applied change (just marks it as accepted, file already changed)"""
    change_id = request.change_id
    change = get_applied_change(change_id)
    
    if not change:
        return {"ok": False, "message": "Change not found"}
    
    # Mark as accepted
    update_change_status(change_id, "accepted")
    
    await broadcast_log(f"✅ Change accepted: {change['file_path']}")
    
    # Broadcast update
    await broadcast_session_changes_update()
    
    return {
        "ok": True,
        "message": f"Accepted: {change['file_path']}",
        "file_path": change["file_path"]
    }

@app.post("/revert-all-changes")
async def revert_all_changes():
    """Revert all applied changes in current session"""
    changes = get_all_session_changes()
    reverted = []
    errors = []
    
    for change_info in changes:
        if change_info["status"] == "applied":
            change = get_applied_change(change_info["change_id"])
            if change:
                try:
                    file_path = change["file_path"]
                    if change["is_new_file"]:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    else:
                        with open(file_path, "w") as f:
                            f.write(change["old_content"])
                    
                    update_change_status(change_info["change_id"], "reverted")
                    reverted.append(file_path)
                except Exception as e:
                    errors.append(f"{file_path}: {str(e)}")
    
    await broadcast_log(f"↩️ Reverted {len(reverted)} files")
    await broadcast_session_changes_update()
    
    return {
        "ok": True,
        "reverted": reverted,
        "errors": errors,
        "message": f"Reverted {len(reverted)} files"
    }

@app.post("/accept-all-changes")
async def accept_all_changes():
    """Accept all applied changes in current session"""
    changes = get_all_session_changes()
    accepted = []
    
    for change_info in changes:
        if change_info["status"] == "applied":
            update_change_status(change_info["change_id"], "accepted")
            accepted.append(change_info["file_path"])
    
    await broadcast_log(f"✅ Accepted {len(accepted)} changes")
    await broadcast_session_changes_update()
    
    return {
        "ok": True,
        "accepted": accepted,
        "message": f"Accepted {len(accepted)} changes"
    }

@app.post("/clear-session-changes")
async def clear_all_session_changes():
    """Clear the session changes list"""
    clear_session_changes()
    await broadcast_session_changes_update()
    return {"ok": True, "message": "Session changes cleared"}

async def broadcast_session_changes_update():
    """Broadcast updated session changes to all clients"""
    changes = get_all_session_changes()
    
    for ws in connected_clients:
        try:
            await ws.send_json({
                "type": "session_changes_update",
                "changes": changes
            })
        except Exception:
            pass

@app.get("/get-file-content")
async def get_file_content(path: str):
    """Get current content of a file"""
    try:
        if os.path.exists(path):
            with open(path, 'r') as f:
                content = f.read()
            return {"ok": True, "content": content}
        else:
            return {"ok": True, "content": ""}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# =============================================
# Process Control Endpoints (Input & Kill)
# =============================================

class ProcessInputRequest(BaseModel):
    input_text: str

@app.post("/send-input/{process_id}")
async def send_input_to_process(process_id: str, request: ProcessInputRequest):
    """Send input to a running process (for interactive commands)"""
    try:
        if process_id not in running_processes:
            return {"ok": False, "message": f"Process {process_id} not found or already finished"}
        
        process_info = running_processes[process_id]
        process = process_info["process"]
        
        if process.stdin is None:
            return {"ok": False, "message": "Process does not support stdin input"}
        
        if process.returncode is not None:
            return {"ok": False, "message": "Process has already finished"}
        
        # Send input with newline
        input_text = request.input_text
        if not input_text.endswith('\n'):
            input_text += '\n'
        
        process.stdin.write(input_text.encode())
        await process.stdin.drain()
        
        await broadcast_log(f"📥 Input sent: {request.input_text}")
        return {"ok": True, "message": "Input sent successfully"}
    except Exception as e:
        await broadcast_log(f"❌ Error sending input: {e}")
        return {"ok": False, "message": str(e)}

@app.post("/kill-process/{process_id}")
async def kill_process(process_id: str):
    """Kill a running process (Ctrl+C equivalent)"""
    try:
        if process_id not in running_processes:
            return {"ok": False, "message": f"Process {process_id} not found or already finished"}
        
        process_info = running_processes[process_id]
        process = process_info["process"]
        command = process_info["command"]
        
        if process.returncode is not None:
            # Already finished
            if process_id in running_processes:
                del running_processes[process_id]
            return {"ok": True, "message": "Process already finished"}
        
        # Send SIGINT (Ctrl+C) first for graceful termination
        try:
            process.send_signal(signal.SIGINT)
            await broadcast_log(f"🛑 Sent Ctrl+C to process {process_id}")
            
            # Wait briefly for graceful shutdown
            await asyncio.sleep(0.5)
            
            # If still running, force kill
            if process.returncode is None:
                process.kill()
                await broadcast_log(f"⚠️ Force killed process {process_id}")
        except ProcessLookupError:
            pass  # Process already terminated
        
        # Clean up
        if process_id in running_processes:
            del running_processes[process_id]
        
        await broadcast_log(f"✅ Process terminated: {command[:50]}...")
        return {"ok": True, "message": "Process terminated"}
    except Exception as e:
        await broadcast_log(f"❌ Error killing process: {e}")
        return {"ok": False, "message": str(e)}

@app.get("/running-processes")
async def get_running_processes():
    """Get list of currently running processes"""
    return {
        "ok": True,
        "processes": [
            {"process_id": pid, "command": info["command"]}
            for pid, info in running_processes.items()
            if info["process"].returncode is None
        ]
    }

# =============================================
# File Browser Endpoints (for @ mentions)
# =============================================

class FileListRequest(BaseModel):
    path: str = None  # Optional path to list from
    search: str = None  # Optional search filter
    workspace_path: str = None  # Workspace path from VS Code

@app.post("/list-workspace-files")
async def list_workspace_files(request: FileListRequest = None):
    """List files in the workspace for @ mention picker"""
    from utils import get_workspace_path, set_workspace_path
    import fnmatch
    
    # Use workspace from request if provided, otherwise try stored one
    workspace = None
    if request and request.workspace_path:
        workspace = request.workspace_path
        set_workspace_path(workspace)  # Also store it for future use
    else:
        workspace = get_workspace_path()
    
    if not workspace:
        return {"ok": False, "message": "No workspace path set"}
    
    search_filter = request.search.lower() if request and request.search else None
    
    files = []
    ignore_patterns = [
        '*.pyc', '__pycache__', '.git', 'node_modules', '.vscode',
        'venv', '.env', '*.egg-info', '.DS_Store', '*.log',
        'dist', 'build', '.next', '.cache', 'coverage'
    ]
    
    try:
        for root, dirs, filenames in os.walk(workspace):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if not any(
                fnmatch.fnmatch(d, pattern) for pattern in ignore_patterns
            )]
            
            for filename in filenames:
                # Skip ignored files
                if any(fnmatch.fnmatch(filename, pattern) for pattern in ignore_patterns):
                    continue
                
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, workspace)
                
                # Apply search filter
                if search_filter and search_filter not in rel_path.lower():
                    continue
                
                # Get file info
                try:
                    stat = os.stat(full_path)
                    files.append({
                        "path": rel_path,
                        "full_path": full_path,
                        "name": filename,
                        "size": stat.st_size,
                        "is_directory": False
                    })
                except OSError:
                    continue
            
            # Limit to prevent overwhelming UI
            if len(files) > 100:
                break
        
        # Sort by path
        files.sort(key=lambda x: x["path"])
        
        return {"ok": True, "files": files[:100], "workspace": workspace}
    except Exception as e:
        return {"ok": False, "message": str(e)}


class FolderListRequest(BaseModel):
    workspace_path: str = None
    search: str = None  # Optional filter

@app.post("/list-workspace-folders")
async def list_workspace_folders(request: FolderListRequest = None):
    """List folders in the workspace for / prompt folder picker (same workspace as @ files)"""
    from utils import get_workspace_path, set_workspace_path
    import fnmatch

    workspace = None
    if request and request.workspace_path:
        workspace = request.workspace_path
        set_workspace_path(workspace)
    else:
        workspace = get_workspace_path()

    if not workspace:
        return {"ok": False, "message": "No workspace path set"}

    search_filter = request.search.lower() if request and request.search else None
    ignore_patterns = [
        '__pycache__', '.git', 'node_modules', '.vscode',
        'venv', '.env', '*.egg-info', '.DS_Store',
        'dist', 'build', '.next', '.cache', 'coverage'
    ]
    folders = []
    try:
        # Include workspace root
        root_name = os.path.basename(workspace.rstrip(os.sep)) or workspace
        folders.append({
            "path": ".",
            "name": root_name,
            "full_path": workspace,
        })
        for root, dirs, _ in os.walk(workspace):
            dirs[:] = [d for d in dirs if not any(
                fnmatch.fnmatch(d, pattern) for pattern in ignore_patterns
            )]
            for d in dirs:
                full_path = os.path.join(root, d)
                rel_path = os.path.relpath(full_path, workspace)
                if search_filter and search_filter not in rel_path.lower():
                    continue
                folders.append({
                    "path": rel_path,
                    "name": d,
                    "full_path": full_path,
                })
            if len(folders) > 80:
                break
        folders.sort(key=lambda x: x["path"])
        return {"ok": True, "folders": folders[:80], "workspace": workspace}
    except Exception as e:
        return {"ok": False, "message": str(e)}


class ReadFileRequest(BaseModel):
    path: str = None
    workspace_path: str = None

@app.post("/read-file-content")
async def read_file_content(path: str = None, request: ReadFileRequest = None):
    """Read file content for context"""
    from utils import get_workspace_path, set_workspace_path
    
    # Get path from query param or request body
    file_path = path or (request.path if request else None)
    
    if not file_path:
        return {"ok": False, "message": "No file path provided"}
    
    # Use workspace from request if provided
    workspace = None
    if request and request.workspace_path:
        workspace = request.workspace_path
        set_workspace_path(workspace)
    else:
        workspace = get_workspace_path()
    
    if not workspace:
        return {"ok": False, "message": "No workspace path set"}
    
    # Resolve full path
    if not os.path.isabs(file_path):
        full_path = os.path.join(workspace, file_path)
    else:
        full_path = file_path
    
    try:
        if not os.path.exists(full_path):
            return {"ok": False, "message": f"File not found: {file_path}"}
        
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "ok": True,
            "path": file_path,
            "content": content,
            "size": len(content)
        }
    except UnicodeDecodeError:
        return {"ok": False, "message": "Cannot read binary file"}
    except Exception as e:
        return {"ok": False, "message": str(e)}

# Updated execute_terminal tool to "broadcast" logs
async def execute_terminal_stream(command: str, websocket: WebSocket):
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    # Read stdout line by line and send to VS Code via WebSocket
    while True:
        line = await process.stdout.readline()
        if not line:
            break
        log_message = line.decode().strip()
        await broadcast_log(log_message)
    
    await process.wait()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)