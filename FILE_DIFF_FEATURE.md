# 📝 File Diff & Approval Feature - v1.5

## What's New?

When the agent edits files, you now see a **beautiful diff view** with **Accept/Reject buttons** - just like in modern IDEs!

---

## The Problem (Before v1.5)

```
You: "Fix the bug in app.py"
Agent: [Edits file]
Agent: "✅ Successfully wrote to app.py"

[File was changed without showing you what changed!]
```

**Issues:**
- ❌ No visibility into what changed
- ❌ Changes applied immediately
- ❌ No way to review before accepting
- ❌ Couldn't reject unwanted changes

---

## The Solution (v1.5) ✅

```
You: "Fix the bug in app.py"
Agent: [Analyzes and proposes fix]

Terminal shows:
┌──────────────────────────────────────────────────┐
│ 📝 File Change Request  EDIT                     │
│ app.py                                           │
├──────────────────────────────────────────────────┤
│ --- app.py (current)                             │
│ +++ app.py (proposed)                            │
│ @@ -5,7 +5,7 @@                                  │
│   def calculate():                               │
│       x = 10                                     │
│       y = 20                                     │
│ -     result = x + y + z  # Bug: z not defined  │
│ +     result = x + y      # Fixed!              │
│       return result                              │
├──────────────────────────────────────────────────┤
│  [✓ Accept Changes]  [✗ Reject Changes]         │
└──────────────────────────────────────────────────┘

[You click: ✓ Accept Changes]

Terminal: ✅ Changes applied to: app.py
```

**Now you have full control!**

---

## How It Works

### 1. Agent Proposes Changes

When agent calls `manage_file` to write/edit:
```python
manage_file(
    path="app.py",
    content="new content",
    action="write"
)
```

### 2. System Generates Diff

- Reads current file content
- Compares with proposed content
- Generates unified diff
- Stores as "pending change"

### 3. UI Shows Diff

Terminal displays:
- File path
- Badge: `NEW FILE` or `EDIT`
- Color-coded diff:
  - 🟢 Green lines = additions (+)
  - 🔴 Red lines = deletions (-)
  - ⚪ White lines = context
- Two buttons: Accept / Reject

### 4. User Decides

**Option A: Accept**
- Click "✓ Accept Changes"
- Changes applied to file
- Terminal shows: ✅ Changes applied

**Option B: Reject**
- Click "✗ Reject Changes"
- File remains unchanged
- Terminal shows: ❌ Changes rejected

---

## Visual Examples

### Example 1: Editing Existing File

```
┌────────────────────────────────────────────────────────┐
│ 📝 File Change Request  EDIT                           │
│ calculator.py                                          │
├────────────────────────────────────────────────────────┤
│ --- calculator.py (current)                            │
│ +++ calculator.py (proposed)                           │
│ @@ -1,5 +1,6 @@                                        │
│  def add(a, b):                                        │
│ -    return a + b                                      │
│ +    # Convert to int for safety                       │
│ +    return int(a) + int(b)                            │
│                                                         │
│  def subtract(a, b):                                   │
│      return a - b                                      │
├────────────────────────────────────────────────────────┤
│  [✓ Accept Changes]  [✗ Reject Changes]               │
└────────────────────────────────────────────────────────┘
```

### Example 2: Creating New File

```
┌────────────────────────────────────────────────────────┐
│ 📝 File Change Request  NEW FILE                       │
│ utils.py                                               │
├────────────────────────────────────────────────────────┤
│ def format_date(date_str):                             │
│     """Format a date string to YYYY-MM-DD"""           │
│     # Implementation here                              │
│     return formatted_date                              │
│                                                         │
│ def validate_email(email):                             │
│     """Validate email format"""                        │
│     # Implementation here                              │
│     return is_valid                                    │
├────────────────────────────────────────────────────────┤
│  [✓ Accept Changes]  [✗ Reject Changes]               │
└────────────────────────────────────────────────────────┘
```

### Example 3: Multiple Changes

