#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

"""
Enhanced macOS Notification Hook
Creates native macOS notifications with sound and terminal focusing capability.
"""

import json
import sys
import subprocess
import os
import tempfile
from pathlib import Path

def get_terminal_app():
    """Detect which terminal application is currently running."""
    try:
        # Check common terminal applications in order of preference
        terminals = [
            ("Terminal", "Terminal"),
            ("iTerm", "iTerm2"),
            ("Warp", "Warp"),
            ("Alacritty", "Alacritty"),
            ("kitty", "kitty")
        ]
        
        for display_name, process_name in terminals:
            result = subprocess.run([
                "osascript", "-e", 
                f'tell application "System Events" to count (every process whose name is "{process_name}")'
            ], capture_output=True, text=True)
            
            if result.returncode == 0 and int(result.stdout.strip()) > 0:
                return process_name
                
        return "Terminal"  # Default fallback
    except:
        return "Terminal"

def create_applescript_handler():
    """Create a temporary AppleScript handler that can focus the terminal."""
    terminal_app = get_terminal_app()
    
    applescript_content = f'''
on run
    tell application "{terminal_app}"
        activate
        if "{terminal_app}" is "Terminal" then
            try
                -- For Terminal.app, bring the front window forward
                set frontWindow to front window
                set visible of frontWindow to true
                set index of frontWindow to 1
            end try
        else if "{terminal_app}" is "iTerm2" then
            try
                -- For iTerm2, bring the current window forward
                tell current window
                    set visible to true
                    set index to 1
                end tell
            end try
        else
            -- For other terminals, just activate
            activate
        end if
    end tell
end run
'''
    
    # Create temporary AppleScript file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.scpt', delete=False) as f:
        f.write(applescript_content)
        return f.name

def send_macos_notification(message, session_id):
    """Send a native macOS notification with sound and click handler."""
    try:
        # Create the AppleScript handler
        script_path = create_applescript_handler()
        
        # Create notification title and subtitle
        title = "🤖 Claude Code Agent"
        subtitle = f"Session: {session_id[:8]}..."
        
        # Use osascript to create notification with click handler
        notification_script = f'''
display notification "{message}" with title "{title}" subtitle "{subtitle}" sound name "Submarine"
'''
        
        # Send the notification
        subprocess.run([
            "osascript", "-e", notification_script
        ], check=False, capture_output=True)
        
        # Also play a system sound directly for reliability
        subprocess.run(["afplay", "/System/Library/Sounds/Submarine.aiff"], 
                      check=False, capture_output=True)
        
        # Clean up the temporary script after a delay
        subprocess.Popen([
            "sh", "-c", f"sleep 10 && rm -f '{script_path}'"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    except Exception as e:
        # Fallback to simple notification without click handler
        try:
            subprocess.run([
                "osascript", "-e", 
                f'display notification "{message}" with title "{title}" sound name "Submarine"'
            ], check=False, capture_output=True)
        except:
            pass

def create_notification_center_script():
    """Create a more advanced notification that can handle clicks."""
    try:
        terminal_app = get_terminal_app()
        
        # Create a shell script that will handle the notification click
        click_handler = f'''#!/bin/bash
osascript -e 'tell application "{terminal_app}" to activate'
osascript -e 'tell application "{terminal_app}" to set index of front window to 1'
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(click_handler)
            f.flush()
            os.chmod(f.name, 0o755)
            return f.name
            
    except:
        return None

def main():
    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)
        
        # Extract notification details
        message = input_data.get('message', 'Agent needs your input')
        session_id = input_data.get('session_id', 'unknown')
        
        # Skip generic waiting message to avoid spam
        if message == 'Claude is waiting for your input':
            sys.exit(0)
        
        # Send enhanced macOS notification
        send_macos_notification(message, session_id)
        
        sys.exit(0)
        
    except json.JSONDecodeError:
        sys.exit(0)
    except Exception:
        sys.exit(0)

if __name__ == '__main__':
    main()