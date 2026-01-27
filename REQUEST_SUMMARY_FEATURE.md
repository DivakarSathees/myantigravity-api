# Automatic Request Summary Feature

## Overview

The system now automatically creates a **markdown summary file** for each chat request. This file documents:
- The user's request
- The agent's response
- All files that were created or modified
- All commands that were executed
- Exit codes and timestamps

## How It Works

### 1. **Session Tracking**
- Each chat session has a unique `session_id`
- The system tracks all activities during that session:
  - File changes (created/modified)
  - Commands executed (with exit codes)

### 2. **Automatic Generation**
- At the end of each chat request, a markdown file is automatically created
- The file is saved in the `.antigravity_logs/` directory within your workspace
- Filename format: `YYYYMMDD_HHMMSS_<request_summary>.md`

### 3. **File Location**
```
<workspace>/.antigravity_logs/
├── 20260127_235500_create_calculator_app.md
├── 20260127_235830_fix_bug_in_main_py.md
└── 20260128_000100_add_new_feature.md
```

## Markdown File Structure

Each summary file contains:

### Header
- Date and time of the request
- Session ID

### User Request Section
- The exact message sent by the user

### Agent Response Section
- The complete response from the agent

### Files Changed Section
- List of all files created or modified
- Action type (CREATED, MODIFIED)
- File paths

### Commands Executed Section
- All terminal commands run
- Exit codes for each command
- Numbered list for easy reference

### Summary Section
- Quick statistics:
  - Number of files modified
  - Number of commands run
  - Session identifier

## Example Output

See `example_request_summary.md` for a complete example.

## Benefits

✅ **Complete Audit Trail** - Know exactly what changed in each request  
✅ **Easy Review** - Quickly see what the agent did  
✅ **Documentation** - Automatic documentation of your development process  
✅ **Debugging** - Track down when specific changes were made  
✅ **Learning** - Review past interactions to understand the agent's approach  

## Technical Implementation

### Files Modified

1. **server.py**
   - Added `session_activities` dictionary to track activities
   - Added `create_request_summary_markdown()` function
   - Added `track_file_change()` and `track_command()` functions
   - Added `get_current_session_id()` for brain.py to access
   - Modified `/chat` endpoint to generate summary after each request

2. **brain.py**
   - Modified `execute_terminal()` to track command executions
   - Modified `manage_file()` to track file changes (both create and modify)
   - Imports tracking functions from server.py

### Data Flow

```
User Request
    ↓
Chat Endpoint (server.py)
    ↓
Set current_session_id
    ↓
Agent Processing (brain.py)
    ↓
Tools Execute:
    - execute_terminal() → track_command()
    - manage_file() → track_file_change()
    ↓
Chat Endpoint Completes
    ↓
create_request_summary_markdown()
    ↓
Markdown File Saved
```

## Configuration

The feature is **enabled by default** and requires no configuration.

### Customization Options

You can modify the markdown template in `create_request_summary_markdown()` function in `server.py` to:
- Change the format
- Add more sections
- Include additional metadata
- Change the file naming convention

## Notes

- The `.antigravity_logs/` directory is automatically created if it doesn't exist
- Files are named with timestamps to avoid conflicts
- The system gracefully handles errors - if summary generation fails, it won't affect the chat request
- Tracking is session-specific - each session gets its own summary files

## Future Enhancements

Potential improvements:
- [ ] Add diff previews in the markdown
- [ ] Include screenshots or output samples
- [ ] Generate a session index file
- [ ] Export summaries in different formats (PDF, HTML)
- [ ] Add search functionality across all summaries
- [ ] Include performance metrics (execution time, etc.)
