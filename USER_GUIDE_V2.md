# 👤 Antigravity v2.0 - User Guide

> Complete guide to using the new chat history and session management features

---

## 🎯 What's New in Your Tool

You now have **powerful session management**! Think of it like having multiple browser tabs, each with its own conversation history.

### Before v2.0 😕
- Only one conversation at a time
- Lost history when starting new chat
- Couldn't go back to previous conversations

### After v2.0 😊
- Multiple conversations (sessions)
- Full history preserved
- Easy navigation between chats
- Never lose a conversation

---

## 🚀 Getting Started

### 1. Start the Application

**Terminal 1 - Backend:**
```bash
cd /Users/divakar/Desktop/my-antigravity
python3 server.py
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Terminal 2 - Extension:**
```bash
cd /Users/divakar/Desktop/my-antigravity/extension-builder/myantigravity
code .
```

Then press `F5` in VS Code.

### 2. Open the Sidebar

Look for the Antigravity icon in the VS Code activity bar (left side).

---

## 💬 Using the Chat Interface

### The Layout

```
┌─────────────────────────────────────┐
│ Chat Sessions                       │  ← Header
│  [Clear] [New Chat] [History]       │  ← Control buttons
│ 💬 Build a Flask app...             │  ← Current session title
├─────────────────────────────────────┤
│                                     │
│ Your message...                     │
│                                     │
│ Agent's response...                 │  ← Chat messages
│                                     │
├─────────────────────────────────────┤
│ [Type your message...] [Send]       │  ← Input area
├─────────────────────────────────────┤
│ Terminal Output                     │
│                                     │
│ agent@antigravity:~$ command        │  ← Terminal section
│ output...                           │
└─────────────────────────────────────┘
```

---

## 🎮 Control Buttons Explained

### 1. Clear Button 🗑️

**What it does**: Removes all messages from current conversation

**When to use**:
- You want to clean up the current chat
- Start fresh but keep the same session ID
- Remove clutter while continuing same topic

**How to use**:
1. Click **"Clear"** button
2. Confirmation: Chat area clears
3. Session ID stays the same
4. You can continue the conversation

**Example:**
```
Before:
- You: Build a Flask app
- Agent: Here's the code...
- You: Add authentication
- Agent: Done...

[Click Clear]

After:
- (empty chat, ready for new messages)
- Still same session
```

---

### 2. New Chat Button ✨

**What it does**: Starts a completely fresh conversation

**When to use**:
- Starting a different project
- Switching topics completely
- Want a clean slate with new session ID

**How to use**:
1. Click **"New Chat"** button
2. Terminal shows: "✨ Started new chat session"
3. New session ID generated
4. Old conversation preserved in history
5. Type your first message

**Example:**
```
Current session: "Build a Flask app"
[Click New Chat]
New session: "New Chat"

Now you can start: "Build a React app"
Old Flask conversation still in history!
```

---

### 3. History Button 📚

**What it does**: Opens a modal showing all your past conversations

**When to use**:
- Want to continue old conversation
- Check what you built yesterday
- Delete old sessions
- Browse your chat history

**How to use**:
1. Click **"History"** button
2. Modal opens showing all sessions
3. Each session shows:
   - Title (first message)
   - Number of messages
   - How long ago (e.g., "2h ago")
   - Delete button (×)
4. Click any session to load it
5. Click × to delete a session
6. Click outside modal or × at top to close

---

## 📚 Working with Chat History

### The History Modal

```
┌─────────────────────────────────────┐
│ 📚 Chat History                  × │  ← Close button
├─────────────────────────────────────┤
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ Build a Flask API...          × │ │  ← Session card
│ │ 15 messages • 2h ago            │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ Fix login bug in auth.py      × │ │
│ │ 8 messages • 5h ago             │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ Create a React component      × │ │
│ │ 20 messages • yesterday         │ │
│ └─────────────────────────────────┘ │
│                                     │
└─────────────────────────────────────┘
```

### Understanding Session Cards

**Title**: Auto-generated from your first message
- "Build a Flask API..." → First 50 characters
- Makes it easy to identify conversations

**Message Count**: Total messages in conversation
- Includes both your messages and agent responses
- "15 messages" = 15 total back-and-forth

**Timestamp**: When last updated
- "just now" - Less than 1 minute
- "5m ago" - Minutes ago
- "2h ago" - Hours ago  
- "yesterday" - 1 day ago
- "2d ago" - Days ago
- "Jan 15" - Older dates

**Delete Button (×)**: Remove session permanently

---

## 🎯 Common Workflows

### Workflow 1: Continue Yesterday's Work

**Scenario**: You were building a Flask app yesterday, want to continue today

**Steps**:
1. Click **"History"** button
2. Find session: "Build a Flask API with auth..."
3. Check timestamp: "yesterday"
4. Click the session card
5. Modal closes automatically
6. Full conversation history loads
7. Session title updates to show current topic
8. Continue where you left off!

**You'll see**:
```
💬 Build a Flask API with auth...

