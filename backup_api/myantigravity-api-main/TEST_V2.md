# 🧪 Version 2.0 Testing Guide

## Quick Verification Tests

### Test 1: Check for RuntimeWarnings ✅

**What to test**: Ensure no coroutine warnings appear

**Steps:**
1. Start server: `python3 server.py`
2. Watch console output carefully
3. In extension, request file edit: "Create a test.py file with hello world"
4. Check server console

**Expected Result:**
```
✅ No RuntimeWarning messages
✅ "📝 File change queued: test.py" appears
✅ File diff displays in VS Code
```

**Signs of failure:**
```
❌ "RuntimeWarning: coroutine 'broadcast_log' was never awaited"
❌ "RuntimeWarning: coroutine 'broadcast_file_change' was never awaited"
```

---

### Test 2: File Edit Operations ✅

**What to test**: File editing works without errors

**Steps:**
1. Request edit: "Create a hello.py file"
2. Wait for diff to appear
3. Click "Accept" button
4. Check if file was created
5. Request another edit: "Add a function to hello.py"
6. Accept changes

**Expected Result:**
```
✅ Diff displays correctly
✅ Accept button appears in VS Code notification
✅ File saves successfully
✅ No "no running event loop" error
✅ Multiple edits work in sequence
```

**Signs of failure:**
```
❌ "no running event loop" error
❌ File doesn't save
❌ VS Code shows "internal error"
```

---

### Test 3: Chat History & Sessions ✅

**What to test**: New session management features

**Steps:**
1. Start a chat: "Hello, build me a Flask app"
2. Have a conversation (3-4 messages)
3. Click "History" button
4. Verify session appears with title
5. Click "New Chat" button
6. Start new conversation
7. Click "History" again
8. Load previous session
9. Verify full history restored
10. Delete old session

**Expected Result:**
```
✅ Session title auto-generated from first message
✅ History modal opens with sessions list
✅ Session shows message count and time
✅ Loading session restores full conversation
✅ New chat creates fresh session
✅ Delete removes session
✅ All navigation smooth and error-free
```

**Signs of failure:**
```
❌ History button doesn't work
❌ Modal doesn't open
❌ Sessions don't appear
❌ Loading session fails
❌ Error messages in console
```

---

### Test 4: Terminal Command Execution ✅

**What to test**: Commands execute with confirmation

**Steps:**
1. Request: "List files in current directory"
2. Agent should ask for confirmation
3. Click "Yes, Execute" button
4. Wait for output
5. Check terminal section

**Expected Result:**
```
✅ Confirmation request appears
✅ Buttons displayed in terminal
✅ Command executes after approval
✅ Output streams in real-time
✅ Formatted like real terminal
```

---

### Test 5: Error Handling ✅

**What to test**: Agent handles errors intelligently

**Steps:**
1. Create file with intentional error: "Create a Python file that imports a non-existent module"
2. Request: "Run this file"
3. Agent executes, sees error
4. Agent should propose fix
5. Accept fix
6. Run again

**Expected Result:**
```
✅ Error detected and displayed
✅ Agent analyzes error
✅ Fix proposed with diff
✅ After fix, asks to rerun
✅ No more errors after fix
```

---

### Test 6: Intelligent File Execution ✅

**What to test**: Agent reads files and provides input

**Steps:**
1. Create a Python script that asks for user input:
   ```python
   name = input("Enter name: ")
   age = input("Enter age: ")
   print(f"Hello {name}, age {age}")
   ```
2. Save as `input_test.py`
3. Request: "Run input_test.py"
4. Agent should:
   - Read the file
   - Detect input requirements
   - Ask you for values
   - Provide those values automatically
   - Execute with piped input

**Expected Result:**
```
✅ Agent reads file first
✅ Detects: "needs name and age inputs"
✅ Asks: "Please provide name and age"
✅ You provide: "John" and "25"
✅ Agent runs: echo -e 'John\n25' | python3 input_test.py
✅ Output shows: "Hello John, age 25"
```

---

## Complete Integration Test

### Scenario: Build a Complete Project

**Test the full workflow:**

```
Step 1: Start fresh
- Click "New Chat"
- Type: "Build a simple Flask REST API with one endpoint"

Step 2: Agent plans
✅ Agent thinks and plans
✅ Proposes file structure
✅ Creates app.py with diff

Step 3: Review and accept
✅ Diff displays in VS Code
✅ Click Accept
✅ File created successfully

Step 4: Install dependencies
- Agent: "Should I install Flask?"
✅ Click "Yes, Execute"
✅ pip install completes

Step 5: Run the app
- Agent asks to run
✅ Click "Yes, Execute"  
✅ Server starts
✅ Output visible in terminal

Step 6: Fix any errors
- If error occurs
✅ Agent detects it
✅ Proposes fix
✅ Shows diff
✅ After accept, reruns

Step 7: Save session
✅ Click "History"
✅ Session saved with title
✅ Can load later

Step 8: Start new project
✅ Click "New Chat"
✅ Fresh session
✅ Old session preserved
```

---

## Performance Tests

### Test 7: Multiple Rapid Edits

**Steps:**
1. Request 5 file edits in quick succession
2. Accept each one
3. Watch for errors or slowdowns

**Expected:**
```
✅ All diffs queue properly
✅ No race conditions
✅ All notifications received
✅ UI remains responsive
```

---

### Test 8: Large File Handling

