#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

"""
Fixed Terminal Notification
Focuses the actual terminal window that Claude Code is running in.
"""

import json
import sys
import subprocess
import os

def get_terminal_window_info():
    """Get the current terminal window info including window ID."""
    try:
        # Get the current TTY
        tty = subprocess.run(["tty"], capture_output=True, text=True).stdout.strip()
        
        # Get process tree to find terminal
        pid = os.getpid()
        terminal_pid = None
        terminal_app = None
        
        for _ in range(10):  # Check up to 10 parent levels
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
                    
                    # Check if this is a terminal process
                    if any(term in comm.lower() for term in ['terminal', 'iterm', 'warp']):
                        terminal_pid = pid
                        if 'iterm' in comm.lower():
                            terminal_app = 'iTerm2'
                        elif 'terminal' in comm.lower():
                            terminal_app = 'Terminal'
                        elif 'warp' in comm.lower():
                            terminal_app = 'Warp'
                        break
                    
                    pid = int(ppid)
                else:
                    break
        
        return {
            'app': terminal_app or 'Terminal',
            'pid': terminal_pid,
            'tty': tty
        }
        
    except Exception as e:
        print(f"Error getting terminal info: {e}", file=sys.stderr)
        return {'app': 'Terminal', 'pid': None, 'tty': None}

def focus_current_terminal_window(terminal_info):
    """Focus the specific terminal window we're running in."""
    terminal_app = terminal_info['app']
    terminal_pid = terminal_info['pid']
    tty = terminal_info['tty']
    
    print(f"Focusing {terminal_app}, PID: {terminal_pid}, TTY: {tty}", file=sys.stderr)
    
    if terminal_app == 'iTerm2':
        # For iTerm2, find the specific window/tab
        applescript = f'''
tell application "iTerm2"
    activate
    try
        -- Find the window with our session
        repeat with theWindow in windows
            repeat with theTab in tabs of theWindow
                repeat with theSession in sessions of theTab
                    if (tty of theSession) is "{tty}" then
                        select theTab
                        set index of theWindow to 1
                        return
                    end if
                end repeat
            end repeat
        end repeat
        -- Fallback: just bring iTerm2 to front
        set index of front window to 1
    end try
end tell
'''
    elif terminal_app == 'Terminal':
        # For Terminal.app, find the specific window
        applescript = f'''
tell application "Terminal"
    activate
    try
        -- Find the window with our TTY
        repeat with theWindow in windows
            repeat with theTab in tabs of theWindow
                if (tty of theTab) is "{tty}" then
                    set index of theWindow to 1
                    set selected tab of theWindow to theTab
                    set visible of theWindow to true
                    return
                end if
            end repeat
        end repeat
        -- Fallback: bring front window forward
        set index of front window to 1
        set visible of front window to true
    end try
end tell
'''
    else:
        # Generic fallback
        applescript = f'tell application "{terminal_app}" to activate'
    
    try:
        # Execute the AppleScript
        subprocess.run(["osascript", "-e", applescript], 
                      timeout=5, check=False, capture_output=True)
        
        # Additional System Events approach
        subprocess.run([
            "osascript", "-e", 
            f'''tell application "System Events"
                set frontmost of application process "{terminal_app}" to true
            end tell'''
        ], timeout=3, check=False, capture_output=True)
        
    except Exception as e:
        print(f"Error focusing terminal: {e}", file=sys.stderr)

def send_notification_with_focus(message, session_id, terminal_info):
    """Send notification with proper terminal focusing."""
    
    # Show notification first
    applescript_notification = f'''
display notification "{message}" with title "🤖 Claude Code Agent" subtitle "Session: {session_id[:8]}" sound name "Submarine"
'''
    
    # Show dialog with focus action
    applescript_dialog = f'''
delay 1
set userChoice to display dialog "🤖 Claude Code Agent\\n\\n{message}\\n\\nSession: {session_id[:8]}\\nTerminal: {terminal_info['app']} ({terminal_info['tty']})" ¬
    with title "Claude Code Agent" ¬
    buttons {{"Dismiss", "Focus Terminal"}} ¬
    default button "Focus Terminal" ¬
    with icon note ¬
    giving up after 30

if button returned of userChoice is "Focus Terminal" or gave up of userChoice is true then
    return "focus"
else
    return "dismiss"
end if
'''
    
    try:
        # Send notification
        subprocess.run(["osascript", "-e", applescript_notification], 
                      capture_output=True, check=False)
        
        # Show dialog and get response
        result = subprocess.run(["osascript", "-e", applescript_dialog], 
                               capture_output=True, text=True, timeout=35)
        
        # If user chose to focus or dialog timed out, focus the terminal
        if result.returncode == 0 and ("focus" in result.stdout or result.stdout.strip() == ""):
            focus_current_terminal_window(terminal_info)
            
    except Exception as e:
        print(f"Notification error: {e}", file=sys.stderr)

def main():
    try:
        input_data = json.load(sys.stdin)
        message = input_data.get('message', 'Agent needs your input')
        session_id = input_data.get('session_id', 'unknown')
        
        # Skip spam messages
        if message == 'Claude is waiting for your input':
            sys.exit(0)
        
        # Get terminal info
        terminal_info = get_terminal_window_info()
        
        # Send notification with focus capability
        send_notification_with_focus(message, session_id, terminal_info)
        
        sys.exit(0)
        
    except Exception as e:
        print(f"Main error: {e}", file=sys.stderr)
        sys.exit(0)

if __name__ == '__main__':
    main()