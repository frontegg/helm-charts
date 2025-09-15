#!/usr/bin/env python3
"""
Query AppState repository for production versions of microservices.
"""

import json
import requests
import sys
import os
import argparse
import base64
import yaml
import re
from pathlib import Path


def get_appstate_version(service_name, token, repo='frontegg/AppState', verbose=False):
    """Query AppState repo for production version of a service"""
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # AppState repo structure: applications/{service-name}/production-global/values.yaml
    possible_paths = [
        f'applications/{service_name}/production-global/values.yaml',
        f'applications/{service_name}/production-global/values.yml'
    ]
    
    for path in possible_paths:
        url = f'https://api.github.com/repos/{repo}/contents/{path}'
        if verbose:
            print(f"    Trying path: {path}")
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if verbose:
                print(f"    Response status: {response.status_code}")
            
            if response.status_code == 401:
                if verbose:
                    print(f"    ❌ Authentication failed - check GitHub token permissions")
                continue
            elif response.status_code == 403:
                if verbose:
                    print(f"    ❌ Access forbidden - token may not have repository access")
                continue
            elif response.status_code == 404:
                if verbose:
                    print(f"    ❌ Path not found: {path}")
                continue
            elif response.status_code == 200:
                content = response.json()
                if content.get('type') == 'file':
                    # Decode base64 content
                    file_content = base64.b64decode(content['content']).decode('utf-8')
                    
                    if verbose:
                        print(f"    Found file at {path}, content length: {len(file_content)}")
                        print(f"    First 200 chars: {file_content[:200]}...")
                    
                    # Try to extract version from YAML content
                    try:
                        yaml_content = yaml.safe_load(file_content)
                        # Look for common version fields
                        version_fields = ['version', 'appVersion', 'tag', 'image_tag', 'imageTag']
                        
                        if isinstance(yaml_content, dict):
                            if verbose:
                                print(f"    YAML keys: {list(yaml_content.keys())}")
                            # Direct fields
                            for field in version_fields:
                                if field in yaml_content:
                                    if verbose:
                                        print(f"    Found {field}: {yaml_content[field]}")
                                    return str(yaml_content[field])
                            
                            # Nested structures
                            for key, value in yaml_content.items():
                                if isinstance(value, dict):
                                    for field in version_fields:
                                        if field in value:
                                            return str(value[field])
                                    
                                    # Check for image field with tag
                                    if 'image' in value and isinstance(value['image'], str):
                                        # Extract tag from image string like "repo:tag"
                                        if ':' in value['image']:
                                            tag = value['image'].split(':')[-1]
                                            if tag and tag != 'latest':
                                                return tag
                        
                    except yaml.YAMLError:
                        # If not YAML, try to extract version with regex
                        version_patterns = [
                            r'(?:version|tag|appVersion|imageTag):\s*([a-f0-9]{7,}|\d+\.\d+\.\d+)',
                            r'(?:version|tag|appVersion|imageTag):\s*"([^"]+)"',
                            r'(?:version|tag|appVersion|imageTag):\s*\'([^\']+)\'',
                            r'image:\s*[^:]+:([a-f0-9]{7,}|\d+\.\d+\.\d+)',
                        ]
                        
                        for pattern in version_patterns:
                            match = re.search(pattern, file_content, re.IGNORECASE)
                            if match:
                                return match.group(1)
                    
                    return f"found-in-{path}"
        except Exception as e:
            if verbose:
                print(f"    Error accessing {path}: {str(e)}")
            continue
    
    return None


def test_repository_access(repo, token, verbose=False):
    """Test if we can access the AppState repository"""
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    url = f'https://api.github.com/repos/{repo}'
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            if verbose:
                repo_info = response.json()
                print(f"✅ Repository access OK: {repo_info.get('full_name')} (private: {repo_info.get('private')})")
            return True
        elif response.status_code == 401:
            print(f"❌ Authentication failed for {repo}. Check your GitHub token.")
            return False
        elif response.status_code == 403:
            print(f"❌ Access forbidden to {repo}. Token may not have repository access.")
            return False
        elif response.status_code == 404:
            print(f"❌ Repository {repo} not found or not accessible.")
            return False
        else:
            print(f"❌ Unexpected response {response.status_code} accessing {repo}")
            return False
    except Exception as e:
        print(f"❌ Error accessing repository {repo}: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Query AppState repository for production versions')
    parser.add_argument('--services-file', 
                       default='all_services.json',
                       help='JSON file containing services to query')
    parser.add_argument('--output', 
                       default='appstate_versions.json',
                       help='Output file for AppState versions')
    parser.add_argument('--token', 
                       help='GitHub token (can also use GITHUB_TOKEN env var)')
    parser.add_argument('--repo', 
                       default='frontegg/AppState',
                       help='AppState repository (default: frontegg/AppState)')
    parser.add_argument('--verbose', '-v', 
                       action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Get GitHub token
    token = args.token or os.environ.get('GITHUB_TOKEN')
    if not token:
        print("Error: GitHub token required. Use --token or set GITHUB_TOKEN environment variable", file=sys.stderr)
        return 1
    
    try:
        # Load services
        if not Path(args.services_file).exists():
            print(f"Error: Services file not found: {args.services_file}", file=sys.stderr)
            return 1
        
        with open(args.services_file, 'r') as f:
            services = json.load(f)
        
        if args.verbose:
            print(f"Loaded {len(services)} services from {args.services_file}")
            print(f"Querying AppState repository: {args.repo}")
        
        # Test repository access first
        if not test_repository_access(args.repo, token, args.verbose):
            print("\n❌ Cannot access AppState repository. Please check:")
            print("  1. GitHub token is valid and not expired")
            print("  2. Token has access to the frontegg/AppState repository")
            print("  3. Repository name is correct")
            return 1
        
        appstate_versions = {}
        
        print("Querying AppState repository for production versions...")
        
        for service in services:
            service_name = service['service_name']
            repository = service['repository']
            
            if args.verbose:
                print(f"Querying {service_name} (repo: {repository})...")
            
            # Try repository name first (more likely to match), then service name
            version = get_appstate_version(repository, token, args.repo, args.verbose)
            if not version and repository != service_name:
                if args.verbose:
                    print(f"    Trying with service name: {service_name}")
                version = get_appstate_version(service_name, token, args.repo, args.verbose)
            
            appstate_versions[service_name] = {
                'version': version,
                'repository': repository,
                'helm_version': service['app_version'],
                'chart': service['chart']
            }
            
            if version:
                if args.verbose:
                    print(f"  ✓ Found version: {version}")
                else:
                    print(f"  {service_name}: {version}")
            else:
                if args.verbose:
                    print(f"  ✗ No version found in AppState")
                else:
                    print(f"  {service_name}: NOT FOUND")
        
        # Save results
        with open(args.output, 'w') as f:
            json.dump(appstate_versions, f, indent=2)
        
        if args.verbose:
            print(f"\nResults saved to: {args.output}")
        
        # Output for GitHub Actions (if running in CI)
        if 'GITHUB_ACTIONS' in os.environ:
            github_output = os.environ.get('GITHUB_OUTPUT')
            if github_output:
                versions_json = json.dumps(appstate_versions)
                with open(github_output, 'a') as f:
                    f.write(f"versions={versions_json}\n")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