You: Build a Flask API with authentication
Agent: I'll create app.py with Flask and JWT...
You: Add a /login endpoint
Agent: Done, here's the diff...
[All your previous messages]

[Now type your next message]
You: Add password hashing
```

---

### Workflow 2: Start Multiple Projects

**Scenario**: Working on 3 different projects

**Steps**:

**Project 1 - Morning:**
```
[Click New Chat]
You: "Build a Flask REST API"
[Work on it for a while]
Session saved automatically
```

**Project 2 - Afternoon:**
```
[Click New Chat]
You: "Create a React dashboard"
[Work on this new project]
Session saved automatically
```

**Project 3 - Evening:**
```
[Click New Chat]
You: "Debug Python script"  
[Work on debugging]
Session saved automatically
```

**Next Day - Switch Between Them:**
```
[Click History]
- Build a Flask REST API... (25 messages)
- Create a React dashboard... (18 messages)
- Debug Python script... (10 messages)

[Click any one to continue that project]
```

---

### Workflow 3: Clean Up Old Sessions

**Scenario**: Have 20+ old sessions, want to delete unused ones

**Steps**:
1. Click **"History"** button
2. Review each session:
   - Read the title
   - Check message count
   - See when last used
3. Click **×** on sessions you don't need
4. Confirm deletion
5. Session disappears from list
6. If it was current session, new chat starts

**Example**:
```
Before:
- Test session... (2 messages) • 5d ago  [×]  ← Delete this
- Build app... (50 messages) • 2h ago         ← Keep
- Random test... (1 message) • week ago [×]  ← Delete this

After:
- Build app... (50 messages) • 2h ago         ← Only this remains
```

---

### Workflow 4: Experiment Safely

**Scenario**: Want to try something without messing up current work

**Steps**:
1. Currently working in: "Build production app"
2. Want to experiment with different approach
3. Click **"New Chat"** (original preserved!)
4. Try experimental approach
5. If it works: Great! Use this session
6. If it doesn't work: 
   - Click **"History"**
   - Load original "Build production app"
   - Continue with original plan
7. Delete experimental session if not needed

---

## 💡 Pro Tips

### Tip 1: Descriptive First Messages
Your first message becomes the session title!

**Bad first message**:
```
You: "Hi"
Title: "Hi" ← Not helpful!
```

**Good first message**:
```
You: "Build a Flask API with JWT authentication and PostgreSQL"
Title: "Build a Flask API with JWT authentication..." ← Very clear!
```

### Tip 2: Regular Cleanup
Delete sessions you don't need anymore:
- One-time experiments
- Successfully completed projects
- Test conversations
- Duplicates

Keeps your history manageable!

### Tip 3: One Project Per Session
Don't mix unrelated work in one session:

**Bad** (mixed session):
```
You: Build a Flask app
Agent: Done
You: Now create a React component  ← Different project!
Agent: Done
You: Fix that Flask bug
Agent: Which Flask app?  ← Confused!
```

**Good** (separate sessions):
```
Session 1: "Build a Flask app"
- All Flask work here

Session 2: "Create React components"  
- All React work here
```

### Tip 4: Use Clear for Pivots
If conversation goes off track, use **Clear**:

```
Current mess:
You: Build app
Agent: Done
You: Actually change approach
Agent: Done  
You: No wait, different thing
Agent: Confused...

[Click Clear]

