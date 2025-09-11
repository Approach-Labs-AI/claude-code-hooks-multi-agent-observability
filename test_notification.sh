#!/bin/bash

# Test script for macOS notifications
echo "🧪 Testing Claude Code notification system..."

# Add paths  
export PATH="$HOME/.local/bin:$PATH"

echo ""
echo "📱 Testing the enhanced notification system..."
echo "   You should see:"
echo "   1. A notification with submarine sound"
echo "   2. Then a dialog with 'Focus Terminal' button"
echo "   3. Click 'Focus Terminal' to test terminal focusing!"
echo ""

# Test the new simple notification system
echo '{"message": "🚀 Agent needs your input! Click Focus Terminal button to test.", "session_id": "demo-session-456"}' | uv run .claude/hooks/simple_notification.py

echo ""
echo "✅ Test sent! Check for:"
echo "   • Notification appeared with sound"
echo "   • Dialog box with Focus Terminal button"  
echo "   • Clicking button should focus this terminal"
echo ""
echo "💡 If it works, the system is ready for Claude Code!"