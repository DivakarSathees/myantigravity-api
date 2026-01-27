# Slash Commands Feature Documentation

## Overview

The VS Code extension now supports **slash commands** (`/`) in addition to file mentions (`@`). When you type `/` in the chat input, a dropdown appears with predefined prompt templates for common development tasks.

## How to Use

1. **Open the chat input** in the Antigravity extension
2. **Type `/`** to trigger the command picker
3. **Browse commands** using:
   - Mouse: Click on any command
   - Keyboard: Use ↑/↓ arrow keys to navigate, Enter to select
4. **Select a command** - the prompt template will be inserted into the input
5. **Send the message** to execute the command

## Available Commands

### 📝 Generate Description
**Purpose:** Create a scenario-based problem description for the project

**What it does:**
- Analyzes project files and structure
- Creates a detailed problem description
- Includes: problem statement, user stories, technical requirements, acceptance criteria
- Saves as a markdown file in the project directory

### 🔍 Code Review
**Purpose:** Perform a comprehensive code review

**What it does:**
- Analyzes code quality across the project
- Identifies potential bugs and code smells
- Suggests improvements and best practices
- Creates a `code_review.md` file with findings

### 🧪 Generate Tests
**Purpose:** Create unit tests for the project

**What it does:**
- Analyzes existing code
- Generates comprehensive unit tests
- Follows project's testing framework conventions
- Includes edge cases and aims for good coverage

### ♻️ Refactor Code
**Purpose:** Suggest and apply code refactoring

**What it does:**
- Identifies refactoring opportunities
- Improves code readability and reduces complexity
- Removes code duplication
- Follows SOLID principles
- Explains all changes made

### 📚 Add Documentation
**Purpose:** Generate comprehensive documentation

**What it does:**
- Creates README.md with setup instructions
- Generates API documentation
- Adds code comments where needed
- Includes usage examples
- Makes documentation beginner-friendly

### 🔒 Security Audit
**Purpose:** Check for security vulnerabilities

**What it does:**
- Scans for common vulnerabilities (SQL injection, XSS, CSRF, etc.)
- Checks for insecure dependencies
- Identifies hardcoded secrets
- Creates a `security_audit.md` report

### ⚡ Optimize Performance
**Purpose:** Identify and fix performance bottlenecks

**What it does:**
- Analyzes code for performance issues
- Identifies inefficient algorithms
- Checks for unnecessary computations and memory leaks
- Provides specific optimization recommendations
- Implements improvements

### 🌐 Generate API Docs
**Purpose:** Create API documentation

**What it does:**
- Documents all API endpoints
- Includes request/response examples
- Describes parameters and error codes
- Adds authentication details
- Can generate OpenAPI/Swagger format

## Features

### Smart Input Detection
- Type `@` to mention files
- Type `/` to use commands
- Both pickers can't be open simultaneously
- Automatically switches between them

### Keyboard Navigation
- **↑/↓ Arrow Keys:** Navigate through commands
- **Enter:** Select highlighted command
- **Escape:** Close the command picker
- **Mouse Click:** Select any command directly

### Visual Feedback
- Highlighted selection shows current command
- Icons for easy identification
- Descriptions explain what each command does
- Smooth animations and transitions

## Technical Implementation

### Files Modified
1. **extension.ts**
   - Added CSS styles for command picker
   - Added HTML structure for command dropdown
   - Added JavaScript functions for command handling
   - Updated input handlers to detect `/` character

### Key Components

#### CSS Classes
- `.command-picker-dropdown` - Main dropdown container
- `.command-item` - Individual command item
- `.command-item-title` - Command title with icon
- `.command-item-description` - Command description text

#### JavaScript Variables
```javascript
const COMMAND_TEMPLATES = [...];  // Array of command objects
let commandPickerVisible = false;  // Visibility state
let selectedCommandIndex = -1;     // Current selection
let filteredCommands = [];         // Filtered command list
```

#### Key Functions
- `showCommandPicker()` - Display the command dropdown
- `hideCommandPicker()` - Hide the command dropdown
- `renderCommandList()` - Render commands in the dropdown
- `selectCommand(commandId)` - Insert selected command prompt
- `updateCommandSelection()` - Update visual selection

### Command Template Structure
```javascript
{
    id: 'command-id',              // Unique identifier
    icon: '📝',                     // Display icon
    title: 'Command Title',         // Display title
    description: 'What it does',    // Short description
    prompt: 'Full prompt text...'   // Template to insert
}
```

## Customization

### Adding New Commands

To add a new command, add an object to the `COMMAND_TEMPLATES` array:

```javascript
{
    id: 'my-custom-command',
    icon: '🎯',
    title: 'My Custom Command',
    description: 'Description of what this command does',
    prompt: 'The full prompt text that will be inserted when selected'
}
```

### Modifying Existing Commands

Edit the corresponding object in `COMMAND_TEMPLATES` array to change:
- Icon (any emoji)
- Title (display name)
- Description (help text)
- Prompt (the actual command text)

## User Experience

### Before
```
[Input: Type @ to mention files...]
```

### After
```
[Input: Type @ for files, / for commands...]

When typing /:
┌─────────────────────────────────────┐
│ 💡 Quick Commands                   │
├─────────────────────────────────────┤
│ 📝 Generate Description             │
│    Create a scenario-based problem  │
│    description for this project     │
├─────────────────────────────────────┤
│ 🔍 Code Review                      │
│    Perform a comprehensive code     │
│    review                           │
└─────────────────────────────────────┘
```

## Benefits

✅ **Faster Workflow** - No need to type long prompts  
✅ **Consistency** - Standardized prompts for common tasks  
✅ **Discoverability** - Users can see available commands  
✅ **Productivity** - Quick access to powerful features  
✅ **Best Practices** - Commands follow proven patterns  

## Future Enhancements

Potential improvements:
- [ ] Custom user-defined commands
- [ ] Command history and favorites
- [ ] Search/filter commands
- [ ] Command categories/groups
- [ ] Keyboard shortcuts for specific commands
- [ ] Command parameters/variables
- [ ] Import/export command templates

## Troubleshooting

### Command picker not showing
- Make sure you're typing `/` at the beginning or after a space
- Check that the extension is properly loaded

### Commands not inserting
- Verify the command picker is visible
- Try clicking directly on a command
- Check browser console for errors

### Styling issues
- Ensure VS Code theme is properly loaded
- Check for CSS conflicts

## Examples

### Example 1: Generate Project Description
1. Type `/` in chat
2. Select "📝 Generate Description"
3. Prompt is inserted: "Create a detailed scenario-based problem description..."
4. Press Enter to send
5. Agent analyzes project and creates description.md

### Example 2: Security Audit
1. Type `/`
2. Select "🔒 Security Audit"
3. Prompt is inserted automatically
4. Send the message
5. Agent performs security scan and creates security_audit.md

---

**Feature Status:** ✅ Complete and Ready to Use  
**Implementation Date:** 2026-01-28  
**Version:** 1.0
