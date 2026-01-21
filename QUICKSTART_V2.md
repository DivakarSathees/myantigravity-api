# 🚀 Antigravity - Quick Start Guide (v2.0)

## What's New in v2.0?
- ✅ **Fixed async/event loop errors**
- ✅ **Chat history navigation**
- ✅ **Session management**
- ✅ **Multiple concurrent conversations**

---

## 🎯 Quick Start (3 Steps)

### 1. Install Dependencies
```bash
cd /Users/divakar/Desktop/my-antigravity
pip install -r requirement.txt
```

### 2. Start Backend Server
```bash
python3 server.py
```
Server runs on `http://localhost:8000`

### 3. Install VS Code Extension
```bash
cd extension-builder/myantigravity
npm install
npm run compile
```

Press `F5` in VS Code to launch extension development host.

---

## 🎮 Using the Tool

### Chat Interface

**Main Controls:**
- **Clear** - Clear current session messages
- **New Chat** - Start a fresh conversation
- **History** - View and manage all sessions

**Input Area:**
- Type message → Press Enter or click Send
- Agent responds with thinking and actions

### Terminal View

**Sections:**
- 📝 **Chat** - Conversation history
- 💻 **Terminal** - Command execution logs
- 🔀 **File Diffs** - Proposed code changes

**Color Coding:**
- 🟢 Green - Success messages
- 🔴 Red - Errors
- 🟡 Yellow - Warnings
- 🔵 Blue - Info/status

### Chat History

**View Sessions:**
1. Click **"History"** button
2. Modal shows all past chats
3. Each session displays:
   - Title (auto-generated)
   - Message count
   - Last updated time
   - Delete button

**Load Session:**
- Click any session card
- Full conversation history loads
- Continue where you left off

**Delete Session:**
- Click × on session card
- Confirm deletion
- Session permanently removed

**Start New Chat:**
- Click **"New Chat"** button
- Fresh session starts
- Previous sessions preserved

---

## 🤖 Agent Capabilities

### 1. File Management
**Read files:**
```
Show me the contents of app.py
```

**Edit files:**
```
Add error handling to the login function
```
- Agent proposes changes
- Diff displayed in editor
- Accept or reject via buttons

### 2. Terminal Commands
**Execute commands:**
```
Run the server
```
- Agent asks for confirmation
- Click "Yes, Execute" or "No, Cancel"
- Output streams in real-time

### 3. Intelligent Execution
**Smart file running:**
```
Run the setup script
```
- Agent reads file first
- Detects input requirements
- Asks for input values
- Pipes input automatically
- Handles errors and retries

### 4. Error Handling
**Auto-fix errors:**
```
The app is crashing, fix it
```
- Agent analyzes error
- Identifies root cause
- Proposes fix with diff
- After approval, asks to rerun

---

## 📋 Example Workflows

### Workflow 1: Build New App
```
User: "Build a Flask app with user authentication"

Agent:
1. 📋 Plans the structure
2. 📝 Creates files (app.py, models.py, etc.)
3. Shows diffs for approval
4. 💾 Saves after acceptance
5. 📦 Installs dependencies
6. ▶️ Asks to run server
```

### Workflow 2: Debug Existing Code
```
User: "The login function isn't working"

Agent:
1. 🔍 Reads relevant files
2. 🧐 Analyzes the code
3. 🐛 Identifies the bug
4. ✏️ Proposes fix with diff
5. ✅ Applies after approval
6. 🔄 Asks to rerun tests
```

### Workflow 3: Run Complex Script
```
User: "Run install.sh"

Agent:
1. 📖 Reads install.sh
2. 🤔 Detects it needs: username, email
3. ❓ Asks: "Please provide username and email"
4. User provides values
5. 🚀 Runs with: echo -e 'user\nemail' | ./install.sh
6. 📊 Shows output
```

---

## 🎨 UI Components Explained

### Session Title Bar
```
┌─────────────────────────────────────┐
│ Chat Sessions                       │
│         [Clear] [New Chat] [History]│
│ 💬 Build a Flask app...             │
└─────────────────────────────────────┘
```

### History Modal
```
┌─────────────────────────────────────┐
│ 📚 Chat History                  × │
├─────────────────────────────────────┤
│ ┌─────────────────────────────────┐ │
│ │ Build a Flask app...          × │ │
│ │ 12 messages • 2h ago            │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │ Fix login bug...              × │ │
│ │ 8 messages • 5h ago             │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### File Diff Display
```
┌─────────────────────────────────────┐
│ 📝 app.py                           │
│ ┌─────────────────────────────────┐ │
│ │ -   return "Hello"              │ │ (red)
│ │ +   return "Hello, World!"      │ │ (green)
│ └─────────────────────────────────┘ │
│ [Accept Changes] [Reject Changes]   │
└─────────────────────────────────────┘
```

### Terminal Execution
```
agent@antigravity:~$ python3 app.py
Starting server on port 5000...
✅ Server started successfully
```

---

## 🔧 Configuration

### Server Settings (server.py)
```python
# Port
uvicorn.run(app, host="0.0.0.0", port=8000)

