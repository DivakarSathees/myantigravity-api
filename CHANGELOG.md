# Changelog - Antigravity AI Coding Assistant

## Version 2.0.0 - January 21, 2026

### 🐛 Critical Bug Fixes

#### Fixed RuntimeWarning: Coroutine Not Awaited
- **Issue**: `RuntimeWarning: coroutine 'broadcast_log' was never awaited`
- **Root Cause**: Synchronous `manage_file` function trying to call async functions
- **Solution**: Implemented queue-based notification system
- **Impact**: No more warnings, stable file operations
- **Files**: `brain.py`, `utils.py`, `server.py`

#### Fixed "No Running Event Loop" Error  
- **Issue**: File edits failed with event loop error
- **Root Cause**: Same as above - async calls in sync context
- **Solution**: Queue notifications, process in async context
- **Impact**: File editing works flawlessly
- **Files**: `brain.py`, `utils.py`, `server.py`

### ✨ New Features

#### Chat History & Session Management
- **View all chat sessions** with metadata
- **Switch between conversations** seamlessly
- **Auto-generated session titles** from first message
- **Delete old sessions** for cleanup
- **Start new chats** without losing history
- **Relative timestamps** (e.g., "2h ago", "5m ago")
- **Session persistence** across interactions
- **Message counts** per session

**New UI Components:**
- Session title display
- "History" button with modal
- "New Chat" button
- "Clear" button for current session
- Session cards with metadata
- Delete buttons per session

**New API Endpoints:**
```
GET  /sessions            - List all sessions
GET  /session/{id}        - Get session details
DELETE /session/{id}      - Delete a session
POST /clear-history       - Clear session messages
```

### 🎨 UI Improvements

#### Enhanced Chat Interface
- **Session title bar** showing current conversation
- **Three-button control panel** for session management
- **Professional modal** for history navigation
- **Hover effects** on interactive elements
- **Dark theme** with VS Code color scheme
- **Responsive design** for different panel sizes

#### Better Visual Feedback
- Status indicators for actions
- Color-coded terminal output
- Smooth modal transitions
- Click-outside-to-close UX
- Relative time formatting

### 🔧 Technical Improvements

#### Async Queue System
```python
# New architecture
file_change_queue = []                    # Queue notifications
notify_file_change()                      # Sync function
process_file_change_queue()               # Async processor
```

#### Session Data Structure
```python
{
    "id": "uuid",
    "messages": [HumanMessage, AIMessage],
    "created_at": "ISO timestamp",
    "updated_at": "ISO timestamp", 
    "title": "Auto-generated title"
}
```

#### Helper Functions
- `get_or_create_session()` - Session lifecycle management
- `updateSessionTitle()` - UI updates
- `formatDate()` - Relative time formatting
- `loadSession()` - History restoration
- `deleteSession()` - Cleanup

### 📚 Documentation

**New Documents:**
- `UPDATES_V2.md` - Detailed version 2.0 changelog
- `QUICKSTART_V2.md` - Updated quick start guide
- `CHANGELOG.md` - This file

**Updated Documents:**
- API reference with new endpoints
- Usage examples with session management
- Troubleshooting for fixed issues

---

## Version 1.4.0 - January 20, 2026

### ✨ Features Added

#### File Diff Display in Editor
- **Native VS Code diff viewer** integration
- **Accept/Reject buttons** as notifications
- **Unified diff format** for clarity
- **Full file comparison** side-by-side
- **Syntax highlighting** in diff view

#### Intelligent Execution
- **Auto-detection** of input requirements
- **Smart file reading** before execution
- **Input piping** for automated scripts
- **Planning phase** before actions
- **Context-aware** command construction

#### Enhanced Error Handling
- **Automatic error analysis**
- **Fix proposals** with diffs
- **Rerun confirmations** after fixes
- **Dependency installation** on import errors
- **Detailed error messages** with context

### 🐛 Fixes
- Increased recursion limit to 50
- TypeScript compilation errors resolved
- Terminal output formatting improved
- WebSocket error handling enhanced

---

## Version 1.3.0 - January 19, 2026

### ✨ Features Added

