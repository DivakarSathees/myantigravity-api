# Shared utilities for the agent system
import uuid
from typing import Dict
import asyncio

# Global set to track connected WebSocket clients
connected_clients = set()

# Store pending file changes awaiting approval
pending_changes: Dict[str, dict] = {}

# Queue for file change notifications (to be sent when event loop is available)
file_change_queue = []

# Current workspace path from VS Code (set by server.py, used by brain.py)
current_workspace_path: str = None

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