```
┌────────────────────────────────────────────────────────┐
│ 📝 File Change Request  EDIT                           │
│ app.py                                                 │
├────────────────────────────────────────────────────────┤
│ --- app.py (current)                                   │
│ +++ app.py (proposed)                                  │
│ @@ -1,3 +1,4 @@                                        │
│ +import json                                           │
│  import os                                             │
│  import sys                                            │
│                                                         │
│ @@ -10,7 +11,10 @@                                     │
│  def process_data(data):                               │
│ -    result = data.split(',')                          │
│ -    return result                                     │
│ +    # Parse JSON instead of CSV                       │
│ +    try:                                              │
│ +        result = json.loads(data)                     │
│ +        return result                                 │
│ +    except json.JSONDecodeError:                      │
│ +        return None                                   │
├────────────────────────────────────────────────────────┤
│  [✓ Accept Changes]  [✗ Reject Changes]               │
└────────────────────────────────────────────────────────┘
```

---

## Color Coding

| Line Type | Color | Symbol | Meaning |
|-----------|-------|--------|---------|
| **Addition** | 🟢 Green | `+` | New line added |
| **Deletion** | 🔴 Red | `-` | Line removed |
| **Context** | ⚪ White | ` ` | Unchanged |
| **Location** | 🔵 Cyan | `@@` | Line numbers |
| **File Header** | 🟡 Yellow | `---/+++` | File names |

---

## Diff Format Explained

```
--- app.py (current)      ← Current version
+++ app.py (proposed)     ← Proposed version
@@ -5,7 +5,8 @@           ← Line numbers (from line 5, 7 lines → to line 5, 8 lines)
 def calculate():         ← Context (unchanged)
     x = 10              ← Context
     y = 20              ← Context
-    result = x + y + z  ← Removed line (red)
+    result = x + y      ← Added line (green)
+    # Bug fixed         ← Added line (green)
     return result       ← Context
```

---

## Workflow Example

### Scenario: Fixing a Bug

```
You: "There's a bug in calculator.py on line 15, fix it"

Agent: "🤔 **Thinking & Planning:**
- Task: Fix bug in calculator.py line 15
- Approach: Read file → Identify issue → Propose fix

Let me read the file..."

[Agent reads calculator.py]

Agent: "📋 **Analysis:**
Found the bug on line 15:
- Issue: Division by zero not handled
- Fix: Add zero check before division

I'll propose a fix..."

[Agent calls manage_file]

Terminal:
┌──────────────────────────────────────────────────┐
│ 📝 File Change Request  EDIT                     │
│ calculator.py                                    │
├──────────────────────────────────────────────────┤
│ --- calculator.py (current)                      │
│ +++ calculator.py (proposed)                     │
│ @@ -13,7 +13,10 @@                               │
│  def divide(a, b):                               │
│ -    return a / b                                │
│ +    if b == 0:                                  │
│ +        return "Error: Cannot divide by zero"   │
│ +    return a / b                                │
├──────────────────────────────────────────────────┤
│  [✓ Accept Changes]  [✗ Reject Changes]         │
└──────────────────────────────────────────────────┘

Agent: "📝 File edit proposed for calculator.py

I've added a zero check to prevent division by zero errors.
Please review the diff and accept or reject the changes."

[You review and click: ✓ Accept Changes]

Terminal: ✅ Changes applied to: calculator.py

Agent: "✅ Changes accepted! The bug has been fixed.
calculator.py now handles division by zero properly."
```

---

## Benefits

### For Users 👥
✅ See exactly what changes before they're applied
✅ Review code modifications
✅ Accept good changes, reject bad ones
✅ Full transparency and control
✅ Learn from agent's changes
✅ Prevent unwanted modifications

### For Development 💻
✅ Safe file modifications
✅ Easy to spot errors in proposed changes
✅ Clear audit trail of changes
✅ No surprise modifications
✅ Can reject and ask for different approach

---

## Technical Details

### Backend (Python)

**File:** `brain.py`
```python
@tool
def manage_file(path, content, action="write"):
    if action == "write":
        if file_exists:
            # Generate diff
            diff = difflib.unified_diff(
                old_content.splitlines(),
                new_content.splitlines(),
                fromfile=f"{path} (current)",
                tofile=f"{path} (proposed)"
            )
            
            # Store pending change
            change_id = store_pending_change(
                path, old_content, new_content, diff
            )
            
            # Broadcast to UI
            broadcast_file_change(change_id)
```

