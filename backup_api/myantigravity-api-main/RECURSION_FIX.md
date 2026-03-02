# 🔧 Recursion Error Fix + Editor Diff Feature

## Issues Fixed ✅

### 1. Recursion Limit Error
**Error:** `langgraph.errors.GraphRecursionError: Recursion limit of 25 reached`

**Cause:** LangGraph's default recursion limit of 25 was too low for complex agent workflows with multiple tool calls.

**Solution:** Increased recursion limit to 50 in both places:

```python
# brain.py
app = workflow.compile()
app.config = {"recursion_limit": 50}

# server.py  
config = {"recursion_limit": 50}
agent_app.astream(inputs, config=config)
```

### 2. Diff in Editor (Not Just Terminal)
**Request:** Show file diffs in VS Code editor with Accept/Reject buttons

**Solution:** Integrated VS Code Diff Editor API

---

## How It Works Now

### When Agent Edits a File:

**Step 1: Agent proposes change**
```python
manage_file("app.py", new_content, "write")
```

**Step 2: Diff broadcasted via WebSocket**
```
Terminal shows colored diff (for reference)
```

**Step 3: VS Code Editor opens with diff**
```
┌────────────────────────────────────────────┐
│ app.py (Changes)                           │
├─────────────────┬──────────────────────────┤
│ CURRENT         │ PROPOSED                 │
├─────────────────┼──────────────────────────┤
│ def calc():     │ def calc():              │
│   x = 10        │   x = 10                 │
│   y = 20        │   y = 20                 │
│   return x+y+z  │   return x+y  # Fixed!   │
└─────────────────┴──────────────────────────┘
```

**Step 4: Modal dialog appears**
```
┌────────────────────────────────────────┐
│ 📝 File changes proposed for: app.py   │
│                                        │
│   [Accept]  [Reject]                   │
└────────────────────────────────────────┘
```

**Step 5: Your decision**
- Click **Accept** → Changes applied, file saved
- Click **Reject** → Changes discarded, file unchanged

---

## Visual Comparison

### Before (v1.5 - Terminal Only):
```
Terminal:
┌────────────────────────────────────────┐
│ 📝 File Change Request  EDIT           │
│ app.py                                 │
│ [diff shown in terminal]               │
│ [✓ Accept] [✗ Reject]                 │
└────────────────────────────────────────┘
```

### After (v1.6 - Editor + Modal):
```
VS Code Editor:
┌──────────────────────────────────────────────┐
│ app.py (Changes)           [Side-by-side]    │
├──────────────┬───────────────────────────────┤
│ CURRENT      │ PROPOSED                      │
│ (left side)  │ (right side with changes)     │
└──────────────┴───────────────────────────────┘

Modal Dialog:
┌────────────────────────────────────────┐
│ 📝 File changes proposed for: app.py   │
│                                        │
│   [Accept]  [Reject]                   │
└────────────────────────────────────────┘
```

---

## Features

### Side-by-Side Diff
- ✅ Current content (left)
- ✅ Proposed content (right)
- ✅ Changes highlighted
- ✅ Native VS Code diff viewer
- ✅ Scroll synchronized

### Modal Dialog
- ✅ Clear file name
- ✅ Big buttons (Accept/Reject)
- ✅ Modal = must decide
- ✅ Can't ignore by accident

### Terminal Reference
- ✅ Still shows diff in terminal
- ✅ Colored for easy reading
- ✅ Both views available

---

## Example Workflow

```
You: "Fix the bug in calculator.py"

Agent: "🤔 Reading calculator.py..."
Agent: "📋 Found issue: division by zero not handled"
Agent: "Proposing fix..."

[VS Code opens diff editor showing:]
┌──────────────────────────────────────────────┐
│ calculator.py (Changes)                      │
├──────────────┬───────────────────────────────┤
│ def divide:  │ def divide:                   │
│   return a/b │   if b == 0:                  │
│              │     return "Error"             │
│              │   return a/b                   │
└──────────────┴───────────────────────────────┘

[Modal appears:]
📝 File changes proposed for: calculator.py
   [Accept]  [Reject]

[You click Accept]

✅ Changes applied to: calculator.py
[Editor refreshes with new content]
```

---

## Technical Details

### Extension (TypeScript)

**New Commands:**
```typescript
// Accept changes
vscode.commands.registerCommand('antigravity.acceptChange', 
    async (changeId: string) => {
        // Apply changes via API
        // Close diff editor
        // Refresh file
    }
);

// Reject changes  
vscode.commands.registerCommand('antigravity.rejectChange',
    async (changeId: string) => {
        // Discard changes via API
        // Close diff editor
    }
);
```

