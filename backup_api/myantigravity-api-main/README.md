# 🚀 Antigravity - AI Coding Assistant (v2.0)

> A powerful VS Code extension powered by LangChain and LangGraph that helps you code, debug, and build projects through natural language.

## ✨ What's New in v2.0?

- ✅ **Fixed async/event loop errors** - Stable file operations
- ✅ **Chat history navigation** - View and manage all conversations
- ✅ **Session management** - Switch between multiple chats
- ✅ **Auto-generated titles** - Easy identification of conversations
- ✅ **Enhanced UI** - Beautiful modal with history

## 🎯 Features

### 💬 Intelligent Chat
- Natural language interaction with AI agent
- Context-aware responses
- Multi-turn conversations
- Session persistence

### 📝 Smart File Management
- Read and analyze files
- Propose edits with diffs
- Create new files
- Accept/reject changes in VS Code editor

### 💻 Terminal Integration
- Execute commands with confirmation
- Real-time output streaming
- Auto-detect input requirements
- Smart error handling and auto-fix

### 📚 Session History
- **View all past chats** with titles and metadata
- **Switch between sessions** seamlessly
- **Delete old conversations** for cleanup
- **Start fresh chats** without losing history

### 🤖 Agent Capabilities
- **Planning**: Thinks before acting
- **File Reading**: Understands code context
- **Input Detection**: Auto-provides script inputs
- **Error Recovery**: Analyzes and fixes issues
- **Dependency Management**: Installs missing packages

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 14+
- VS Code
- OpenAI API Key

### Installation

1. **Clone & Install Backend**
```bash
cd /Users/divakar/Desktop/my-antigravity
pip install -r requirement.txt
```

2. **Set OpenAI API Key**
```bash
export OPENAI_API_KEY="your-key-here"
```

3. **Start Server**
```bash
python3 server.py
```

4. **Build Extension**
```bash
cd extension-builder/myantigravity
npm install
npm run compile
```

5. **Launch Extension**
- Open the extension folder in VS Code
- Press `F5` to start debugging
- Extension opens in new VS Code window

## 📖 Usage

### Basic Chat
1. Open the Antigravity sidebar
2. Type your request (e.g., "Build a Flask API")
3. Agent thinks, plans, and proposes actions
4. Review diffs and confirm commands
5. Continue the conversation

### Session Management
- **New Chat**: Start fresh conversation
- **History**: View all past sessions
- **Clear**: Clear current chat messages
- **Load Session**: Click any session in history
- **Delete**: Remove unwanted sessions

### Example Requests

**Create a project:**
```
"Build a Flask app with user authentication"
```

**Debug code:**
```
"The login function in auth.py is broken, fix it"
```

**Run scripts:**
```
"Run the setup.py script"
```
(Agent auto-detects and provides required inputs)

**Fix errors:**
```
"The app crashed with ImportError"
```
(Agent analyzes, fixes, and asks to rerun)

## 🎨 UI Overview

### Main Interface
```
┌─────────────────────────────────────┐
│ 📚 Antigravity                      │
│                                     │
│ Chat Sessions                       │
│      [Clear] [New Chat] [History]   │
│ 💬 Build a Flask app...             │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ You: Build a Flask app          │ │
│ │                                 │ │
│ │ Agent: I'll create...           │ │
│ └─────────────────────────────────┘ │
│                                     │
│ [Type message...] [Send]            │
│                                     │
│ Terminal Output                     │
│ ┌─────────────────────────────────┐ │
│ │ agent@antigravity:~$ python app.py│
│ │ ✅ Server started on port 5000  │ │
│ └─────────────────────────────────┘ │
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
│ │ 8 messages • yesterday          │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

## 🔧 Architecture

### Backend (Python)
- **FastAPI**: HTTP + WebSocket server
- **LangGraph**: Agent workflow management
- **LangChain**: LLM integration
- **Tools**: Terminal, file operations, search

### Frontend (TypeScript)
- **VS Code Extension API**: UI integration
- **WebSocket Client**: Real-time updates
- **Diff Viewer**: Native VS Code diffs

### Agent Flow
```
User Input → LangGraph → Tool Selection → Execution → Response
     ↑                                                    ↓
     └──────────── Feedback Loop ────────────────────────┘