# Recursion limit
config = {"recursion_limit": 50}
```

### Agent Behavior (brain.py)
```python
# System prompt defines:
- Thinking & planning approach
- Confirmation requirements
- Error handling strategy
- Input detection logic
```

---

## 🐛 Troubleshooting

### Issue: "Connection Failed"
**Solution:**
1. Ensure server is running: `python3 server.py`
2. Check console for errors
3. Verify port 8000 is available

### Issue: "Session Not Found"
**Solution:**
1. Click "New Chat"
2. Server restarts clear sessions (not persistent)
3. Session IDs don't survive server restart

### Issue: RuntimeWarning About Coroutines
**Status:** ✅ FIXED in v2.0
- Async queue system prevents warnings
- File operations work correctly now

### Issue: "No Running Event Loop"
**Status:** ✅ FIXED in v2.0
- File edits now work without errors
- Synchronous notification queue implemented

### Issue: Extension Not Loading
**Solution:**
1. Run `npm install` in extension directory
2. Run `npm run compile`
3. Press F5 to launch
4. Check for TypeScript errors

---

## 📊 Performance Tips

1. **Clear Old Sessions**
   - Delete unused sessions regularly
   - Reduces memory usage

2. **Use Specific Queries**
   - "Fix the login bug in auth.py"
   - Better than "fix everything"

3. **Monitor Terminal Output**
   - Watch for errors in real-time
   - Cancel long-running processes if needed

4. **Review Diffs Carefully**
   - Check all changes before accepting
   - Reject and ask for modifications if needed

---

## 🎓 Learning Resources

### Understanding the Agent
- Reads `SYSTEM_PROMPT` for behavior guidelines
- Uses LangGraph for workflow
- Tools: `execute_terminal`, `manage_file`, `find_file`

### Understanding Sessions
- Each chat = unique UUID
- Messages stored in memory
- Not persisted to disk (resets on server restart)

### Understanding File Diffs
- Generated using Python's `difflib`
- Unified diff format (industry standard)
- Shows only changed lines with context

---

## 🚀 Advanced Usage

### Chaining Commands
```
User: "Create a Flask app, add authentication, and run it"

Agent will:
1. Create files
2. Show each diff
3. Wait for approvals
4. Install dependencies
5. Ask to run
```

### Multi-File Edits
```
User: "Refactor the database models"

Agent will:
1. Read all relevant files
2. Plan changes
3. Show diff for each file
4. Apply after approval
```

### Error Recovery
```
Agent: "ModuleNotFoundError: flask"
Agent: "I'll install Flask..."
Agent: [Runs pip install flask]
Agent: "Should I retry running the app?"
```

---

## 📱 Keyboard Shortcuts

- `Enter` - Send message
- `Esc` - Close history modal
- Click outside modal - Close modal

---

## 🔗 API Reference

### Chat Endpoint
```
POST /chat
Body: { "message": "...", "session_id": "..." }
Response: { "response": "...", "session_id": "...", "session_title": "..." }
```

### Sessions Endpoint
```
GET /sessions
Response: { "ok": true, "sessions": [...] }
```

### Load Session
```
GET /session/{session_id}
Response: { "ok": true, "session": {...} }
```

### Delete Session
```
DELETE /session/{session_id}
Response: { "ok": true, "message": "..." }
```

### WebSocket Logs
```
ws://localhost:8000/ws
Messages: {"type": "log", "message": "..."}
          {"type": "file_change", "change_id": "...", ...}
```

---

## ✅ Quick Test

**1. Start fresh:**
```bash
python3 server.py
# In another terminal
cd extension-builder/myantigravity && code .
# Press F5
```

**2. Test basic chat:**
```
Type: "List files in the current directory"
Expected: Agent uses find_file tool, shows results
```

**3. Test file edit:**
```
Type: "Create a hello.py file"
Expected: Diff shown, accept button appears
```

**4. Test sessions:**
```
Click "History" → See sessions
Click "New Chat" → Fresh session
Load old session → History restored
```

---

## 🎉 You're Ready!

Start building with Antigravity v2.0! The agent is ready to:
- Write code
- Fix bugs
- Run commands
- Manage files
- Remember conversations

**Happy coding!** 🚀

