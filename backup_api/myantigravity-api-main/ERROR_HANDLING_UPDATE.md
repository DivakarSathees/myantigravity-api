# 🔧 Error Handling & Auto-Fix Update - v1.3

## What's New?

Two major improvements to make the agent smarter and more helpful:

### ✅ 1. Better Command Output Display
- Shows both stdout AND stderr
- Displays actual output from commands
- Exit codes tracked
- Clear error messages

### ✅ 2. Intelligent Error Handling & Auto-Fix
- Agent analyzes errors automatically
- Fixes code errors and asks to rerun
- Suggests missing dependencies
- Provides helpful next steps

---

## Problem #1: Missing Command Output

### Before (v1.2):
```
agent@antigravity:~$ python3 app.py
✅ Command completed: python3 app.py

Agent: "The script has been run. No output was produced."
```

**Issue:** You couldn't see what the script actually printed!

### After (v1.3):
```
agent@antigravity:~$ python3 app.py
  Hello, World!
  Prime numbers: 2, 3, 5, 7, 11, 13
  Calculation complete: 42
✅ Command completed successfully: python3 app.py

Agent: "Command executed successfully.
Output:
Hello, World!
Prime numbers: 2, 3, 5, 7, 11, 13
Calculation complete: 42"
```

**Fixed:** All command output is captured and displayed!

---

## Problem #2: No Error Recovery

### Before (v1.2):
```
You: "Run app.py"
Agent: [Runs it]
  ❌ NameError: name 'x' is not defined
Agent: "The command failed."
[Dead end - you have to manually fix it]
```

### After (v1.3):
```
You: "Run app.py"
Agent: "I need to run: `python3 app.py`. Should I proceed? (yes/no)"
You: [Click ✓ Yes]

agent@antigravity:~$ python3 app.py
  ❌ NameError: name 'x' is not defined
  ❌ File "app.py", line 5
❌ Command failed with exit code 1: python3 app.py

Agent: "The script has a NameError on line 5: variable 'x' is not defined.

I can see the issue - the variable needs to be initialized. I'll fix it:

[Agent fixes the code using manage_file]

✅ Fixed the error in app.py. Should I rerun: `python3 app.py`? (yes/no)"

You: [Click ✓ Yes]

agent@antigravity:~$ python3 app.py
  Result: 42
✅ Command completed successfully: python3 app.py

Agent: "Perfect! The script now runs successfully and outputs: 42"
```

**Fixed:** Agent automatically diagnoses and fixes errors!

---

## How It Works

### 1. Enhanced Command Execution

The `execute_terminal` tool now:
- Captures **both stdout and stderr**
- Tracks **exit codes** (0 = success, non-zero = error)
- Returns detailed error information
- Shows all output in real-time

**Technical Details:**
```python
# Reads stdout and stderr simultaneously
stdout_lines = []  # Normal output
stderr_lines = []  # Error messages
exit_code = process.returncode  # 0 = success

if exit_code == 0:
    return "Success + output"
else:
    return "Failed with errors"
```

---

### 2. Intelligent Error Analysis

The agent's system prompt now includes:

```
ERROR HANDLING:
- If a command fails, ANALYZE the error
- Determine the root cause
- If it's a code error you can fix:
  1. Explain the error briefly
  2. Fix the code using manage_file
  3. Ask to rerun: "Should I rerun: `command`? (yes/no)"
- If it's a missing dependency:
  1. Tell user what's missing
  2. Ask to install: "Should I run: `pip install package`? (yes/no)"
```

---

## Example Scenarios

### Scenario 1: Syntax Error