#### Interactive Terminal
- **Command confirmation** with buttons
- **Real-time output streaming**
- **Color-coded messages** by type
- **Terminal-like prompt** display
- **Separate chat/terminal views**

#### Enhanced Agent Behavior
- **Explicit confirmation requests** before execution
- **Wait for user approval** pattern
- **Better command formatting**
- **Status indicators** throughout

### 🔧 Improvements
- System prompt refinements
- Tool execution logging
- WebSocket stability
- UI/UX polish

---

## Version 1.2.0 - January 18, 2026

### ✨ Features Added

#### Chat Memory
- **Session-based conversations**
- **Full context preservation**
- **LangGraph state management**
- **History persistence** (in-memory)

#### File Management
- **Read file** operations
- **Write file** with diffs
- **Create new files**
- **Directory auto-creation**

### 🔧 Improvements
- Modular code organization
- Separated WebSocket utilities
- Better error messages
- Terminal output capture

---

## Version 1.1.0 - January 17, 2026

### ✨ Features Added

#### Basic Agent Tools
- `execute_terminal` - Run shell commands
- `manage_file` - File operations
- `find_file` - File search

#### VS Code Extension
- Webview sidebar
- Input/output interface
- Basic styling
- Server connection

### 🔧 Improvements
- LangChain integration
- OpenAI API setup
- FastAPI server structure

---

## Version 1.0.0 - January 16, 2026

### 🎉 Initial Release

#### Core Features
- **FastAPI backend** server
- **LangGraph agent** workflow
- **VS Code extension** skeleton
- **WebSocket** communication
- **Basic chat** interface

#### Tools Implemented
- Terminal command execution
- File reading
- File writing
- File finding

#### Tech Stack
- Python 3.9+
- FastAPI
- LangChain/LangGraph
- TypeScript
- VS Code Extension API

---

## Upgrade Guide

### From v1.x to v2.0

**Backend Changes:**
```bash
# Update server.py
python3 server.py  # Restart required
```

**Frontend Changes:**
```bash
cd extension-builder/myantigravity
npm install  # May have new deps
npm run compile
# Press F5 to reload extension
```

**Data Migration:**
- No breaking changes to existing functionality
- Sessions are backwards compatible
- Old behavior preserved, new features added

**API Changes:**
- All v1.x endpoints still work
- New endpoints added (optional)
- Response format unchanged for `/chat`

---

## Known Issues

### Current Limitations

1. **Session Persistence**
   - Sessions stored in memory only
   - Lost on server restart
   - No database yet

2. **WebSocket Reconnection**
   - Limited retry logic
   - May need manual refresh

3. **Large File Diffs**
   - Very large files may lag UI
   - Consider splitting changes

4. **Concurrent Sessions**
   - One active user at a time
   - No multi-user support yet

### Planned Fixes

- [ ] Database for session persistence
- [ ] Better WebSocket handling
- [ ] Multi-user support
- [ ] Session export/import
- [ ] Search in history

---

## Migration from Cursor/Antigravity

If you're coming from similar tools:

1. **Install**: Follow QUICKSTART_V2.md
2. **Familiar Features**:
   - File diffs ✅
   - Terminal execution ✅
   - Chat interface ✅
   - Code generation ✅
3. **New Features**:
   - Session management
   - Better error handling
   - Input auto-detection
4. **Differences**:
   - Local backend (not cloud)
   - Open source
   - Customizable prompts

---

## Contributing

### Bug Reports
- Include version number
- Steps to reproduce
- Expected vs actual behavior
- Error messages/screenshots

### Feature Requests
- Describe use case
- Explain expected behavior
- Consider implementation complexity

### Pull Requests
- Follow code style
- Add tests if applicable
- Update documentation
- Reference issue number

---

## Credits

**Developer**: Divakar
**Inspired By**: Cursor, Antigravity
**Built With**: LangChain, LangGraph, FastAPI, VS Code API
**Version**: 2.0.0
**Date**: January 21, 2026

---

## License

[Add your license here]

---

## Support

For issues, questions, or suggestions:
- Check documentation in project root
- Review known issues above
- Test with latest version
- Provide detailed bug reports

---

**Thank you for using Antigravity!** 🚀

