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
from utils import broadcast_log, connected_clients, pending_changes, broadcast_file_change, process_file_change_queue
import os
from datetime import datetime

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
    # Get or create session
    session_id, session = get_or_create_session(request.session_id)
    
    # Add user message to history
    session["messages"].append(HumanMessage(content=request.message))
    session["updated_at"] = datetime.now().isoformat()
    
    # Update title based on first message
    if len(session["messages"]) == 1:
        # Use first 50 chars of message as title
        session["title"] = request.message[:50] + ("..." if len(request.message) > 50 else "")
    
    # Create inputs with full conversation history and recursion limit
    inputs = {"messages": session["messages"].copy()}
    config = {"recursion_limit": 50}  # Prevent recursion errors
    final_response = ""

    async for output in agent_app.astream(inputs, config=config):
        for key, value in output.items():

            # Stream agent messages
            if key == "agent":
                msg = value["messages"][-1].content
                await broadcast_log(f"🤖 Agent: {msg}")
                final_response = msg

            # Stream tool execution
            if key == "action":
                await broadcast_log("⚙️ Tool executed")
                # Process any queued file changes
                await process_file_change_queue()

    # Add agent response to history
    if final_response:
        session["messages"].append(AIMessage(content=final_response))
        session["updated_at"] = datetime.now().isoformat()
    
    return {
        "response": final_response,
        "session_id": session_id,
        "session_title": session["title"]
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
        # await websocket.send_json({"type": "log", "content": log_message})
    
    await process.wait()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)