```
You: "Run calculator.py"

Agent: "I need to run: `python3 calculator.py`. Should I proceed? (yes/no)"
[Click ✓ Yes]

agent@antigravity:~$ python3 calculator.py
  ❌ SyntaxError: invalid syntax
  ❌ File "calculator.py", line 10
  ❌     print("Result" 42)
  ❌                   ^
❌ Command failed with exit code 1

Agent: "There's a syntax error on line 10 - missing comma in the print statement.

I'll fix it:
[Fixes: print("Result", 42)]

✅ Fixed! Should I rerun: `python3 calculator.py`? (yes/no)"

[Click ✓ Yes]

agent@antigravity:~$ python3 calculator.py
  Result: 42
✅ Command completed successfully
```

---

### Scenario 2: Missing Module

```
You: "Run web_scraper.py"

Agent: "I need to run: `python3 web_scraper.py`. Should I proceed? (yes/no)"
[Click ✓ Yes]

agent@antigravity:~$ python3 web_scraper.py
  ❌ ModuleNotFoundError: No module named 'requests'
❌ Command failed with exit code 1

Agent: "The script requires the 'requests' module which isn't installed.

Should I install it: `pip install requests`? (yes/no)"

[Click ✓ Yes]

agent@antigravity:~$ pip install requests
  Collecting requests...
  Successfully installed requests-2.31.0
✅ Command completed successfully

Agent: "Great! Now should I rerun: `python3 web_scraper.py`? (yes/no)"

[Click ✓ Yes]

agent@antigravity:~$ python3 web_scraper.py
  Fetching data...
  Success! Data saved to output.json
✅ Command completed successfully
```

---

### Scenario 3: File Not Found

```
You: "Run app.py"

Agent: "I need to run: `python3 app.py`. Should I proceed? (yes/no)"
[Click ✓ Yes]

agent@antigravity:~$ python3 app.py
  ❌ python3: can't open file 'app.py': [Errno 2] No such file or directory
❌ Command failed with exit code 2

Agent: "The file 'app.py' doesn't exist in the current directory.

Let me search for it:
[Calls find_file('app.py')]

Found it at: ./myproject/app.py

Should I run: `python3 ./myproject/app.py`? (yes/no)"
```

---

### Scenario 4: Logic Error with Output

```
You: "Run test.py"

Agent: "I need to run: `python3 test.py`. Should I proceed? (yes/no)"
[Click ✓ Yes]

agent@antigravity:~$ python3 test.py
  Testing function add(2, 2)...
  Expected: 4
  Got: 22
  ❌ Test failed!
✅ Command completed successfully (exit code 0)

Agent: "The script ran successfully but the test failed. Looking at the output, 
it seems add(2, 2) returned 22 instead of 4.

This is likely a string concatenation issue. Let me check the code:
[Reads test.py]

I found it! The function is concatenating strings instead of adding numbers.
Line 5: return a + b  # Should convert to int first

I'll fix it:
[Updates code to: return int(a) + int(b)]

✅ Fixed! Should I rerun: `python3 test.py`? (yes/no)"
```

---

## Key Features

### 1. Complete Output Capture ✅
```python
# Before: Only saw "Command completed"
# After: See actual output
  Hello, World!
  Processing data...
  Result: 42
```

### 2. Error Details ❌
```python
# Exit code tracking
exit_code = 1  # Non-zero = error

# Stderr capture
  ❌ NameError: name 'x' is not defined
  ❌ File "app.py", line 5
```

### 3. Smart Error Analysis 🧠
```
Agent analyzes:
- SyntaxError → Finds the line, fixes syntax
- ModuleNotFoundError → Offers to install
- NameError → Checks if variable should exist
- FileNotFoundError → Searches for the file
```

### 4. Auto-Fix Workflow 🔧
```
1. Run command
2. Error occurs
3. Agent analyzes error
4. Agent fixes the issue
5. Agent asks: "Should I rerun?"
6. User approves
7. Command succeeds!
```

---

## Technical Implementation

### Enhanced execute_terminal Tool

