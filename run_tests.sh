#!/bin/bash

# Run tests for Google Calendar MCP Bot

echo "🧪 Running Bot Tests..."
echo ""

# Set environment variables
export GOOGLE_OAUTH_CREDENTIALS="$(pwd)/credentials/google_credentials.json"
export BROWSER=/usr/bin/chromium

# Activate virtual environment
source venv/bin/activate

# Run tests
python tests/test_bot.py

# Capture exit code
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed. Exit code: $EXIT_CODE"
fi

exit $EXIT_CODE