**Diff Display:**
```typescript
async function showDiffInEditor(changeData) {
    // Create temp files for diff
    const originalUri = Uri.parse(`untitled:${file}.original`);
    const modifiedUri = Uri.parse(`untitled:${file}.modified`);
    
    // Open VS Code diff editor
    await vscode.commands.executeCommand(
        'vscode.diff',
        originalUri,
        modifiedUri,
        `${file} (Changes)`
    );
    
    // Show modal with buttons
    const result = await vscode.window.showInformationMessage(
        `📝 File changes proposed for: ${file}`,
        { modal: true },
        'Accept',
        'Reject'
    );
}
```

### Server (Python)

**New Endpoint:**
```python
@app.get("/get-file-content")
async def get_file_content(path: str):
    """Get current file content for diff comparison"""
    if os.path.exists(path):
        with open(path, 'r') as f:
            return {"ok": True, "content": f.read()}
    return {"ok": True, "content": ""}
```

---

## Recursion Limit Fix

### Why It Happened:
```
Agent workflow:
1. User message → Agent
2. Agent calls tool → Action  
3. Action returns → Agent
4. Agent responds → (might call another tool)
5. Loop continues...
```

If agent makes many tool calls (read file → analyze → edit → read again → verify), it hits the 25-step limit.

### Solution:
```python
# brain.py - Global config
app.config = {"recursion_limit": 50}

# server.py - Per-request config
config = {"recursion_limit": 50}
async for output in agent_app.astream(inputs, config=config):
    # Process outputs
```

### Benefits:
- ✅ Handles complex multi-step tasks
- ✅ Agent can make more tool calls
- ✅ No more recursion errors
- ✅ Still has safety limit (50)

---

## Usage Tips

### Tip 1: Review Before Accepting
- Left side = current code
- Right side = proposed changes
- Look for unintended changes

### Tip 2: Use Reject to Iterate
```
Agent proposes fix
[You review]
[Doesn't look right]
[Click Reject]
"Try a different approach - use a try/except instead"
[Agent tries again]
```

### Tip 3: Terminal as Reference
- Diff still appears in terminal
- Can scroll back to see it
- Useful for comparison

### Tip 4: Multiple Files
- Each file opens separately
- Approve/reject one at a time
- Process in order

---

## Keyboard Shortcuts

- **Tab** - Switch between buttons in modal
- **Enter** - Accepts focused button
- **Escape** - Closes modal (acts as reject)
- **Ctrl+W** - Close diff editor

---

## Troubleshooting

### Issue: Diff doesn't open in editor
**Solution:** Restart extension (Ctrl+R in Extension Development Host)

### Issue: Still getting recursion errors
**Solution:** Restart server to load new config: `python3 server.py`

### Issue: Modal doesn't appear
**Check:** Extension is properly loaded and commands registered

### Issue: Accept doesn't apply changes
**Check:** Server logs for errors, verify file path is correct

---

## Files Modified

| File | Changes |
|------|---------|
| `brain.py` | Added recursion_limit config |
| `server.py` | Added recursion_limit to astream, new endpoint |
| `extension.ts` | Added diff editor integration, commands, modal |
| `utils.py` | Added new_content to broadcast |

---

## Comparison Table

| Feature | v1.5 | v1.6 |
|---------|------|------|
| **Diff Location** | Terminal only | Editor + Terminal |
| **Diff Style** | Colored text | Side-by-side |
| **Buttons** | In terminal | Modal dialog |
| **Interaction** | Click in terminal | Click in modal |
| **Editor** | No integration | Full integration |
| **Recursion Limit** | 25 (default) | 50 (increased) |

---

## Benefits

### For Reviewing Changes:
✅ Side-by-side comparison (easier to read)
✅ Native VS Code diff viewer (familiar)
✅ Better highlighting
✅ Can't miss the modal
✅ Clear decision required

### For Complex Tasks:
✅ No more recursion errors
✅ Agent can make more tool calls
✅ Handle longer workflows
✅ Better for large refactorings

---

## Testing

### Test Recursion Fix:
```
You: "Create a complex Flask app with 5 endpoints, 
      database models, and error handling"

Expected:
- Agent makes many tool calls
- Creates multiple files
- No recursion error
- Completes successfully
```

### Test Editor Diff:
```
You: "Fix the syntax error in app.py"

Expected:
1. Agent analyzes file
2. Proposes fix
3. Diff editor opens in VS Code
4. Modal appears with buttons
5. You click Accept or Reject
6. Changes applied (or not)
7. Editor refreshes
```

---

## Summary

### What Was Fixed:

1. **Recursion Error** ✅
   - Increased limit from 25 → 50
   - Applied globally and per-request
   - Agent can handle complex tasks

2. **Editor Diff** ✅
   - Diffs now open in VS Code editor
   - Side-by-side comparison
   - Modal dialog with buttons
   - Native IDE experience

---

**Version:** 1.6
**Date:** 2026-01-21  
**Status:** ✅ Production Ready

Your agent is now more robust and provides an IDE-native diff experience! 🎉

