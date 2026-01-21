# 🚀 Quick Start Guide - MyAntigravity

Get your Cursor/Antigravity clone running in 3 minutes!

## ✅ What Was Fixed

1. **NameError: 'broadcast_log' is not defined** ✅ FIXED
   - Added proper imports in `brain.py` and `server.py`
   
2. **Terminal view not displayed** ✅ FIXED
   - Complete UI redesign with separate chat and terminal sections
   - Real-time status indicator
   - Auto-reconnecting WebSocket

## 🏃 Quick Start

### 1️⃣ Start the Backend Server (Required)

```bash
# Open Terminal 1
cd /Users/divakar/Desktop/my-antigravity
source venv/bin/activate
python3 server.py
```

**Expected Output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

✅ Leave this terminal running!

### 2️⃣ Test the Connection (Optional but Recommended)

```bash
# Open Terminal 2
cd /Users/divakar/Desktop/my-antigravity
source venv/bin/activate
python3 test_connection.py
```

**Expected Output:**
```
============================================================
🚀 MyAntigravity Connection Test
============================================================

ℹ️  Testing HTTP endpoints...
✅ Server is running and accessible
✅ Log emission endpoint working

ℹ️  Testing WebSocket connection...
✅ WebSocket connected successfully!

🎉 All tests passed! Your setup is working correctly.
```

### 3️⃣ Launch VS Code Extension

```bash
# Open Terminal 3 (or use VS Code)
cd /Users/divakar/Desktop/my-antigravity/extension-builder/myantigravity
code .
```

In VS Code:
1. Press **F5** (or Run → Start Debugging)
2. A new "Extension Development Host" window will open
3. In the new window, click the **MyAntigravity** icon in the Activity Bar (left sidebar)

### 4️⃣ Start Using the Agent!

In the MyAntigravity sidebar:

1. **Wait for Connection**: Look for "🟢 Connected" status in the Terminal Output section

2. **Type a Command**: Try these examples:
   ```
   Create a Python script that prints "Hello, World!"
   ```
   ```
   List all files in the current directory
   ```
   ```
   Create a simple Flask app with a /hello endpoint
   ```

3. **Watch the Magic**:
   - **Chat Section**: Shows your message and the agent's response
   - **Terminal Output**: Shows real-time command execution logs

## 📊 Visual Layout

```
┌────────────────────────────────────────────────┐
│  🚀 MyAntigravity Agent                        │
├────────────────────────────────────────────────┤
│  CHAT                                          │
│  ┌──────────────────────────────────────────┐ │
│  │ You: Create a Python script              │ │
│  │ Agent: I'll create that for you...       │ │
│  └──────────────────────────────────────────┘ │
│  [Type here.....................] [Send]      │
├────────────────────────────────────────────────┤
│  TERMINAL OUTPUT                               │
│  Status: 🟢 Connected                          │
│  ┌──────────────────────────────────────────┐ │
│  │ ✅ Agent terminal connected              │ │
│  │ ⚙️ Agent processing request...           │ │
│  │ > Executing: python script.py            │ │
│  │ > Hello, World!                          │ │
│  │ ✅ Command finished                      │ │
│  └──────────────────────────────────────────┘ │
└────────────────────────────────────────────────┘
```

## 🎯 Example Commands to Try

### Basic Commands
```
List all Python files in this directory
```

### File Operations
```
Create a file called test.py with a function that adds two numbers
```

```
Read the contents of brain.py
```

### Script Execution
```
Create and run a Python script that prints prime numbers up to 50
```

### Complex Tasks
```
Create a new directory called 'myproject', add a Python file with a Flask app, and list the directory contents
```

## 🔍 How to Verify It's Working

### ✅ Server is Working
You should see in Terminal 1:
```
✅ WebSocket client connected. Total clients: 1
```

### ✅ Extension is Connected
In the MyAntigravity sidebar:
- Status shows: **🟢 Connected**
- Terminal shows: **✅ Agent terminal connected**

### ✅ Agent is Responding
When you send a message:
- Chat section shows your message and agent's response
- Terminal section shows real-time logs:
  ```
  ⚙️ Agent processing request...
  🤖 Agent: [agent's thought process]
  ⚙️ Tool executed
  ✅ Agent response received
  ```

## ⚠️ Common Issues & Solutions

### Issue: "WebSocket error – check DevTools"
**Solution:** Make sure the server is running in Terminal 1

### Issue: Agent doesn't respond
**Solution:** Check Azure OpenAI credentials in `brain.py`
```python
AZURE_ENDPOINT = "your-endpoint-here"
AZURE_API_KEY = "your-key-here"
AZURE_DEPLOYMENT = "your-deployment-name"
```

### Issue: "Port 8000 already in use"
**Solution:** Kill the existing process
```bash
lsof -i :8000  # Find the process ID
kill -9 <PID>   # Kill it
python3 server.py  # Try again
```

### Issue: Extension doesn't load
**Solution:** Recompile the extension
```bash
cd extension-builder/myantigravity
npm run compile
# Press F5 again
```

## 📁 Project Structure

```
my-antigravity/
├── brain.py              ✅ Fixed: imports broadcast_log
├── server.py             ✅ Fixed: imports from utils
├── utils.py              ✅ Shared broadcast_log function
├── start_server.sh       ✨ New: Easy server startup
├── test_connection.py    ✨ New: Connection tester
├── README.md             ✨ New: Full documentation
├── QUICKSTART.md         ✨ This file!
└── extension-builder/
    └── myantigravity/
        ├── src/
        │   └── extension.ts  ✅ Fixed: New dual-panel UI
        └── out/
            └── extension.js  ✅ Recompiled
```

## 🎓 What Each Component Does

### `brain.py`
- Contains the LangGraph agent
- Defines tools: `execute_terminal`, `manage_file`, `find_file`
- Uses Azure OpenAI for AI capabilities

### `server.py`
- FastAPI web server
- Handles HTTP POST `/chat` endpoint
- Manages WebSocket connections at `/ws/logs`
- Broadcasts logs to connected clients

### `utils.py`
- Shared utility functions
- `broadcast_log()`: Sends logs to all connected clients
- `connected_clients`: Tracks WebSocket connections

### `extension.ts`
- VS Code extension code
- Creates the sidebar UI
- Manages WebSocket connection
- Displays chat and terminal output

## 💡 Tips

1. **Keep the server running** - It needs to stay active in Terminal 1
2. **Watch the Terminal Output** - It shows what the agent is doing in real-time
3. **Be specific** - The more specific your request, the better the agent can help
4. **Check logs** - If something fails, the terminal section will show errors

## 🆘 Need Help?

1. **Check server logs** in Terminal 1
2. **Run test script**: `python3 test_connection.py`
3. **Check VS Code DevTools**: Help → Toggle Developer Tools
4. **Read full docs**: See `README.md`

## 🎉 Success!

If you can see:
- ✅ Server running in Terminal 1
- ✅ "🟢 Connected" in the extension
- ✅ Agent responds to your messages
- ✅ Terminal shows real-time logs

**Congratulations! Your Cursor/Antigravity clone is working!** 🚀

---

**Next Steps:**
- Explore different commands
- Read the full README.md
- Check out FIXES_APPLIED.md to see what was fixed
- Start building amazing things!

---

Made with ❤️ | Last Updated: 2026-01-21

