#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

"""
Extract Agent Response Hook
Extracts the agent's final response from chat transcript and sends as separate event.
"""

import json
import sys
import os
import subprocess
from pathlib import Path

def extract_final_response(transcript_path):
    """Extract the last agent response from the transcript."""
    if not os.path.exists(transcript_path):
        return None
    
    try:
        # Read the JSONL transcript file
        messages = []
        with open(transcript_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        messages.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        
        # Find the last assistant message
        for message in reversed(messages):
            if message.get('role') == 'assistant':
                content = message.get('content', '')
                if isinstance(content, list):
                    # Handle content that might be an array
                    text_content = []
                    for item in content:
                        if isinstance(item, dict) and item.get('type') == 'text':
                            text_content.append(item.get('text', ''))
                        elif isinstance(item, str):
                            text_content.append(item)
                    return '\n'.join(text_content) if text_content else None
                elif isinstance(content, str):
                    return content
                
        return None
        
    except Exception as e:
        print(f"Error extracting response: {e}", file=sys.stderr)
        return None

def main():
    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)
        
        # Extract transcript path
        transcript_path = input_data.get('transcript_path')
        if not transcript_path:
            sys.exit(0)  # No transcript available
        
        # Extract the final response
        final_response = extract_final_response(transcript_path)
        if not final_response:
            sys.exit(0)  # No response found
        
        # Create enhanced payload with the final response
        response_data = {
            'session_id': input_data.get('session_id', 'unknown'),
            'final_response': final_response,
            'response_length': len(final_response),
            'transcript_path': transcript_path,
            'original_payload': input_data
        }
        
        # Send as a separate "AgentResponse" event
        try:
            subprocess.run([
                'uv', 'run', '.claude/hooks/send_event.py',
                '--source-app', 'cc-hook-multi-agent-obvs',
                '--event-type', 'AgentResponse',
                '--summarize'
            ], input=json.dumps(response_data), text=True, timeout=10)
        except Exception:
            pass  # Don't fail if sending event fails
        
        sys.exit(0)
        
    except json.JSONDecodeError:
        sys.exit(0)
    except Exception:
        sys.exit(0)

if __name__ == '__main__':
    main()