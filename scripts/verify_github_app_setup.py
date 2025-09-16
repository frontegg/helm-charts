#!/usr/bin/env python3
"""
Verify GitHub App setup and configuration.
This script helps you verify your GitHub App secrets and configuration.
"""

import os
import re
import sys

def verify_app_id(app_id_str):
    """Verify App ID format"""
    print("🔍 Verifying GitHub App ID...")
    
    if not app_id_str:
        print("❌ App ID is empty or not provided")
        return False
    
    if not app_id_str.isdigit():
        print(f"❌ App ID should be numeric, got: {app_id_str}")
        return False
    
    app_id = int(app_id_str)
    if app_id < 1:
        print(f"❌ App ID should be positive, got: {app_id}")
        return False
    
    print(f"✅ App ID format is valid: {app_id}")
    return True

def verify_private_key(private_key_content):
    """Verify private key format"""
    print("\n🔍 Verifying GitHub App Private Key...")
    
    if not private_key_content:
        print("❌ Private key is empty or not provided")
        return False
    
    # Check for PEM format
    if not private_key_content.startswith('-----BEGIN'):
        print("❌ Private key must start with '-----BEGIN PRIVATE KEY-----' or similar")
        print(f"   Current start: {private_key_content[:50]}...")
        return False
    
    if not private_key_content.rstrip().endswith('-----'):
        print("❌ Private key must end with '-----END PRIVATE KEY-----' or similar")
        print(f"   Current end: ...{private_key_content.rstrip()[-50:]}")
        return False
    
    # Check for common PEM headers
    valid_headers = [
        '-----BEGIN PRIVATE KEY-----',
        '-----BEGIN RSA PRIVATE KEY-----',
        '-----BEGIN EC PRIVATE KEY-----'
    ]
    
    header_found = False
    for header in valid_headers:
        if header in private_key_content:
            header_found = True
            print(f"✅ Found valid PEM header: {header}")
            break
    
    if not header_found:
        print("❌ No valid PEM header found")
        print("   Expected one of:", valid_headers)
        return False
    
    # Check for corresponding footer
    if '-----BEGIN PRIVATE KEY-----' in private_key_content:
        if '-----END PRIVATE KEY-----' not in private_key_content:
            print("❌ Missing '-----END PRIVATE KEY-----' footer")
            return False
    elif '-----BEGIN RSA PRIVATE KEY-----' in private_key_content:
        if '-----END RSA PRIVATE KEY-----' not in private_key_content:
            print("❌ Missing '-----END RSA PRIVATE KEY-----' footer")
            return False
    elif '-----BEGIN EC PRIVATE KEY-----' in private_key_content:
        if '-----END EC PRIVATE KEY-----' not in private_key_content:
            print("❌ Missing '-----END EC PRIVATE KEY-----' footer")
            return False
    
    # Check key length (should have base64 content)
    lines = private_key_content.strip().split('\n')
    content_lines = [line for line in lines if not line.startswith('-----')]
    
    if len(content_lines) < 5:
        print("❌ Private key seems too short (less than 5 lines of content)")
        return False
    
    # Check base64 format of content lines
    base64_pattern = re.compile(r'^[A-Za-z0-9+/=]+$')
    for i, line in enumerate(content_lines[:3]):  # Check first 3 content lines
        if not base64_pattern.match(line):
            print(f"❌ Line {i+1} doesn't look like valid base64: {line[:20]}...")
            return False
    
    print(f"✅ Private key format appears valid ({len(content_lines)} content lines)")
    return True

def check_workflow_secrets_usage():
    """Check how secrets are used in the workflow"""
    print("\n🔍 Checking workflow secrets usage...")
    
    workflow_path = '.github/workflows/microservices-version-sync.yml'
    if not os.path.exists(workflow_path):
        print(f"❌ Workflow file not found: {workflow_path}")
        return False
    
    with open(workflow_path, 'r') as f:
        content = f.read()
    
    # Check for correct secret references
    if '${{ secrets.GH_APP_ID }}' not in content:
        print("❌ GH_APP_ID secret not found in workflow")
        return False
    else:
        print("✅ GH_APP_ID secret reference found")
    
    if '${{ secrets.GH_APP_PRIVATE_KEY }}' not in content:
        print("❌ GH_APP_PRIVATE_KEY secret not found in workflow")
        return False
    else:
        print("✅ GH_APP_PRIVATE_KEY secret reference found")
    
    # Check for GitHub App token generation
    if 'actions/create-github-app-token@v1' not in content:
        print("❌ GitHub App token generation action not found")
        return False
    else:
        print("✅ GitHub App token generation action found")
    
    return True

def main():
    """Main verification function"""
    print("🔧 GitHub App Configuration Verification")
    print("=" * 50)
    
    # Get inputs
    app_id = input("Enter your GitHub App ID: ").strip()
    
    print("\nEnter your private key content (paste the entire PEM content, then press Enter twice):")
    private_key_lines = []
    while True:
        try:
            line = input()
            if line == "" and private_key_lines:
                break
            private_key_lines.append(line)
        except EOFError:
            break
    
    private_key = '\n'.join(private_key_lines)
    
    print("\n" + "=" * 50)
    
    # Run verifications
    app_id_valid = verify_app_id(app_id)
    private_key_valid = verify_private_key(private_key)
    workflow_valid = check_workflow_secrets_usage()
    
    print("\n" + "=" * 50)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 50)
    
    print(f"App ID: {'✅ Valid' if app_id_valid else '❌ Invalid'}")
    print(f"Private Key: {'✅ Valid' if private_key_valid else '❌ Invalid'}")
    print(f"Workflow Config: {'✅ Valid' if workflow_valid else '❌ Invalid'}")
    
    if app_id_valid and private_key_valid and workflow_valid:
        print("\n🎉 All verifications passed!")
        print("\nNext steps:")
        print("1. Ensure these exact values are set as GitHub repository secrets:")
        print(f"   - GH_APP_ID = {app_id}")
        print("   - GH_APP_PRIVATE_KEY = [the full PEM content you provided]")
        print("2. Verify GitHub App is installed on the frontegg organization")
        print("3. Check GitHub App permissions (Contents: Read, Metadata: Read)")
        return True
    else:
        print("\n❌ Some verifications failed. Please fix the issues above.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