**File:** `utils.py`
```python
# Store pending changes
pending_changes = {}

def store_pending_change(path, old, new, diff):
    change_id = uuid4()
    pending_changes[change_id] = {
        "file_path": path,
        "old_content": old,
        "new_content": new,
        "diff": diff
    }
    return change_id

async def broadcast_file_change(change_id):
    # Send to all connected clients
    await ws.send_json({
        "type": "file_change",
        "change_id": change_id,
        "file_path": path,
        "diff": diff
    })
```

**File:** `server.py`
```python
@app.post("/approve-file-change")
async def approve_file_change(approval):
    if approval.approved:
        # Apply changes to file
        with open(file_path, "w") as f:
            f.write(new_content)
        return {"ok": True}
    else:
        # Discard changes
        return {"ok": True, "rejected": True}
```

### Frontend (TypeScript)

**File:** `extension.ts`
```typescript
socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'file_change') {
        showFileDiff(
            data.change_id,
            data.file_path,
            data.diff
        );
    }
};

function showFileDiff(changeId, path, diff) {
    // Create diff UI with colored lines
    // Add Accept/Reject buttons
    // Show in terminal
}

async function handleFileDiff(changeId, approved) {
    await fetch('/approve-file-change', {
        body: JSON.stringify({ change_id, approved })
    });
}
```

---

## Use Cases

### 1. Bug Fixes
```
You: "Fix the null pointer bug"
[Agent proposes fix]
[You review diff]
[Accept if correct, reject if wrong approach]
```

### 2. Refactoring
```
You: "Refactor the authentication function"
[Agent proposes refactored code]
[Review changes carefully]
[Accept if improvements are good]
```

### 3. Adding Features
```
You: "Add error handling to all API calls"
[Agent adds try-catch blocks]
[Review each change]
[Accept or ask for modifications]
```

### 4. Code Cleanup
```
You: "Remove unused imports and add comments"
[Agent proposes cleanup]
[Review removals to ensure nothing needed is deleted]
[Accept if clean]
```

---

## Keyboard & Mouse

### Buttons
- **✓ Accept Changes** - Green button, applies changes
- **✗ Reject Changes** - Red button, discards changes

### Workflow
1. Agent proposes change
2. Diff appears in terminal
3. Scroll to review if needed
4. Click button to decide
5. Change applied or rejected
6. Next diff appears (if multiple files)

---

## Edge Cases Handled

### No Changes Detected
```
Agent: "✅ No changes needed - file already has this content"
[No diff shown, file untouched]
```

### File Doesn't Exist (New File)
```
[Shows preview instead of diff]
[Badge: NEW FILE]
[Full content preview with first 500 chars]
```

### Multiple Pending Changes
```
[Each change gets unique ID]
[Can accept/reject independently]
[Changes applied in order of approval]
```

---

## Comparison

| Aspect | Before (v1.4) | After (v1.5) |
|--------|---------------|--------------|
| **Visibility** | ❌ None | ✅ Full diff |
| **Control** | ❌ Auto-applied | ✅ User approval |
| **Review** | ❌ After change | ✅ Before change |
| **Reject** | ❌ No option | ✅ Can reject |
| **Color coding** | ❌ No | ✅ Yes |
| **Transparency** | ❌ Low | ✅ High |

---

## Tips

### Tip 1: Review Carefully
Look at both additions (+) and deletions (-) to ensure nothing important is removed.

### Tip 2: Reject and Iterate
If the change isn't quite right, reject it and ask agent to try again with different approach.

### Tip 3: Multiple Files
Agent may propose changes to multiple files - review each one individually.

### Tip 4: Learn from Diffs
Study the diffs to learn how agent solves problems.

---

## Future Enhancements

Planned for v1.6:
- [ ] Side-by-side diff view
- [ ] Partial accept (accept some changes, reject others)
- [ ] Diff search/filter
- [ ] Export diff to file
- [ ] Undo applied changes
- [ ] Compare with git diff

---

## Summary

### What Changed?

**Files Modified:**
- `brain.py` - manage_file now generates diffs
- `utils.py` - Added pending changes storage
- `server.py` - Added approval endpoint
- `extension.ts` - Added diff UI display

**Result:**
- ✅ Beautiful diff display
- ✅ Accept/Reject buttons
- ✅ Full control over file changes
- ✅ No surprise modifications
- ✅ IDE-like experience

---

**Version:** 1.5  
**Date:** 2026-01-21  
**Status:** ✅ Production Ready

Your agent now shows you EXACTLY what it's changing! 📝✨

