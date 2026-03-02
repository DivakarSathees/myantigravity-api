# Slash Commands - Quick Start Guide

## What is it?

A powerful feature that lets you quickly access AI prompt templates by typing `/` in the chat input.

## How to Use

### Step 1: Type `/`
In the chat input box, simply type the forward slash character: `/`

### Step 2: Browse Commands
A dropdown menu appears showing all available commands:

```
┌─────────────────────────────────────────────────────┐
│ 💡 Quick Commands                                   │
├─────────────────────────────────────────────────────┤
│ 📝 Generate Description                             │
│    Create a scenario-based problem description      │
│    for this project                                 │
├─────────────────────────────────────────────────────┤
│ 🔍 Code Review                                      │
│    Perform a comprehensive code review              │
├─────────────────────────────────────────────────────┤
│ 🧪 Generate Tests                                   │
│    Create unit tests for the project                │
├─────────────────────────────────────────────────────┤
│ ♻️ Refactor Code                                    │
│    Suggest and apply code refactoring               │
├─────────────────────────────────────────────────────┤
│ 📚 Add Documentation                                │
│    Generate comprehensive documentation             │
├─────────────────────────────────────────────────────┤
│ 🔒 Security Audit                                   │
│    Check for security vulnerabilities               │
├─────────────────────────────────────────────────────┤
│ ⚡ Optimize Performance                             │
│    Identify and fix performance bottlenecks         │
├─────────────────────────────────────────────────────┤
│ 🌐 Generate API Docs                                │
│    Create API documentation                         │
└─────────────────────────────────────────────────────┘
```

### Step 3: Select a Command

**Using Keyboard:**
- Press `↑` or `↓` arrow keys to navigate
- Press `Enter` to select
- Press `Escape` to cancel

**Using Mouse:**
- Click on any command to select it

### Step 4: Directory Selection (if needed)

Some commands (like "Generate Description") will ask you to select a directory:
1. VS Code's folder picker opens
2. Navigate to the desired folder
3. Click "Select Directory"
4. The prompt is automatically updated with the directory path

### Step 5: Send the Command

Press `Enter` to send the command to the AI agent!

## Example Workflows

### Example 1: Generate Project Description

**Goal:** Create a detailed problem description for your project

1. Type `/` in chat
2. Select "📝 Generate Description" (first option)
3. Folder picker opens
4. Select where to save the description (e.g., `/docs` folder)
5. Input shows: "Create a detailed scenario-based problem description... Save the file in: /path/to/docs"
6. Press Enter
7. AI analyzes your project and creates `description.md`

**Result:** A comprehensive markdown file with:
- Problem statement
- User stories
- Technical requirements
- Acceptance criteria

---

### Example 2: Security Audit

**Goal:** Check your code for security vulnerabilities

1. Type `/` in chat
2. Navigate to "🔒 Security Audit" (6th option)
3. Press Enter
4. Prompt is inserted: "Perform a security audit of this project..."
5. Press Enter again to send
6. AI scans your code for vulnerabilities

**Result:** A `security_audit.md` file with:
- Common vulnerabilities found (SQL injection, XSS, CSRF, etc.)
- Insecure dependencies
- Hardcoded secrets
- Recommendations

---

### Example 3: Generate Tests

**Goal:** Create unit tests for your code

1. Type `/` in chat
2. Select "🧪 Generate Tests" (3rd option)
3. Press Enter
4. AI analyzes your code
5. Generates comprehensive unit tests

**Result:** Test files created with:
- Test cases for all functions
- Edge cases covered
- Following your project's testing framework

## Tips & Tricks

### 💡 Tip 1: Quick Navigation
The first command is selected by default. Just press Enter to use it!

### 💡 Tip 2: Combine with File Mentions
You can use both features together:
1. Type `@` to attach specific files
2. Then type `/` to select a command
3. The AI will focus on the mentioned files

### 💡 Tip 3: Escape to Cancel
Press `Escape` at any time to close the command picker without selecting anything.

### 💡 Tip 4: Click Outside to Close
Click anywhere outside the dropdown to close it.

## Keyboard Shortcuts Summary

| Key | Action |
|-----|--------|
| `/` | Open command picker |
| `@` | Open file picker |
| `↑` | Navigate up |
| `↓` | Navigate down |
| `Enter` | Select command |
| `Escape` | Close picker |

## All Available Commands

| Icon | Command | What it does | Directory? |
|------|---------|--------------|------------|
| 📝 | Generate Description | Creates project description | ✅ Yes |
| 🔍 | Code Review | Reviews code quality | ❌ No |
| 🧪 | Generate Tests | Creates unit tests | ❌ No |
| ♻️ | Refactor Code | Suggests refactoring | ❌ No |
| 📚 | Add Documentation | Generates docs | ❌ No |
| 🔒 | Security Audit | Checks security | ❌ No |
| ⚡ | Optimize Performance | Improves performance | ❌ No |
| 🌐 | Generate API Docs | Creates API docs | ❌ No |

## Troubleshooting

### Command picker not showing?
- Make sure you're typing `/` at the beginning or after a space
- Check that the extension is properly loaded

### Directory picker not opening?
- This only happens for "Generate Description" command
- Other commands insert the prompt directly

### Can't select a command?
- Try clicking directly on the command
- Or use arrow keys + Enter

## Need Help?

If you encounter any issues:
1. Check the console for errors (Help > Toggle Developer Tools)
2. Restart VS Code
3. Reload the extension window

---

**Happy Coding! 🚀**

*Version 1.0 - 2026-01-28*