Fresh start in same session:
You: Let's start over. Build X with approach Y.
Agent: Clear instructions, better results!
```

### Tip 5: Load Session Before Big Changes
Before making major changes to a project:

1. Click **"History"**
2. Note your current session
3. Make changes
4. If something breaks:
   - Reload that session
   - Review what worked before
   - Compare approaches

---

## 🎨 Understanding the UI

### Session Title Bar

The title bar shows your current conversation:

```
💬 Build a Flask API with authentication...
```

**What it tells you**:
- 💬 You're in an active session
- Title from your first message
- Truncated if too long (shows first ~50 chars)

**When it updates**:
- When you start new chat: "New Chat"
- After first message: Your message becomes title
- When you load session: Shows that session's title

### Chat Area

```
┌─────────────────────────────────────┐
│ You:                                │  ← Your messages (lighter)
│ Build a Flask API                   │
│                                     │
│ Agent:                              │  ← Agent messages (different color)
│ I'll create app.py with...          │
└─────────────────────────────────────┘
```

**Color coding**:
- Your messages: One color
- Agent messages: Different color
- Easy to scan conversation

### Terminal Area

```
┌─────────────────────────────────────┐
│ agent@antigravity:~$ python3 app.py │  ← Command (prompt style)
│ Starting server...                  │  ← Output
│ ✅ Server started on port 5000      │  ← Success (green)
└─────────────────────────────────────┘
```

**Color meanings**:
- 🟢 Green: Success messages
- 🔴 Red: Errors
- 🟡 Yellow: Warnings
- 🔵 Blue: Info/status

---

## 📱 Keyboard & Mouse

### Keyboard Shortcuts

**Send message**:
- Type message → Press `Enter`
- Or click **Send** button

**Close modal**:
- Press `Esc` (when modal open)
- Or click × button
- Or click outside modal

### Mouse Actions

**In History Modal**:
- **Click session card** → Load session
- **Click ×** on card → Delete that session
- **Click × at top** → Close modal
- **Click outside** → Close modal

**In Chat**:
- **Click input field** → Type message
- **Click Send** → Send message
- **Click Clear** → Clear current chat
- **Click New Chat** → Start fresh
- **Click History** → Open modal

---

## ❓ Frequently Asked Questions

### Q: Will my sessions be saved if I close VS Code?
**A**: No, sessions are stored in memory only. When you restart the server, all sessions are lost. This will be fixed in a future version with database support.

### Q: How many sessions can I have?
**A**: Technically unlimited, but keep it manageable (10-20 active sessions). Delete old ones regularly.

### Q: What happens if I delete the current session?
**A**: A new chat will start automatically. The deleted session is permanently removed.

### Q: Can I rename session titles?
**A**: Not yet! Titles are auto-generated from first message. Make your first message descriptive!

### Q: Can I export my chat history?
**A**: Not yet, planned for future version. Currently, you'd need to copy/paste manually.

### Q: Do sessions share context?
**A**: No! Each session is completely independent. The agent only knows about messages in the current session.

### Q: Can I merge two sessions?
**A**: Not directly. You'd need to manually copy messages from one to another.

### Q: What if History button does nothing?
**A**: Check that:
1. Server is running
2. WebSocket connected
3. Console for errors
4. Try refreshing extension

---

## 🔧 Troubleshooting

### Problem: "No sessions appear in history"
**Solutions**:
- You haven't had any conversations yet
- Server was restarted (sessions lost)
- Check server console for errors

### Problem: "Can't load session"
**Solutions**:
- Session might have been deleted
- Server restarted
- Try clicking New Chat and starting fresh

### Problem: "Modal won't close"
**Solutions**:
- Click × at top right
- Click outside the modal
- Press Esc key
- Refresh the extension

### Problem: "Session title shows 'New Chat'"
**Solutions**:
- You haven't sent first message yet
- Send a message and title will update
- Title generated after first message

---

## 🎯 Best Practices Summary

### DO ✅
- Start new chat for each project
- Use descriptive first messages
- Delete old sessions regularly
- Load sessions to continue work
- Clear when conversation gets messy

### DON'T ❌
- Mix unrelated projects in one session
- Keep hundreds of old sessions
- Use vague first messages like "hi"
- Delete sessions you might need later
- Assume sessions persist after server restart

---

## 🎉 You're Ready!

You now know how to:
- ✅ Use all three control buttons
- ✅ Navigate chat history
- ✅ Load and delete sessions
- ✅ Manage multiple projects
- ✅ Keep your workspace organized

### Quick Reference Card

```
┌─────────────────────────────────────┐
│ BUTTON ACTIONS                      │
├─────────────────────────────────────┤
│ Clear      → Remove current messages│
│ New Chat   → Start fresh session    │
│ History    → View all sessions      │
├─────────────────────────────────────┤
│ IN HISTORY MODAL                    │
├─────────────────────────────────────┤
│ Click card → Load session           │
│ Click ×    → Delete session         │
│ Click out  → Close modal            │
└─────────────────────────────────────┘
```

---

**Happy building with Antigravity v2.0!** 🚀

*For technical details, see: QUICKSTART_V2.md*  
*For bug fixes, see: FIXES_SUMMARY.md*  
*For testing, see: TEST_V2.md*

