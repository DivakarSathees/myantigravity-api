# 📖 Usage Examples

Real-world examples of using MyAntigravity with the new features.

---

## Example 1: Multi-Turn Conversation with Memory 💭

### Scenario: Building a Python Project

```
You: "Create a Python file called calculator.py with add and subtract functions"

Agent: "I'll create that file for you."
[Agent creates the file]

You: "Now add multiply and divide functions to it"

Agent: "I'll add those functions to calculator.py"  ← Remembers the file!
[Agent modifies the file]

You: "Can you show me what's in the file now?"

Agent: "Here's the content of calculator.py..."  ← Still remembers!
[Agent reads and shows the file]

You: "Run it with a test"

Agent: "I'll create a test for calculator.py and run it"  ← Context maintained!
[Agent creates test and executes]
```

**Key Point:** The agent remembers "calculator.py" throughout the conversation without you having to repeat the filename!

---

## Example 2: Command Confirmation for Safety ⚠️

### Scenario: Listing Files

```
You: "Show me all Python files in this directory"

Agent ⚠️: "I need to run this command: `find . -name "*.py"`
Should I proceed? (yes/no)"

Terminal Output:
  ⚠️ Agent is requesting confirmation

You: "yes"

Agent: "Running the command now..."

Terminal Output:
  ⚠️ Command to execute: find . -name "*.py"
  💡 Awaiting user confirmation...
  ▶️ Executing: find . -name "*.py"
  ./brain.py
  ./server.py
  ./utils.py
  ✅ Command completed: find . -name "*.py"

Agent: "Found 3 Python files: brain.py, server.py, and utils.py"
```

---

## Example 3: Refusing Dangerous Commands 🛑

### Scenario: Preventing Accidental Deletion

