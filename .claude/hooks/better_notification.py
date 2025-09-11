#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

"""
Better macOS Notification with Action Button
Creates notifications with custom action buttons that reliably focus terminal.
"""

import json
import sys
import subprocess
import os
import tempfile
from pathlib import Path

def get_terminal_info():
    """Get current terminal app info."""
    try:
        # Check parent processes
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

def create_focus_action():
    """Create an action that focuses the terminal."""
    terminal_app = get_terminal_info()
    
    # Create a simple shell command to focus terminal
    focus_cmd = f'''
osascript -e 'tell application "{terminal_app}" to activate' -e 'tell application "{terminal_app}" to set index of front window to 1' 2>/dev/null || 
osascript -e 'tell application "System Events" to set frontmost of application process "{terminal_app}" to true' 2>/dev/null
'''
    
    return focus_cmd.strip()

def send_notification_with_action(message, session_id):
    """Send notification with a custom action button."""
    try:
        focus_action = create_focus_action()
        
        # Method 1: Use terminal-notifier with actions
        cmd = [
            "terminal-notifier",
            "-title", "🤖 Claude Code",
            "-subtitle", f"Session {session_id[:8]}",
            "-message", message,
            "-sound", "Submarine",
            "-actions", "Focus Terminal",
            "-timeout", "30"
        ]
        
        # Run notification and capture which action was chosen
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # If user clicked "Focus Terminal", run the focus action
        if result.returncode == 0 and "Focus Terminal" in result.stdout:
            subprocess.run(focus_action, shell=True, capture_output=True)
        
        return True
        
    except Exception as e:
        print(f"Action notification failed: {e}", file=sys.stderr)
        return False

def send_simple_clickable_notification(message, session_id):
    """Simpler approach with immediate activation on any click."""
    try:
        terminal_app = get_terminal_info()
        
        # Create a notification that runs the focus command when clicked
        applescript = f'''
set theMessage to "{message}"
set theTitle to "🤖 Claude Code Agent"
set theSubtitle to "Session: {session_id[:8]}... (Click to focus terminal)"

display notification theMessage with title theTitle subtitle theSubtitle sound name "Submarine"

-- Also immediately try to focus, in case notification is clicked quickly
delay 1
tell application "{terminal_app}"
    activate
    try
        set frontmost to true
        set index of front window to 1
    end try
end tell
'''
        
        subprocess.run(["osascript", "-e", applescript], 
                      capture_output=True, check=False)
        return True
        
    except Exception:
        return False

def main():
    try:
        input_data = json.load(sys.stdin)
        message = input_data.get('message', 'Agent needs your input')
        session_id = input_data.get('session_id', 'unknown')
        
        # Skip spam messages
        if message == 'Claude is waiting for your input':
            sys.exit(0)
        
        # Try different notification methods
        success = False
        
        # Method 1: Try action-based notification
        if not success:
            success = send_notification_with_action(message, session_id)
        
        # Method 2: Try simple clickable notification  
        if not success:
            success = send_simple_clickable_notification(message, session_id)
        
        # Method 3: Fallback to basic notification
        if not success:
            subprocess.run([
                "osascript", "-e", 
                f'display notification "{message}" with title "🤖 Claude Code" sound name "Submarine"'
            ], capture_output=True)
        
        sys.exit(0)
        
    except:
        sys.exit(0)

if __name__ == '__main__':
    main()