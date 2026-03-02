# 🔍 Debug: View Diff Error

## The Issue
"Failed to load file change" when clicking "View Diff" button

## Quick Test

### 1. Check if server is receiving the request

**Start server and watch console:**
```bash
cd /Users/divakar/Desktop/my-antigravity
python3 server.py
```

When you click "View Diff", you should see:
```
🔍 Looking for pending change: abc12345
📊 Available changes: ['abc12345', 'xyz67890']
✅ Found change abc12345
```

### 2. Manual API Test

**Open a browser or use curl:**
```bash
# First, create a file change to get a change_id
# Look in server console for: "📝 File change queued: hello.py (ID: c37a2c89)"

# Then test the endpoint:
curl http://localhost:8000/get-pending-change/c37a2c89
```

**Expected Response:**
```json
{
  "ok": true,
  "change": {
    "file_path": "hello.py",
    "old_content": "",
    "new_content": "print('hello')",
    "diff": "...",
    "is_new_file": true
  }
}
```

**If you get:**
```json
{
  "ok": false,
  "error": "Change not found. Available: []"
}
```

This means the change isn't being stored properly.

### 3. Check the Flow

**Trace the change_id through the system:**

1. **Agent creates file** → `manage_file()` called
2. **Change stored** → `store_pending_change()` returns change_id
3. **Change queued** → `notify_file_change(change_id, ...)` 
4. **Queue processed** → `process_file_change_queue()`
5. **Broadcast** → `broadcast_file_change(change_id)`
6. **Frontend receives** → WebSocket message with change_id
7. **User clicks "View Diff"** → Sends change_id to `/get-pending-change/{change_id}`
8. **Endpoint looks up** → `pending_changes[change_id]`

**Where it might fail:**
- ❌ Change not stored: Issue in `store_pending_change()`
- ❌ Change_id mismatch: Different ID used in storage vs lookup
- ❌ Change cleared: Expired or already processed
- ❌ Import issue: `pending_changes` dict not accessible

### 4. Quick Fix to Try

**Restart everything fresh:**
```bash
# Terminal 1: Stop old server (Ctrl+C)
cd /Users/divakar/Desktop/my-antigravity
python3 server.py

# Terminal 2: Stop extension, press F5 to restart

# Terminal 3: Check the endpoint
curl http://localhost:8000/get-pending-change/test123
# Should return: {"ok": false, "error": "Change not found..."}
```

### 5. Test with Agent

1. **Request a file change**: "Create test.py"
2. **Watch server console** for:
   ```
   📝 File change queued: test.py (ID: abc12345)
   🔄 Processing file change queue...
   ✅ File change sent to WebSocket client
   ```
3. **Note the ID**: `abc12345`
4. **Click "View Diff"** button
5. **Watch server console** for:
   ```
   🔍 Looking for pending change: abc12345
   📊 Available changes: ['abc12345']
   ✅ Found change abc12345
   ```

**If you see:**
```
🔍 Looking for pending change: abc12345
📊 Available changes: []
❌ Change abc12345 not found
```

→ **Problem**: Change not being stored or already cleared

### 6. Common Issues

#### Issue 1: Change Already Processed
**Symptom**: Change ID in queue but not in `pending_changes`

**Cause**: Change was already accepted/rejected and removed

**Fix**: Changes should stay in `pending_changes` until explicitly approved/rejected

#### Issue 2: ID Mismatch
**Symptom**: Different IDs in logs

**Cause**: UUID being shortened differently in different places

**Fix**: Ensure consistent ID generation everywhere

#### Issue 3: Import Issue
**Symptom**: `pending_changes` appears empty

**Cause**: Multiple instances of the dict

**Fix**: Import at module level, not inside functions

### 7. Detailed Debug

**Add to extension.ts console:**
```javascript
window.viewDiffInEditor = function(changeId, filePath) {
    console.log('🔍 Requesting diff for:', changeId);
    console.log('📁 File path:', filePath);
    
    vscode.postMessage({
        type: 'viewDiff',
        changeId: changeId,
        filePath: filePath
    });
};
```

**Check browser console when clicking "View Diff":**
- Should see: `🔍 Requesting diff for: abc12345`

**Check VS Code Extension Host console:**
- Should see: Fetch request to `/get-pending-change/abc12345`

**Check server console:**
- Should see: `🔍 Looking for pending change: abc12345`

### 8. Temporary Workaround

If debugging takes time, you can still accept/reject without viewing:

**Just click the Accept or Reject buttons directly!**
- No diff viewing needed
- Changes applied immediately
- Bypasses the issue completely

---

## Next Steps

Please:
1. **Restart server** with debug logging
2. **Request a file change**
3. **Copy the server console output** when you click "View Diff"
4. **Share the output** so I can see exactly what's failing

The debug logs I added will show us:
- What change_id is being requested
- What change_ids are actually stored
- Whether the lookup succeeds or fails

This will tell us exactly where the issue is! 🔍