```python
@tool
async def execute_terminal(command: str):
    """Executes command and captures stdout/stderr"""
    
    # Run command
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    # Capture both outputs simultaneously
    stdout_lines = []
    stderr_lines = []
    
    async def read_stdout():
        # Capture and display stdout
        
    async def read_stderr():
        # Capture and display stderr (with ❌ prefix)
    
    await asyncio.gather(read_stdout(), read_stderr())
    
    # Check exit code
    exit_code = process.returncode
    
    if exit_code == 0:
        return "Success + output"
    else:
        return "Failed + errors + output"
```

### Improved System Prompt

```
CRITICAL WORKFLOW:
1. Ask permission FIRST
2. Wait for "yes"
3. THEN call execute_terminal
4. IF error → Analyze and fix
5. Ask to rerun

ERROR HANDLING:
- Code error → Fix with manage_file → Ask to rerun
- Missing dependency → Offer to install → Rerun
- File not found → Search for it → Ask with correct path
```

---

## Benefits

### For Users 👥
✅ See actual command output
✅ Automatic error diagnosis
✅ Automatic code fixes
✅ Fewer manual interventions
✅ Faster development cycle

### For Development 💻
✅ Less debugging time
✅ Agent handles common errors
✅ Clear error messages
✅ Iterative fixing process
✅ Learn from agent's fixes

---

## Comparison

| Aspect | Before (v1.2) | After (v1.3) |
|--------|---------------|--------------|
| **Output** | Not shown | Fully captured ✓ |
| **Stderr** | Not captured | Shown with ❌ ✓ |
| **Exit codes** | Ignored | Tracked ✓ |
| **Error analysis** | None | Automatic ✓ |
| **Auto-fix** | No | Yes ✓ |
| **Rerun suggestion** | Manual | Automatic ✓ |

---

## Testing

### Test 1: Output Display
```bash
# Create test script
echo 'print("Hello, World!")' > test.py

# In agent:
"Run test.py"
[Click Yes]

# Expected: See "Hello, World!" in terminal
```

### Test 2: Error & Fix
```bash
# Create buggy script
echo 'print("Test" 42)' > bug.py  # Missing comma

# In agent:
"Run bug.py"
[Click Yes]

# Expected:
# - See syntax error
# - Agent offers to fix
# - After fix, asks to rerun
```

### Test 3: Missing Module
```bash
# Create script with missing import
echo 'import nonexistent_module' > missing.py

# In agent:
"Run missing.py"
[Click Yes]

# Expected:
# - See ModuleNotFoundError
# - Agent explains the issue
```

---

## Configuration

### Adjust Error Handling Verbosity

In `brain.py`, modify the system prompt:

```python
# For detailed explanations:
"Explain errors in detail with code examples"

# For brief responses:
"Explain errors briefly and fix quickly"

# For no auto-fix:
"Report errors but don't fix automatically"
```

---

## Troubleshooting

### Issue: Output not showing
**Check:** Server logs for errors in async functions

### Issue: Agent doesn't offer to fix
**Check:** System prompt is properly injected in call_model

### Issue: Stderr not displayed
**Check:** Red ❌ lines in terminal output

---

## Future Enhancements

Planned for v1.4:
- [ ] Multi-step error resolution
- [ ] Learn from previous fixes
- [ ] Suggest code improvements
- [ ] Unit test generation after fixes
- [ ] Rollback if fix doesn't work

---

## Summary

### What Changed?

**File:** `brain.py`
- ✅ Enhanced `execute_terminal` to capture stdout/stderr
- ✅ Added exit code tracking
- ✅ Improved error messages
- ✅ Updated system prompt for error handling
- ✅ Enhanced `manage_file` with better error handling

**Result:**
- ✅ See actual command output
- ✅ Get detailed error information
- ✅ Automatic error diagnosis and fixing
- ✅ Smarter, more helpful agent

---

**Version:** 1.3  
**Date:** 2026-01-21  
**Status:** ✅ Ready to Use

Your agent is now smarter and more helpful! 🎉

