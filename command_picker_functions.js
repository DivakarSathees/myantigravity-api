// Command Picker Functions for Slash Commands
// Add this code after the file picker functions in extension.ts

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

// =============================================
// REPLACE handleInputChange function with this:
// =============================================

function handleInputChange(event) {
    const input = event.target;
    const value = input.value;
    const cursorPos = input.selectionStart;

    // Check if @ or / is typed at cursor position
    const textBeforeCursor = value.substring(0, cursorPos);
    const atMatch = textBeforeCursor.match(/@(\w*)$/);
    const slashMatch = textBeforeCursor.match(/\/(\w*)$/);

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
}

// =============================================
// REPLACE handleInputKeyDown function with this:
// =============================================

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

    // Handle file picker navigation
    if (filePickerVisible) {
        const items = document.querySelectorAll('.file-picker-item');

        if (event.key === 'ArrowDown') {
            event.preventDefault();
            selectedFileIndex = Math.min(selectedFileIndex + 1, items.length - 1);
            updateFileSelection(items);
        } else if (event.key === 'ArrowUp') {
            event.preventDefault();
            selectedFileIndex = Math.max(selectedFileIndex - 1, 0);
            updateFileSelection(items);
        } else if (event.key === 'Enter' && selectedFileIndex >= 0) {
            event.preventDefault();
            const selectedItem = items[selectedFileIndex];
            const filePath = selectedItem.getAttribute('data-path');
            addSelectedFile(filePath);
            return;
        } else if (event.key === 'Escape') {
            hideFilePicker();
            return;
        }
    }

    // Default behavior (send on Enter)
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        send();
    }
}
