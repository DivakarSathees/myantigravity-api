# Version 2.0 Updates - Chat History & Bug Fixes

## 📅 Date: January 21, 2026

## 🐛 Critical Bug Fixes

### 1. Fixed RuntimeWarning: Coroutine Not Awaited
**Issue:**
```
RuntimeWarning: coroutine 'broadcast_log' was never awaited
```

**Problem:**
The `manage_file` tool was a regular (non-async) function trying to call async functions like `broadcast_log` and `broadcast_file_change` using `asyncio.create_task()`. This failed because there was no running event loop in the synchronous context.

**Solution:**
- Created a synchronous notification queue system (`file_change_queue`)
- Added `notify_file_change()` - a non-async function that queues notifications
- Added `process_file_change_queue()` - called from async context to broadcast queued changes
- Modified `manage_file` to use the sync notification system

**Files Changed:**
- `brain.py` - Updated `manage_file` to use `notify_file_change`
- `utils.py` - Added queue system and `process_file_change_queue()`
- `server.py` - Call `process_file_change_queue()` after tool execution

### 2. Fixed "No Running Event Loop" Error
**Issue:**
When editing files, VS Code showed:
```
I'm sorry — the edit couldn't be saved due to an internal error ("no running event loop").
```

**Solution:**
Same as above - the queue-based notification system ensures async operations only happen in async contexts.

---

## ✨ New Feature: Chat History Navigation

### Overview
Users can now:
- **View all past chat sessions** with titles and metadata
- **Switch between sessions** to continue previous conversations
- **Delete old sessions** to clean up history
- **Start new chats** without losing previous ones
- **See session titles** automatically generated from first message

### UI Components

#### 1. Session Header
- **Current session title** displayed below controls
- **Three action buttons:**
  - `Clear` - Clear current session history
  - `New Chat` - Start fresh conversation
  - `History` - Open sessions modal

#### 2. Sessions Modal
- **Modal dialog** showing all chat sessions
- **Session cards** with:
  - Title (first 50 chars of first message)
  - Message count
  - Last updated timestamp (relative time)
  - Delete button (×)
- **Click session** to load and continue
- **Click delete (×)** to remove session

### Backend API

#### New Endpoints

**GET /sessions**
```json
{
  "ok": true,
  "sessions": [
    {
      "id": "uuid",
      "title": "Build a web app...",
      "created_at": "2026-01-21T10:30:00",
      "updated_at": "2026-01-21T10:45:00",
      "message_count": 12
    }
  ]
}
```

**GET /session/{session_id}**
```json
{
  "ok": true,
  "session": {
    "id": "uuid",
    "title": "Build a web app...",
    "created_at": "2026-01-21T10:30:00",
    "updated_at": "2026-01-21T10:45:00",
    "messages": [
      {"role": "user", "content": "..."},
      {"role": "agent", "content": "..."}
    ]
  }
}
```

**DELETE /session/{session_id}**
```json
{
  "ok": true,
  "message": "Session uuid deleted"
}
```

**POST /clear-history**
```json
{
  "ok": true,
  "message": "History cleared for session uuid"
}
```

### Data Structure

**Session Object:**
```python
{
    "id": "uuid",
    "messages": [HumanMessage, AIMessage, ...],
    "created_at": "ISO timestamp",
    "updated_at": "ISO timestamp",
    "title": "Auto-generated or default"
}
```

**Title Generation:**
- Automatically created from first 50 characters of first message
- Updated only once when session is created
- Displayed in both header and history modal

### Frontend Implementation

**State Management:**
```typescript
let sessionId = null;              // Current session UUID
let currentSessionTitle = "New Chat";  // Display title
```

**Key Functions:**
- `updateSessionTitle()` - Updates UI with current title
- `newChat()` - Clears state, starts fresh
- `showSessions()` - Fetches and displays all sessions
- `loadSession(id)` - Loads specific session history
- `deleteSession(id)` - Removes session permanently
- `formatDate(dateStr)` - Relative time formatting

**Time Formatting:**
- "just now" - < 1 minute ago
- "5m ago" - < 1 hour ago
- "3h ago" - < 24 hours ago
- "2d ago" - < 7 days ago
- Full date - older than 7 days

---

