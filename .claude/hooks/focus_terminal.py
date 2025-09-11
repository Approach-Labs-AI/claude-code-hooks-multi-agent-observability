#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

"""
Terminal Focus Script
Dedicated script to focus the terminal window when notification is clicked.
"""

import subprocess
import sys
import os

def get_current_terminal():
    """Get the current terminal application."""
    try:
        # Get parent processes to find terminal
        pid = os.getpid()
        for _ in range(5):  # Check up to 5 parent levels
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
                    
                    # Check if this is a terminal
                    if any(term in comm.lower() for term in ['terminal', 'iterm', 'warp', 'alacritty', 'kitty']):
                        # Map to app name
                        if 'iterm' in comm.lower():
                            return 'iTerm2'
                        elif 'terminal' in comm.lower():
                            return 'Terminal'
                        elif 'warp' in comm.lower():
                            return 'Warp'
                        elif 'alacritty' in comm.lower():
                            return 'Alacritty'
                        elif 'kitty' in comm.lower():
                            return 'kitty'
                    
                    pid = int(ppid)
                else:
                    break
                    
        return 'Terminal'  # Default fallback
        
    except:
        return 'Terminal'

def focus_terminal():
    """Focus the terminal window with multiple strategies."""
    terminal_app = get_current_terminal()
    
    # Strategy 1: Simple and reliable activation
    try:
        subprocess.run([
            "osascript", "-e", f'tell application "{terminal_app}" to activate'
        ], timeout=3, check=True)
    except:
        pass
    
    # Strategy 2: Try to bring window to front
    try:
        if terminal_app == "Terminal":
            applescript = '''
tell application "Terminal"
    activate
    try
        set index of front window to 1
        set visible of front window to true
    end try
end tell
'''
        elif terminal_app == "iTerm2":
            applescript = '''
tell application "iTerm2"
    activate
    try
        tell current window to set index to 1
    end try
end tell
'''
        else:
            applescript = f'tell application "{terminal_app}" to activate'
        
        subprocess.run(["osascript", "-e", applescript], timeout=3, check=False)
    except:
        pass
    
    # Strategy 3: Use System Events as final attempt
    try:
        subprocess.run([
            "osascript", "-e", 
            f'tell application "System Events" to set frontmost of application process "{terminal_app}" to true'
        ], timeout=2, check=False)
    except:
        pass

def main():
    focus_terminal()
    sys.exit(0)

if __name__ == '__main__':
    main()