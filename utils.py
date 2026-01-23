# Shared utilities for the agent system
import uuid
from typing import Dict
import asyncio

# Global set to track connected WebSocket clients
connected_clients = set()

# Store pending file changes awaiting approval (legacy - keeping for compatibility)
pending_changes: Dict[str, dict] = {}

# Store APPLIED file changes (for the new workflow - changes applied, can be reverted)
applied_changes: Dict[str, dict] = {}

# Queue for file change notifications (to be sent when event loop is available)
file_change_queue = []

# Session changes list (all changes in current session for the sidebar)
session_changes: list = []

# Current workspace path from VS Code (set by server.py, used by brain.py)
current_workspace_path: str = None

# Track running processes for interactive input and kill support
running_processes: Dict[str, dict] = {}

# Track current task progress
current_tasks: Dict[str, dict] = {}
task_counter = 0

def set_workspace_path(path: str):
    """Set the current workspace path"""
    global current_workspace_path
    current_workspace_path = path
    print(f"📂 Workspace path set to: {path}")

def get_workspace_path() -> str:
    """Get the current workspace path"""
    return current_workspace_path

async def broadcast_log(message: str):
    """Broadcast a log message to all connected WebSocket clients."""
    if not connected_clients:
        print(f"⚠️ No WebSocket clients connected. Log: {message}")
        return
    
    disconnected = set()
    for ws in connected_clients:
        try:
            await ws.send_json({
                "type": "log",
                "content": message
            })
        except Exception as e:
            print(f"❌ Failed to send to client: {e}")
            disconnected.add(ws)
    
    # Remove disconnected clients
    for ws in disconnected:
        connected_clients.discard(ws)

def store_pending_change(file_path: str, old_content: str, new_content: str, diff: str) -> str:
    """Store a pending file change and return its ID."""
    change_id = str(uuid.uuid4())[:8]
    pending_changes[change_id] = {
        "file_path": file_path,
        "old_content": old_content,
        "new_content": new_content,
        "diff": diff,
        "is_new_file": old_content == ""
    }
    return change_id

def notify_file_change(change_id: str, file_path: str, is_new: bool = False):
    """Queue a file change notification (non-async version)"""
    file_change_queue.append({
        "change_id": change_id,
        "file_path": file_path,
        "is_new": is_new
    })
    print(f"📝 File change queued: {file_path} (ID: {change_id})")

async def broadcast_file_change(change_id: str):
    """Broadcast a file change proposal to all connected clients."""
    print(f"🔍 Broadcasting file change: {change_id}")
    print(f"📊 Connected clients: {len(connected_clients)}")
    
    if change_id not in pending_changes:
        print(f"⚠️ Change ID {change_id} not found in pending_changes")
        return
    
    change = pending_changes[change_id]
    print(f"📝 Sending file change: {change['file_path']}")
    
    if not connected_clients:
        print("⚠️ No WebSocket clients connected! File change cannot be displayed.")
        print("💡 Make sure the VS Code extension sidebar is open and WebSocket is connected.")
        return
    
    disconnected = set()
    for ws in connected_clients:
        try:
            message = {
                "type": "file_change",
                "change_id": change_id,
                "file_path": change["file_path"],
                "diff": change["diff"],
                "is_new_file": change["is_new_file"],
                "preview": change["new_content"][:500] if change["is_new_file"] else None,
                "new_content": change["new_content"]  # Full content for diff editor
            }
            await ws.send_json(message)
            print(f"✅ File change sent to WebSocket client")
        except Exception as e:
            print(f"❌ Failed to send file change to client: {e}")
            disconnected.add(ws)
    
    for ws in disconnected:
        connected_clients.discard(ws)

async def process_file_change_queue():
    """Process queued file change notifications"""
    global file_change_queue
    print(f"🔄 Processing file change queue... ({len(file_change_queue)} items)")
    while file_change_queue:
        notification = file_change_queue.pop(0)
        print(f"📤 Processing queued change: {notification['change_id']}")
        await broadcast_file_change(notification["change_id"])

# =============================================
# Progress/Task Tracking System
# =============================================

async def broadcast_progress(action: str, task_id: str = None, task_name: str = None, status: str = None, details: str = None):
    """
    Broadcast progress updates to all connected clients.
    
    Actions:
    - 'start_session': Start a new progress session (clears old tasks)
    - 'add_task': Add a new task to the list
    - 'update_task': Update task status (pending, in_progress, completed, error)
    - 'end_session': End the progress session
    
    Status values: pending, in_progress, completed, error
    """
    global task_counter, current_tasks
    
    if action == 'start_session':
        current_tasks = {}
        task_counter = 0
    
    if action == 'add_task' and task_name:
        task_counter += 1
        task_id = f"task_{task_counter}"
        current_tasks[task_id] = {
            "id": task_id,
            "name": task_name,
            "status": "pending",
            "details": details or ""
        }
    
    if action == 'update_task' and task_id and task_id in current_tasks:
        if status:
            current_tasks[task_id]["status"] = status
        if details:
            current_tasks[task_id]["details"] = details
    
    # Broadcast to all clients
    message = {
        "type": "progress",
        "action": action,
        "task_id": task_id,
        "task_name": task_name,
        "status": status,
        "details": details,
        "tasks": list(current_tasks.values())
    }
    
    disconnected = set()
    for ws in connected_clients:
        try:
            await ws.send_json(message)
        except Exception as e:
            print(f"❌ Failed to send progress to client: {e}")
            disconnected.add(ws)
    
    for ws in disconnected:
        connected_clients.discard(ws)