```
You: "Delete all files in the temp directory"

Agent ⚠️: "I need to run this command: `rm -rf /tmp/*`
⚠️ WARNING: This will permanently delete files.
Should I proceed? (yes/no)"

Terminal Output:
  ⚠️ Agent is requesting confirmation
  ⚠️ Command to execute: rm -rf /tmp/*

You: "no, wait, I meant a different directory"

Agent: "Understood, I won't execute that command. Which directory did you mean?"

You: "The ./temp directory in the current project"

Agent ⚠️: "Got it. I need to run: `rm -rf ./temp/*`
Should I proceed? (yes/no)"

You: "yes"

Agent: "Executing now..."
[Command runs safely]
```

**Key Point:** The confirmation prompt saved you from accidentally deleting system files!

---

## Example 4: Building a Web App from Scratch 🌐

### Scenario: Creating a Flask Application

```
You: "Let's build a simple Flask web app"

Agent: "I'll help you create a Flask app. What should it do?"

You: "Create a hello world endpoint"

Agent: "I'll create a Flask app with a /hello endpoint. First, let me create the file."
[Agent creates app.py]

Agent: "File created. Now should I install Flask?"

You: "yes"

Agent ⚠️: "I need to run: `pip install flask`
Should I proceed? (yes/no)"

You: "yes"

Terminal Output:
  ▶️ Executing: pip install flask
  Collecting flask...
  Successfully installed flask

Agent: "Flask installed! Want me to run the app?"

You: "yes"

Agent ⚠️: "I'll run: `python app.py`
Should I proceed? (yes/no)"

You: "yes"

Terminal Output:
  ▶️ Executing: python app.py
  * Running on http://127.0.0.1:5000
  
Agent: "Your Flask app is now running on http://127.0.0.1:5000/hello"
```

**Key Point:** Multi-turn conversation with context awareness and safety confirmations!

---

## Example 5: Debugging with Context 🐛

### Scenario: Finding and Fixing a Bug

```
You: "I have a bug in my Python script"

Agent: "I'll help you debug it. Which script?"

You: "test.py"

Agent: "Let me read test.py to see what's there."
[Agent reads the file]

Agent: "I see the script. What's the issue you're experiencing?"

You: "It's not printing the output"

Agent: "I found the issue - there's no print statement. Should I add one?"

You: "yes, print the result variable"

Agent: "I'll add `print(result)` to test.py"
[Agent modifies file]

Agent: "Fixed! Want me to run it to verify?"

You: "yes"

Agent ⚠️: "I'll run: `python test.py`
Should I proceed? (yes/no)"

You: "yes"

Terminal Output:
  ▶️ Executing: python test.py
  42  ← Output appears!
  ✅ Command completed

Agent: "The script now works and outputs: 42"
```

**Key Point:** Agent remembers which file you're working on and maintains context throughout debugging!

---

## Example 6: Project Setup with Dependencies 📦

### Scenario: Setting Up a New Project

```
You: "Set up a new Python project for data analysis"

Agent: "I'll create a project structure for you. What should we call it?"

You: "data_analyzer"

Agent: "Creating directory structure for data_analyzer..."
[Agent creates directories]

Agent: "Created the following structure:
- data_analyzer/
  - src/
  - tests/
  - data/
  
Should I create a requirements.txt file?"

You: "yes, include pandas, numpy, and matplotlib"

Agent: "I'll create requirements.txt with those packages."
[Agent creates file]

Agent: "Requirements file created. Want me to set up a virtual environment and install dependencies?"

You: "yes"

Agent ⚠️: "I need to run these commands:
1. `python -m venv venv`
2. `source venv/bin/activate`
3. `pip install -r requirements.txt`

Should I proceed? (yes/no)"

You: "yes"

Terminal Output:
  ▶️ Executing: python -m venv venv
  ✅ Command completed
  ▶️ Executing: source venv/bin/activate
  ✅ Command completed
  ▶️ Executing: pip install -r requirements.txt
  Collecting pandas...
  Successfully installed pandas numpy matplotlib

Agent: "Your data_analyzer project is ready! Virtual environment is active and dependencies are installed."
```

**Key Point:** Complex multi-step workflow with context maintained throughout!

---

## Example 7: Using Clear History 🗑️

### Scenario: Starting Fresh

```
[Previous conversation about web development]

You: "Let's work on something different now"

Agent: "Sure, what would you like to work on?"

You: [Click "Clear History" button]

Terminal Output:
  🗑️ Chat history cleared
  
You: "Create a machine learning script"

Agent: "I'll help you create a machine learning script. What should it do?"
[Agent doesn't remember the previous web development conversation]
```

**Key Point:** Clear History lets you start fresh without confusing context!

---

## Example 8: Quick Commands (No Confirmation Needed) ⚡

### Scenario: Safe File Operations

```
You: "Create a file called notes.txt with 'Hello World'"

Agent: "I'll create that file for you."
[Agent creates file immediately - no confirmation needed]
✅ File created successfully

You: "Read the file back to me"

Agent: "The content of notes.txt is: Hello World"
[Agent reads immediately - no confirmation needed]

You: "Now run ls to see all files"

Agent ⚠️: "I need to run: `ls`
Should I proceed? (yes/no)"
[Terminal commands still need confirmation]
```

**Key Point:** File operations (read/write) don't need confirmation, but terminal commands do!

---

## Tips for Best Results 💡

### 1. Be Conversational
```
✅ Good: "Create a Python file"
✅ Good: "Now add a function to it"
✅ Good: "Run the file"

The agent will understand the context!
```

### 2. Use Clear Confirmations
```
✅ Good: "yes"
✅ Good: "ok"
✅ Good: "proceed"
✅ Good: "go ahead"

❌ Avoid: "maybe", "I think so", "sure" (ambiguous)
```

### 3. Reference Previous Work
```
✅ Good: "Now modify that file"
✅ Good: "Add another function to it"
✅ Good: "What was in that file again?"

The agent remembers!
```

### 4. Clear History When Switching Topics
```
✅ Good: Click "Clear History" when starting a completely new project
✅ Good: Keeps context focused and relevant
```

### 5. Review Commands Before Confirming
```
✅ Good: Read the command the agent shows you
✅ Good: Say "no" if it's not what you want
✅ Good: Clarify and ask again

Safety first!
```

---

## Common Patterns

### Pattern: Iterative Development
```
1. "Create a basic version"
2. Agent creates ✓
3. "Add feature X"
4. Agent modifies ✓
5. "Add feature Y"
6. Agent modifies ✓
7. "Test it"
8. Agent runs ✓
9. "Fix the bug in line 5"
10. Agent fixes ✓
```

### Pattern: Exploration
```
1. "What Python files are in this project?"
2. Agent lists them ✓
3. "Show me what's in brain.py"
4. Agent reads it ✓
5. "Explain how the agent works"
6. Agent explains based on the code ✓
```

### Pattern: Safe Experimentation
```
1. "Can you show me what command would delete all .pyc files?"
2. Agent shows: `find . -name "*.pyc" -delete`
3. "Is that safe?"
4. Agent explains what it does
5. "Ok, go ahead"
6. Agent asks for confirmation ⚠️
7. "yes"
8. Agent executes ✓
```

---

## Advanced Usage

### Using Session IDs Programmatically

If you want to interact with the API directly:

```bash
# Start a conversation
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
# Response includes: {"response": "...", "session_id": "abc123"}

# Continue the conversation
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What did I just say?", "session_id": "abc123"}'
# Agent remembers: "You said Hello"

# Clear history
curl -X POST http://localhost:8000/clear-history \
  -H "Content-Type: application/json" \
  -d '{"session_id": "abc123"}'
```

---

## Troubleshooting Examples

### Issue: Agent Doesn't Remember

```
Problem: You said "Now modify it" but agent asks "Modify what?"

Solution:
1. Check terminal for "📝 Chat session started"
2. If not there, click "Clear History" and start fresh
3. Be more explicit: "Now modify calculator.py"
```

### Issue: Agent Executes Without Asking

```
Problem: Agent ran a command without confirmation

Possible Reasons:
1. It was a safe file operation (create/read)
2. System prompt might be missing
3. You said "yes" in a previous message

Solution:
- Terminal commands ALWAYS need confirmation
- If not happening, restart the server
```

---

**Happy Coding with MyAntigravity! 🚀**

For more information:
- [NEW_FEATURES.md](NEW_FEATURES.md) - Feature documentation
- [QUICKSTART.md](QUICKSTART.md) - Getting started
- [README.md](README.md) - Complete reference

