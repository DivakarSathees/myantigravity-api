#!/usr/bin/env python3
"""
Script to add slash command functionality to extension.ts
"""

import re

# Read the file
with open('extension-builder/myantigravity/src/extension.ts', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update handleInputChange function
old_handle_input_change = '''    // Handle input changes for @ detection
    function handleInputChange(event) {
        const input = event.target;
        const value = input.value;
        const cursorPos = input.selectionStart;
        
        // Check if @ is typed at cursor position
        const textBeforeCursor = value.substring(0, cursorPos);
        const atMatch = textBeforeCursor.match(/@(\\w*)$/);
        
        if (atMatch) {
            if (!filePickerVisible) {
                showFilePicker();
            }
        } else if (filePickerVisible) {
            hideFilePicker();
        }
    }'''

new_handle_input_change = '''    // Handle input changes for @ detection and / detection
    function handleInputChange(event) {
        const input = event.target;
        const value = input.value;
        const cursorPos = input.selectionStart;
        
        // Check if @ or / is typed at cursor position
        const textBeforeCursor = value.substring(0, cursorPos);
        const atMatch = textBeforeCursor.match(/@(\\w*)$/);
        const slashMatch = textBeforeCursor.match(/\\/(\\w*)$/);
        
        if (slashMatch) {
            // Show command picker
            if (!commandPickerVisible) {
                showCommandPicker();
            }
            // Hide file picker if it's open
            if (filePickerVisible) {
                hideFilePicker();
            }
        } else if (atMatch) {
            // Show file picker
            if (!filePickerVisible) {
                showFilePicker();
            }
            // Hide command picker if it's open
            if (commandPickerVisible) {
                hideCommandPicker();
            }
        } else {
            // Hide both pickers
            if (filePickerVisible) {
                hideFilePicker();
            }
            if (commandPickerVisible) {
                hideCommandPicker();
            }
        }
    }'''

content = content.replace(old_handle_input_change, new_handle_input_change)

# 2. Add command picker functions after the file picker section
# Find the location to insert (after "Close file picker when clicking outside")
insertion_point = content.find('    // Close file picker when clicking outside')
if insertion_point != -1:
    # Find the end of that event listener
    next_section = content.find('    // =====', insertion_point + 100)
    if next_section != -1:
        command_functions = '''
    
    // =============================================
    // Command Picker Functions
    // =============================================
    
    function showCommandPicker() {
        const picker = document.getElementById('command-picker');
        const commandList = document.getElementById('command-list');
        
        commandPickerVisible = true;
        picker.classList.add('visible');
        
        // Show all commands
        filteredCommands = COMMAND_TEMPLATES;
        renderCommandList(filteredCommands);
    }
    
    function hideCommandPicker() {
        const picker = document.getElementById('command-picker');
        picker.classList.remove('visible');
        commandPickerVisible = false;
        selectedCommandIndex = -1;
    }
    
    function renderCommandList(commands) {
        const commandList = document.getElementById('command-list');
        
        if (commands.length === 0) {
            commandList.innerHTML = '<div class="file-picker-empty">No commands found</div>';
            return;
        }
        
        commandList.innerHTML = commands.map((cmd, index) => `
            <div class="command-item ${index === selectedCommandIndex ? 'selected' : ''}" 
                 onclick="selectCommand('${cmd.id}')"
                 data-command-id="${cmd.id}">
                <div class="command-item-title">
                    <span class="command-item-icon">${cmd.icon}</span>
                    <span>${cmd.title}</span>
                </div>
                <div class="command-item-description">${cmd.description}</div>
            </div>
        `).join('');
    }
    
    function selectCommand(commandId) {
        const command = COMMAND_TEMPLATES.find(c => c.id === commandId);
        if (!command) return;
        
        hideCommandPicker();
        
        // Replace / with the command prompt
        const input = document.getElementById('input');
        input.value = command.prompt;
        input.focus();
    }
    
    function updateCommandSelection(items) {
        items.forEach((item, index) => {
            if (index === selectedCommandIndex) {
                item.classList.add('selected');
            } else {
                item.classList.remove('selected');
            }
        });
        
        // Scroll selected item into view
        if (selectedCommandIndex >= 0 && items[selectedCommandIndex]) {
            items[selectedCommandIndex].scrollIntoView({ block: 'nearest' });
        }
    }
    
    // Make command functions globally available
    window.selectCommand = selectCommand;
'''
        content = content[:next_section] + command_functions + '\n' + content[next_section:]

# 3. Update handleInputKeyDown to handle command picker
# This is more complex, so we'll add it at the beginning of the function
old_key_down_start = '''    // Handle input keydown for @ detection and navigation
    function handleInputKeyDown(event) {
        if (filePickerVisible) {'''

new_key_down_start = '''    // Handle input keydown for @ detection, / detection and navigation
    function handleInputKeyDown(event) {
        // Handle command picker navigation
        if (commandPickerVisible) {
            const items = document.querySelectorAll('.command-item');
            
            if (event.key === 'ArrowDown') {
                event.preventDefault();
                selectedCommandIndex = Math.min(selectedCommandIndex + 1, items.length - 1);
                updateCommandSelection(items);
            } else if (event.key === 'ArrowUp') {
                event.preventDefault();
                selectedCommandIndex = Math.max(selectedCommandIndex - 1, 0);
                updateCommandSelection(items);
            } else if (event.key === 'Enter' && selectedCommandIndex >= 0) {
                event.preventDefault();
                const selectedItem = items[selectedCommandIndex];
                const commandId = selectedItem.getAttribute('data-command-id');
                selectCommand(commandId);
                return;
            } else if (event.key === 'Escape') {
                hideCommandPicker();
                return;
            }
            return;
        }
        
        if (filePickerVisible) {'''

content = content.replace(old_key_down_start, new_key_down_start)

# Write the updated content
with open('extension-builder/myantigravity/src/extension.ts', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Successfully added slash command functionality!")
print("📝 Changes made:")
print("  - Updated handleInputChange to detect / character")
print("  - Added command picker functions (show, hide, render, select)")
print("  - Updated handleInputKeyDown to handle command picker navigation")
