from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
import json
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from brain import app as agent_app  # Import your LangGraph app
from langchain_core.messages import HumanMessage

app = FastAPI()

# Allow VS Code (which runs on a different port) to talk to this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

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
    inputs = {"messages": [HumanMessage(content=request.message)]}
    final_response = ""

    async for output in agent_app.astream(inputs):
        for key, value in output.items():

            # Stream agent messages
            if key == "agent":
                msg = value["messages"][-1].content
                await broadcast_log(f"🤖 Agent: {msg}")
                final_response = msg

            # Stream tool execution
            if key == "action":
                await broadcast_log("⚙️ Tool executed")

    return {"response": final_response}


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


connected_websockets: set[WebSocket] = set()

connected_clients = set()

@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        while True:
            await asyncio.sleep(60)  # keep connection alive
    except WebSocketDisconnect:
        connected_clients.remove(websocket)

@app.post("/emit-test-log")
async def emit_test_log():
    for ws in connected_clients:
        await ws.send_json({
            "type": "log",
            "content": "🔥 Test log from FastAPI"
        })
    return {"ok": True}

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

async def broadcast_log(message: str):
    for ws in list(connected_clients):
        try:
            await ws.send_json({
                "type": "log",
                "content": message
            })
        except:
            connected_clients.remove(ws)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)