#!/usr/bin/env python3
"""
Test GitHub App configuration and permissions.
This script helps debug GitHub App issues before running the full workflow.
"""

import os
import sys
import requests
import json
import jwt
import time
from datetime import datetime, timedelta

def generate_jwt_token(app_id, private_key_path):
    """Generate JWT token for GitHub App authentication"""
    try:
        with open(private_key_path, 'r') as f:
            private_key = f.read()
    except FileNotFoundError:
        print(f"❌ Private key file not found: {private_key_path}")
        return None
    
    # Create JWT payload
    now = datetime.utcnow()
    payload = {
        'iat': int(now.timestamp()),
        'exp': int((now + timedelta(minutes=10)).timestamp()),
        'iss': app_id
    }
    
    try:
        token = jwt.encode(payload, private_key, algorithm='RS256')
        return token
    except Exception as e:
        print(f"❌ Failed to generate JWT token: {e}")
        return None

def get_installation_token(jwt_token, installation_id):
    """Get installation access token using JWT"""
    headers = {
        'Authorization': f'Bearer {jwt_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    url = f'https://api.github.com/app/installations/{installation_id}/access_tokens'
    response = requests.post(url, headers=headers)
    
    if response.status_code == 201:
        return response.json()['token']
    else:
        print(f"❌ Failed to get installation token: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def test_github_app(app_id, private_key_path, installation_id=None):
    """Test GitHub App configuration"""
    print("🔍 Testing GitHub App Configuration")
    print("=" * 50)
    
    # Step 1: Generate JWT token
    print("1. Generating JWT token...")
    jwt_token = generate_jwt_token(app_id, private_key_path)
    if not jwt_token:
        return False
    print("✅ JWT token generated successfully")
    
    # Step 2: Test JWT token
    print("\n2. Testing JWT token...")
    headers = {
        'Authorization': f'Bearer {jwt_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    response = requests.get('https://api.github.com/app', headers=headers)
    if response.status_code == 200:
        app_info = response.json()
        print(f"✅ GitHub App authenticated: {app_info['name']}")
        print(f"   App ID: {app_info['id']}")
        print(f"   Owner: {app_info['owner']['login']}")
    else:
        print(f"❌ JWT authentication failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Step 3: List installations
    print("\n3. Listing installations...")
    response = requests.get('https://api.github.com/app/installations', headers=headers)
    if response.status_code == 200:
        installations = response.json()
        print(f"✅ Found {len(installations)} installation(s)")
        
        for install in installations:
            print(f"   Installation ID: {install['id']}")
            print(f"   Account: {install['account']['login']}")
            print(f"   Type: {install['account']['type']}")
            
            # If no specific installation ID provided, use the first one
            if installation_id is None:
                installation_id = install['id']
                print(f"   Using installation ID: {installation_id}")
    else:
        print(f"❌ Failed to list installations: {response.status_code}")
        return False
    
    if not installation_id:
        print("❌ No installation ID available")
        return False
    
    # Step 4: Get installation token
    print(f"\n4. Getting installation token for ID {installation_id}...")
    install_token = get_installation_token(jwt_token, installation_id)
    if not install_token:
        return False
    print("✅ Installation token obtained")
    
    # Step 5: Test repository access
    print("\n5. Testing repository access...")
    headers = {
        'Authorization': f'token {install_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Test AppState repository access
    response = requests.get('https://api.github.com/repos/frontegg/AppState', headers=headers)
    if response.status_code == 200:
        repo_info = response.json()
        print(f"✅ AppState repository access: {repo_info['full_name']}")
        print(f"   Private: {repo_info['private']}")
        if 'permissions' in repo_info:
            print(f"   Permissions: {repo_info['permissions']}")
    else:
        print(f"❌ AppState repository access failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Step 6: Test file access
    print("\n6. Testing file access...")
    file_url = 'https://api.github.com/repos/frontegg/AppState/contents/applications/admins-service/production-global/values.yaml'
    response = requests.get(file_url, headers=headers)
    if response.status_code == 200:
        print("✅ File access successful")
        file_info = response.json()
        print(f"   File size: {file_info['size']} bytes")
    else:
        print(f"❌ File access failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    print("\n🎉 All tests passed! GitHub App is configured correctly.")
    return True

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test GitHub App configuration')
    parser.add_argument('--app-id', required=True, help='GitHub App ID')
    parser.add_argument('--private-key', required=True, help='Path to private key file')
    parser.add_argument('--installation-id', type=int, help='Installation ID (optional)')
    
    args = parser.parse_args()
    
    success = test_github_app(args.app_id, args.private_key, args.installation_id)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
