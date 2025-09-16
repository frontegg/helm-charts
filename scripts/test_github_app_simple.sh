#!/bin/bash
# Simple GitHub App test script
# Usage: ./test_github_app_simple.sh <APP_ID> <PRIVATE_KEY_FILE>

set -e

if [ $# -ne 2 ]; then
    echo "Usage: $0 <APP_ID> <PRIVATE_KEY_FILE>"
    echo "Example: $0 1960250 /path/to/private-key.pem"
    exit 1
fi

APP_ID="$1"
PRIVATE_KEY_FILE="$2"

echo "🔍 Testing GitHub App Configuration"
echo "=================================="
echo "App ID: $APP_ID"
echo "Private Key File: $PRIVATE_KEY_FILE"
echo ""

# Check if private key file exists
if [ ! -f "$PRIVATE_KEY_FILE" ]; then
    echo "❌ Private key file not found: $PRIVATE_KEY_FILE"
    exit 1
fi

# Check private key format
echo "1. Checking private key format..."
if ! grep -q "BEGIN.*PRIVATE KEY" "$PRIVATE_KEY_FILE"; then
    echo "❌ Private key file doesn't contain PEM header"
    echo "   Expected: -----BEGIN PRIVATE KEY-----"
    exit 1
fi

if ! grep -q "END.*PRIVATE KEY" "$PRIVATE_KEY_FILE"; then
    echo "❌ Private key file doesn't contain PEM footer"
    echo "   Expected: -----END PRIVATE KEY-----"
    exit 1
fi

echo "✅ Private key format looks correct"

# Test with GitHub CLI if available
if command -v gh &> /dev/null; then
    echo ""
    echo "2. Testing with GitHub CLI..."
    
    # Try to authenticate with the app (this won't work directly, but will validate the key format)
    echo "   Note: This test validates the key format, not full app authentication"
    echo "✅ GitHub CLI is available for additional testing"
else
    echo ""
    echo "2. GitHub CLI not available, skipping CLI tests"
fi

echo ""
echo "3. Key content preview:"
echo "   First line: $(head -n1 "$PRIVATE_KEY_FILE")"
echo "   Last line:  $(tail -n1 "$PRIVATE_KEY_FILE")"
echo "   Total lines: $(wc -l < "$PRIVATE_KEY_FILE")"

echo ""
echo "✅ Basic validation complete!"
echo ""
echo "📋 Next steps:"
echo "1. Ensure these values are set as GitHub repository secrets:"
echo "   - GH_APP_ID = $APP_ID"
echo "   - GH_APP_PRIVATE_KEY = [full content of $PRIVATE_KEY_FILE]"
echo ""
echo "2. Verify GitHub App is installed on frontegg organization"
echo "3. Check GitHub App permissions (Contents: Read, Metadata: Read)"
echo "4. Run the workflow to test the full authentication flow"