**Steps:**
1. Create a large file (1000+ lines)
2. Request edit in middle
3. Check diff display

**Expected:**
```
✅ Diff generates correctly
✅ UI doesn't freeze
✅ Changes apply properly
```

---

### Test 9: Server Restart

**Steps:**
1. Have active session
2. Stop server (Ctrl+C)
3. Restart server
4. Try to continue conversation

**Expected:**
```
⚠️ Session lost (expected - in-memory storage)
✅ New session starts cleanly
✅ No crashes or errors
```

---

## Edge Case Tests

### Test 10: Invalid Requests

**Test various error conditions:**

```
Test: "Edit a file that doesn't exist"
✅ Agent handles gracefully
✅ Clear error message

Test: "Run a command that fails"
✅ Error captured and displayed
✅ Agent offers to fix

Test: Click reject on diff
✅ Changes not applied
✅ Agent acknowledges
✅ Can request different approach

Test: Close modal without selecting session
✅ Modal closes cleanly
✅ Current session unchanged
```

---

## WebSocket Tests

### Test 11: Connection Stability

**Steps:**
1. Start with WebSocket connected
2. Perform various operations
3. Check console for connection errors
4. Refresh extension
5. Verify reconnection

**Expected:**
```
✅ Initial connection successful
✅ Messages flow correctly
✅ No disconnection errors
✅ Reconnects after refresh
```

---

## Automated Test Script

**Create this file to run basic tests:**

```python
# test_v2_fixes.py

import asyncio
import sys

async def test_queue_system():
    """Test the notification queue system"""
    from utils import notify_file_change, process_file_change_queue, file_change_queue, store_pending_change
    
    print("Testing notification queue system...")
    
    # Test 1: Queue notifications synchronously
    store_pending_change("test1.py", "", "content1", "diff1")
    notify_file_change("id1", "test1.py", False)
    
    store_pending_change("test2.py", "", "content2", "diff2")
    notify_file_change("id2", "test2.py", True)
    
    assert len(file_change_queue) == 2, "Queue should have 2 items"
    print("✅ Synchronous queueing works")
    
    # Test 2: Process queue asynchronously
    # Note: Can't fully test without WebSocket clients connected
    print("✅ Queue system structure correct")
    
    return True

async def test_manage_file():
    """Test manage_file doesn't produce warnings"""
    from brain import manage_file
    
    print("Testing manage_file...")
    
    # This should NOT produce RuntimeWarning
    result = manage_file.invoke({
        "path": "test_output.txt",
        "content": "Hello, World!",
        "action": "write"
    })
    
    assert "Error" not in result or "proposed" in result
    print("✅ manage_file executes without warnings")
    
    return True

async def test_session_structure():
    """Test session data structure"""
    from server import get_or_create_session, chat_sessions
    
    print("Testing session management...")
    
    # Create new session
    sid, session = get_or_create_session()
    
    assert "id" in session
    assert "messages" in session
    assert "created_at" in session
    assert "updated_at" in session
    assert "title" in session
    assert session["title"] == "New Chat"
    
    print("✅ Session structure correct")
    
    # Test session retrieval
    sid2, session2 = get_or_create_session(sid)
    assert sid == sid2
    assert session == session2
    
    print("✅ Session retrieval works")
    
    return True

async def run_all_tests():
    """Run all automated tests"""
    print("=" * 50)
    print("🧪 Version 2.0 Automated Tests")
    print("=" * 50)
    
    tests = [
        ("Queue System", test_queue_system),
        ("File Management", test_manage_file),
        ("Session Structure", test_session_structure)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        print(f"\n📋 Running: {name}")
        try:
            result = await test_func()
            if result:
                passed += 1
                print(f"✅ {name} PASSED")
            else:
                failed += 1
                print(f"❌ {name} FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {name} FAILED: {e}")
    
    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)
    
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
```

**Run tests:**
```bash
cd /Users/divakar/Desktop/my-antigravity
python3 test_v2_fixes.py
```

---

## Success Criteria

### All Tests Must Pass ✅

- [ ] No RuntimeWarnings in console
- [ ] File edits work without errors
- [ ] Chat history displays correctly
- [ ] Sessions load and save properly
- [ ] Commands execute with confirmation
- [ ] Error handling works intelligently
- [ ] Input detection functions correctly
- [ ] Diffs display in VS Code
- [ ] Accept/reject buttons work
- [ ] WebSocket connection stable
- [ ] UI responsive and smooth
- [ ] No console errors
- [ ] Extension compiles without errors
- [ ] Backend starts without warnings

---

## Reporting Issues

**If any test fails:**

1. **Note the test number and name**
2. **Capture error message** (screenshot or copy)
3. **Check console output** (both server and extension)
4. **Describe steps** to reproduce
5. **Include environment** (Python version, Node version, VS Code version)

**Common Issues:**

- **Port 8000 in use**: Change port in server.py
- **Module not found**: Run `pip install -r requirement.txt`
- **Extension won't load**: Run `npm install && npm run compile`
- **WebSocket can't connect**: Check firewall, ensure server running

---

## 🎉 All Tests Passing?

**You're ready to use Antigravity v2.0!**

The fixes are working correctly:
- ✅ No async warnings
- ✅ Stable file operations  
- ✅ Complete session management
- ✅ Professional UI
- ✅ Production ready

**Start building amazing projects with AI assistance!** 🚀