async def add_progress_task(name: str, details: str = "") -> str:
    """Add a task and return its ID"""
    global task_counter, current_tasks
    task_counter += 1
    task_id = f"task_{task_counter}"
    current_tasks[task_id] = {
        "id": task_id,
        "name": name,
        "status": "in_progress",
        "details": details
    }
    await broadcast_progress("add_task", task_id, name, "in_progress", details)
    return task_id


async def update_progress_task(task_id: str, status: str, details: str = None):
    """Update a task's status"""
    if task_id in current_tasks:
        current_tasks[task_id]["status"] = status
        if details:
            current_tasks[task_id]["details"] = details
        await broadcast_progress("update_task", task_id, None, status, details)


async def start_progress_session():
    """Start a new progress tracking session"""
    global current_tasks, task_counter
    current_tasks = {}
    task_counter = 0
    await broadcast_progress("start_session")


async def end_progress_session():
    """End the current progress session"""
    await broadcast_progress("end_session")


# =============================================
# Applied File Changes Tracking (New Workflow)
# =============================================

def store_applied_change(file_path: str, old_content: str, new_content: str, diff: str, is_new_file: bool = False) -> str:
    """Store an applied file change (already written to disk) and return its ID."""
    import os
    change_id = str(uuid.uuid4())[:8]
    
    print(f"💾 STORING APPLIED CHANGE: {file_path}")
    print(f"   Change ID: {change_id}")
    print(f"   Is new file: {is_new_file}")
    
    applied_changes[change_id] = {
        "file_path": file_path,
        "old_content": old_content,
        "new_content": new_content,
        "diff": diff,
        "is_new_file": is_new_file,
        "status": "applied",
        "timestamp": __import__('datetime').datetime.now().isoformat()
    }
    
    # Also add to session changes for sidebar display
    session_changes.append({
        "change_id": change_id,
        "file_path": file_path,
        "file_name": os.path.basename(file_path),
        "is_new_file": is_new_file,
        "status": "applied"
    })
    
    print(f"📝 Applied change stored: {file_path} (ID: {change_id})")
    print(f"📊 Total applied_changes: {len(applied_changes)}")
    print(f"📊 Total session_changes: {len(session_changes)}")
    return change_id


def notify_applied_change(change_id: str, file_path: str, is_new: bool = False):
    """Queue an applied file change notification"""
    print(f"📢 NOTIFY APPLIED CHANGE: {file_path} (ID: {change_id})")
    file_change_queue.append({
        "change_id": change_id,
        "file_path": file_path,
        "is_new": is_new,
        "type": "applied"
    })
    print(f"📋 Queue now has {len(file_change_queue)} items")


async def broadcast_applied_change(change_id: str):
    """Broadcast an applied file change to all connected clients."""
    print(f"🔍 Broadcasting applied change: {change_id}")
    print(f"📊 Applied changes dict: {list(applied_changes.keys())}")
    print(f"📊 Session changes list: {len(session_changes)} items")
    
    if change_id not in applied_changes:
        print(f"⚠️ Change ID {change_id} not found in applied_changes")
        return
    
    change = applied_changes[change_id]
    
    if not connected_clients:
        print("⚠️ No WebSocket clients connected!")
        return
    
    print(f"📡 Broadcasting to {len(connected_clients)} clients")
    
    # Build session changes list with all required fields
    changes_for_sidebar = []
    for sc in session_changes:
        changes_for_sidebar.append({
            "change_id": sc.get("change_id", ""),
            "file_path": sc.get("file_path", ""),
            "file_name": sc.get("file_name", ""),
            "is_new_file": sc.get("is_new_file", False),
            "status": sc.get("status", "applied")
        })
    
    print(f"📋 Sending {len(changes_for_sidebar)} changes to sidebar")
    
    disconnected = set()
    for ws in connected_clients:
        try:
            message = {
                "type": "file_applied",
                "change_id": change_id,
                "file_path": change["file_path"],
                "diff": change["diff"],
                "is_new_file": change["is_new_file"],
                "old_content": change["old_content"],
                "new_content": change["new_content"],
                "status": change["status"],
                "all_changes": changes_for_sidebar
            }
            print(f"📤 Sending message: type={message['type']}, file={message['file_path']}, changes={len(message['all_changes'])}")
            await ws.send_json(message)
            print(f"✅ Applied change sent to WebSocket client")
        except Exception as e:
            print(f"❌ Failed to send applied change to client: {e}")
            import traceback
            traceback.print_exc()
            disconnected.add(ws)
    
    for ws in disconnected:
        connected_clients.discard(ws)


async def process_applied_change_queue():
    """Process queued applied file change notifications"""
    global file_change_queue
    print(f"🔄 Processing applied change queue... (total queue: {len(file_change_queue)} items)")
    
    items_to_process = [item for item in file_change_queue if item.get("type") == "applied"]
    print(f"📊 Found {len(items_to_process)} applied changes to process")
    
    for item in items_to_process:
        print(f"📤 Broadcasting applied change: {item['change_id']}")
        file_change_queue.remove(item)
        await broadcast_applied_change(item["change_id"])


def clear_session_changes():
    """Clear all session changes (called when starting new session)"""
    global session_changes, applied_changes
    session_changes = []
    applied_changes = {}
    print("🗑️ Session changes cleared")


def update_change_status(change_id: str, status: str):
    """Update the status of an applied change (accepted/reverted)"""
    if change_id in applied_changes:
        applied_changes[change_id]["status"] = status
        # Update in session_changes list too
        for change in session_changes:
            if change["change_id"] == change_id:
                change["status"] = status
                break
        print(f"📝 Change {change_id} status updated to: {status}")


def get_all_session_changes():
    """Get all changes in current session"""
    return session_changes.copy()


def get_applied_change(change_id: str):
    """Get details of an applied change"""
    return applied_changes.get(change_id)