```

## 📁 Project Structure

```
my-antigravity/
├── brain.py              # Agent logic & tools
├── server.py             # FastAPI backend
├── utils.py              # Shared utilities
├── requirement.txt       # Python dependencies
├── extension-builder/
│   └── myantigravity/
│       ├── src/
│       │   └── extension.ts   # VS Code extension
│       ├── package.json
│       └── tsconfig.json
└── docs/
    ├── UPDATES_V2.md          # v2.0 changelog
    ├── QUICKSTART_V2.md       # Quick start guide
    └── CHANGELOG.md           # Full changelog
```

## 🛠️ Configuration

### Server Settings (server.py)
```python
# Change port
uvicorn.run(app, host="0.0.0.0", port=8000)

# Adjust recursion limit
config = {"recursion_limit": 50}
```

### Agent Behavior (brain.py)
```python
# Modify SYSTEM_PROMPT to change:
- How agent thinks and plans
- When it asks for confirmation  
- Error handling approach
- Input detection logic
```

## 📊 API Reference

### Chat
```http
POST /chat
Content-Type: application/json

{
  "message": "Build a Flask app",
  "session_id": "optional-uuid"
}

Response:
{
  "response": "I'll create...",
  "session_id": "uuid",
  "session_title": "Build a Flask app"
}
```

### Sessions
```http
GET /sessions
Response: { "ok": true, "sessions": [...] }

GET /session/{id}
Response: { "ok": true, "session": {...} }

DELETE /session/{id}
Response: { "ok": true, "message": "..." }

POST /clear-history
Body: { "session_id": "uuid" }
Response: { "ok": true, "message": "..." }
```

### WebSocket
```http
ws://localhost:8000/ws

Messages:
- {"type": "log", "message": "..."}
- {"type": "file_change", "change_id": "...", ...}
```

## 🐛 Troubleshooting

### Connection Issues
- Ensure server is running on port 8000
- Check firewall settings
- Verify OPENAI_API_KEY is set

### Extension Not Loading
```bash
cd extension-builder/myantigravity
npm install
npm run compile
# Press F5 in VS Code
```

### Async Errors (FIXED in v2.0)
- ✅ RuntimeWarning resolved
- ✅ Event loop errors fixed
- ✅ File operations stable

### Sessions Lost on Restart
- Sessions stored in memory (not persistent)
- Will add database in future version
- Export important conversations manually

## 📚 Documentation

- **QUICKSTART_V2.md** - Detailed setup guide
- **UPDATES_V2.md** - Version 2.0 changes
- **CHANGELOG.md** - Full version history
- **FILE_DIFF_FEATURE.md** - Diff implementation details
- **INTELLIGENT_EXECUTION_UPDATE.md** - Smart execution guide

## 🎯 Roadmap

### v2.1 (Planned)
- [ ] Session persistence (database)
- [ ] Export/import conversations
- [ ] Search within history
- [ ] Keyboard shortcuts

### v3.0 (Future)
- [ ] Multi-user support
- [ ] Cloud sync
- [ ] Custom tool plugins
- [ ] Voice input

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Update documentation
6. Submit pull request

## 📝 License

[Add your license here]

## 🙏 Acknowledgments

- **Inspired by**: Cursor, Antigravity
- **Built with**: LangChain, LangGraph, FastAPI, VS Code API
- **Powered by**: OpenAI GPT-4

## 📧 Support

For issues or questions:
- Check documentation
- Review troubleshooting section
- Open GitHub issue (if applicable)
- Provide detailed error messages

---

**Made with ❤️ by Divakar**

**Version 2.0.0 - January 21, 2026**

---

## 🎉 Quick Test

```bash
# Terminal 1: Start server
python3 server.py

# Terminal 2: Launch extension
cd extension-builder/myantigravity && code .
# Press F5 in VS Code

# In extension:
# 1. Type: "Create a hello.py file"
# 2. Review diff, click Accept
# 3. Type: "Run hello.py"
# 4. Click "Yes, Execute"
# 5. See output in terminal

# Test history:
# 1. Click "History" button
# 2. See your session
# 3. Click "New Chat"
# 4. Start fresh conversation
# 5. Load previous session
```

**🚀 You're ready to build with AI!**
