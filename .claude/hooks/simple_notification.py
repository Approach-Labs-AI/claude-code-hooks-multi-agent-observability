#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

"""
Simple but Effective macOS Notification
Uses AppleScript dialog with custom buttons for reliable terminal focusing.
"""

import json
import sys
import subprocess
import os

def get_terminal_app():
    """Detect current terminal application."""
    try:
        pid = os.getpid()
        for _ in range(5):
            result = subprocess.run(
                ["ps", "-p", str(pid), "-o", "ppid=,comm="], 
                capture_output=True, text=True
            )
            if result.returncode != 0:
                break
                
            lines = result.stdout.strip().split('\n')
            if lines:
                parts = lines[0].strip().split(None, 1)
                if len(parts) == 2:
                    ppid, comm = parts
                    
                    if 'iterm' in comm.lower():
                        return 'iTerm2'
                    elif 'terminal' in comm.lower():
                        return 'Terminal'
                    elif 'warp' in comm.lower():
                        return 'Warp'
                    
                    pid = int(ppid)
                    
        return 'Terminal'
    except:
        return 'Terminal'

def send_notification_with_dialog(message, session_id):
    """Send notification using AppleScript dialog with focus button."""
    terminal_app = get_terminal_app()
    
    # Create an AppleScript that shows notification and handles the response
    applescript = f'''
-- Show the notification first
display notification "{message}" with title "🤖 Claude Code Agent" subtitle "Session: {session_id[:8]}" sound name "Submarine"

-- Wait a moment then show dialog with options
delay 1

set userChoice to display dialog "🤖 Claude Code Agent needs your attention:\\n\\n{message}\\n\\nSession: {session_id[:8]}..." ¬
    with title "Claude Code Agent" ¬
    buttons {{"Dismiss", "Focus Terminal"}} ¬
    default button "Focus Terminal" ¬
    with icon note ¬
    giving up after 30

if button returned of userChoice is "Focus Terminal" or gave up of userChoice is true then
    -- Focus the terminal
    tell application "{terminal_app}"
        activate
        try
            set frontmost to true
            if "{terminal_app}" is "Terminal" then
                set index of front window to 1
            end if
        end try
    end tell
    
    -- Additional focus using System Events
    tell application "System Events"
        try
            set frontmost of application process "{terminal_app}" to true
        end try
    end tell
end if
'''
    
    try:
        # Run in background so it doesn't block
        subprocess.Popen([
            "osascript", "-e", applescript
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        print(f"Dialog notification failed: {e}", file=sys.stderr)
        return False

def send_simple_notification(message, session_id):
    """Fallback: simple notification with immediate focus."""
    terminal_app = get_terminal_app()
    
    applescript = f'''
-- Show notification
display notification "{message}" with title "🤖 Claude Code" subtitle "Click to focus terminal" sound name "Submarine"

-- Focus terminal immediately (user can ignore if they want)
delay 2
tell application "{terminal_app}"
    activate
end tell
'''
    
    try:
        subprocess.run(["osascript", "-e", applescript], 
                      timeout=5, check=False, capture_output=True)
    except:
        pass

def main():
    try:
        input_data = json.load(sys.stdin)
        message = input_data.get('message', 'Agent needs your input')
        session_id = input_data.get('session_id', 'unknown')
        
        # Skip spam messages
        if message == 'Claude is waiting for your input':
            sys.exit(0)
        
        # Try dialog approach first
        success = send_notification_with_dialog(message, session_id)
        
        # Fallback to simple notification
        if not success:
            send_simple_notification(message, session_id)
        
        sys.exit(0)
        
    except:
        sys.exit(0)

if __name__ == '__main__':
    main()