## 🎨 UI Improvements

### Modal Styling
- **Dark overlay** with 70% opacity
- **Centered dialog** with max-width 500px
- **VS Code theme integration** for all colors
- **Hover effects** on session items
- **Click outside to close** modal

### Session Cards
- **Clean layout** with title and metadata
- **Hover highlight** for better UX
- **Delete button** positioned in top-right
- **Color-coded text** using VS Code variables

### Buttons
- **Compact design** with small font
- **Float right** for space efficiency
- **Margin spacing** for visual separation
- **Consistent styling** across all actions

---

## 🔧 Technical Details

### Async Queue System

**Problem:**
```python
# BEFORE (Broken)
@tool
def manage_file(...):
    asyncio.create_task(broadcast_log(...))  # No event loop!
```

**Solution:**
```python
# AFTER (Fixed)
file_change_queue = []

def notify_file_change(change_id, file_path, is_new=False):
    file_change_queue.append({...})

async def process_file_change_queue():
    while file_change_queue:
        notification = file_change_queue.pop(0)
        await broadcast_file_change(notification["change_id"])
```

### Session Persistence

**Storage:**
```python
chat_sessions: Dict[str, dict] = {}
```

**Helper Function:**
```python
def get_or_create_session(session_id: str = None):
    if not session_id:
        session_id = str(uuid4())
    
    if session_id not in chat_sessions:
        chat_sessions[session_id] = {
            "id": session_id,
            "messages": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "title": "New Chat"
        }
    
    return session_id, chat_sessions[session_id]
```

---

## 🚀 Usage Examples

### Starting a New Chat
1. Click **"New Chat"** button
2. Session state clears
3. Terminal shows: `✨ Started new chat session`
4. Type new message

### Viewing History
1. Click **"History"** button
2. Modal opens with all sessions
3. Sessions sorted by most recent first
4. See titles, message counts, timestamps

### Loading Old Session
1. Open history modal
2. Click on any session card
3. Chat area populates with full history
4. Continue conversation from where you left off
5. Modal closes automatically

### Deleting Sessions
1. In history modal, click **×** on session card
2. Confirm deletion dialog appears
3. Session removed from list
4. If current session deleted, new chat starts

### Clearing Current Session
1. Click **"Clear"** button
2. Current session messages cleared
3. Session ID preserved for continuation
4. Terminal shows: `🗑️ Chat history cleared`

---

## 📁 Files Modified

### Backend
- `brain.py` - Fixed async issues in `manage_file`
- `utils.py` - Added queue system and processing
- `server.py` - Added session endpoints, updated chat handler

### Frontend
- `extension.ts` - Added modal, buttons, session management

---

## ✅ Testing Checklist

- [ ] File edits work without "no event loop" error
- [ ] RuntimeWarning for coroutines resolved
- [ ] New chat creates fresh session
- [ ] History modal displays all sessions
- [ ] Loading session restores full conversation
- [ ] Deleting session works correctly
- [ ] Session titles auto-generate properly
- [ ] Time formatting shows relative times
- [ ] Clear button clears current session
- [ ] Multiple sessions can coexist
- [ ] WebSocket still receives file diffs
- [ ] Modal closes on outside click
- [ ] UI matches VS Code theme

---

## 🎯 Key Improvements

1. **Stability** - No more async/event loop errors
2. **Persistence** - Chat history preserved across sessions
3. **Organization** - Easy navigation between conversations
4. **UX** - Clean modal interface for history
5. **Performance** - Efficient queue-based notification system

---

## 🔮 Future Enhancements

- [ ] Export chat sessions to files
- [ ] Search within chat history
- [ ] Session tags/categories
- [ ] Persistent storage (database)
- [ ] Session sharing/import
- [ ] Keyboard shortcuts for navigation
- [ ] Bulk delete old sessions
- [ ] Session rename capability

---

## 📚 Related Documentation
- `QUICKSTART.md` - Setup instructions
- `FILE_DIFF_FEATURE.md` - Diff implementation
- `RECURSION_FIX.md` - Graph recursion fix
- `INTELLIGENT_EXECUTION_UPDATE.md` - Agent behavior

---

**Version 2.0 brings stability and powerful session management to the Antigravity tool!** 🚀

