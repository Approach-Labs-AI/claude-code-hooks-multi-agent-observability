#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

"""
Enhanced macOS Notification with Terminal Focusing
Uses terminal-notifier for advanced click handling and terminal activation.
"""

import json
import sys
import subprocess
import os
import tempfile
from pathlib import Path

def check_terminal_notifier():
    """Check if terminal-notifier is installed, install if not."""
    try:
        result = subprocess.run(["which", "terminal-notifier"], 
                               capture_output=True, text=True)
        if result.returncode == 0:
            return True
        
        # Try to install via Homebrew
        print("Installing terminal-notifier...", file=sys.stderr)
        subprocess.run(["brew", "install", "terminal-notifier"], 
                      capture_output=True, check=False)
        
        # Check again
        result = subprocess.run(["which", "terminal-notifier"], 
                               capture_output=True, text=True)
        return result.returncode == 0
        
    except:
        return False

def get_terminal_info():
    """Get current terminal application and window info."""
    try:
        # Get the parent process info to identify terminal
        ppid = os.getppid()
        result = subprocess.run(["ps", "-p", str(ppid), "-o", "comm="], 
                               capture_output=True, text=True)
        
        if result.returncode == 0:
            process_name = result.stdout.strip()
            
            # Map process names to application names
            terminal_map = {
                "Terminal": "Terminal",
                "iTerm2": "iTerm2", 
                "iTerm": "iTerm2",
                "Warp": "Warp",
                "alacritty": "Alacritty",
                "kitty": "kitty"
            }
            
            for proc, app in terminal_map.items():
                if proc in process_name:
                    return app
        
        return "Terminal"  # Default fallback
        
    except:
        return "Terminal"

def create_focus_script(terminal_app):
    """Create a script to focus the terminal window."""
    script_content = f'''#!/bin/bash
# Focus the terminal window
osascript -e '
tell application "{terminal_app}"
    activate
    try
        if "{terminal_app}" is "Terminal" then
            set frontWindow to front window
            set visible of frontWindow to true
            set index of frontWindow to 1
        else if "{terminal_app}" is "iTerm2" then  
            tell current window to set index to 1
        else
            activate
        end if
    on error
        activate
    end try
end tell
'

# Also try to bring terminal to front using System Events
osascript -e '
tell application "System Events"
    try
        set frontmost of application process "{terminal_app}" to true
    end try
end tell
'
'''
    
    # Create temporary script file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
        f.write(script_content)
        f.flush()
        os.chmod(f.name, 0o755)
        return f.name

def send_notification_with_terminal_notifier(message, session_id, terminal_app):
    """Send notification using terminal-notifier with click to focus."""
    try:
        # Get path to our focus script
        script_dir = Path(__file__).parent
        focus_script = script_dir / "focus_terminal.py"
        
        # Use terminal-notifier with click action
        cmd = [
            "terminal-notifier",
            "-title", "🤖 Claude Code Agent",  
            "-subtitle", f"Session: {session_id[:8]}...",
            "-message", message,
            "-sound", "Submarine",
            "-execute", f'export PATH="$HOME/.local/bin:$PATH" && uv run "{focus_script}"',
            "-timeout", "30",
            "-sender", "com.apple.Terminal"  # This helps with focusing
        ]
        
        subprocess.run(cmd, capture_output=True, check=False)
        return True
        
    except Exception as e:
        print(f"Terminal-notifier error: {e}", file=sys.stderr)
        return False

def send_fallback_notification(message, session_id):
    """Fallback notification using built-in osascript."""
    try:
        # Play sound first
        subprocess.run(["afplay", "/System/Library/Sounds/Submarine.aiff"], 
                      capture_output=True, check=False)
        
        # Send notification
        notification_script = f'''
display notification "{message}" with title "🤖 Claude Code Agent" subtitle "Session: {session_id[:8]}..." sound name "Submarine"
'''
        
        subprocess.run(["osascript", "-e", notification_script], 
                      capture_output=True, check=False)
        
    except:
        pass

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
        
        # Get terminal info
        terminal_app = get_terminal_info()
        
        # Try enhanced notification first
        if check_terminal_notifier():
            success = send_notification_with_terminal_notifier(message, session_id, terminal_app)
            if not success:
                send_fallback_notification(message, session_id)
        else:
            send_fallback_notification(message, session_id)
        
        sys.exit(0)
        
    except json.JSONDecodeError:
        sys.exit(0)
    except Exception:
        sys.exit(0)

if __name__ == '__main__':
    main()