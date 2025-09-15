#!/usr/bin/env python3
"""
Extract microservices and their versions from Helm values files.
"""

import yaml
import json
import sys
import argparse
from pathlib import Path


def extract_services_from_core_values(file_path, chart_name):
    """Extract services from frontegg-core-services values.yaml"""
    with open(file_path, 'r') as f:
        values = yaml.safe_load(f)
    
    services = []
    
    # Skip non-service entries
    skip_keys = {'global', 'debezium', 'initDbJob', 'environmentSetupJob', 'configCenter'}
    
    for key, value in values.items():
        if key in skip_keys or not isinstance(value, dict):
            continue
        
        if 'appVersion' in value and 'name' in value:
            service_info = {
                'chart': chart_name,
                'service_key': key,
                'service_name': value['name'],
                'app_version': value['appVersion'],
                'repository': value.get('image', {}).get('repository', '').replace('frontegg/', '') if 'image' in value else key
            }
            services.append(service_info)
    
    return services


def extract_services_from_dashboard_values(file_path, chart_name):
    """Extract services from frontegg-dashboard values.yaml"""
    with open(file_path, 'r') as f:
        values = yaml.safe_load(f)
    
    services = []
    
    # For dashboard, we have a different structure
    if 'dashboard' in values and 'appVersion' in values['dashboard']:
        service_info = {
            'chart': chart_name,
            'service_key': 'dashboard',
            'service_name': values['dashboard']['name'],
            'app_version': values['dashboard']['appVersion'],
            'repository': values['dashboard'].get('image', {}).get('repository', '').replace('frontegg/', '') if 'image' in values['dashboard'] else 'dashboard'
        }
        services.append(service_info)
    
    return services


def main():
    parser = argparse.ArgumentParser(description='Extract microservices from Helm values files')
    parser.add_argument('--core-services', 
                       default='charts/frontegg-core-services/values.yaml',
                       help='Path to frontegg-core-services values.yaml')
    parser.add_argument('--dashboard', 
                       default='charts/frontegg-dashboard/values.yaml',
                       help='Path to frontegg-dashboard values.yaml')
    parser.add_argument('--output-dir', 
                       default='.',
                       help='Output directory for JSON files')
    parser.add_argument('--verbose', '-v', 
                       action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    try:
        # Extract core services
        if Path(args.core_services).exists():
            core_services = extract_services_from_core_values(args.core_services, 'frontegg-core-services')
            if args.verbose:
                print(f"Extracted {len(core_services)} services from core-services")
        else:
            print(f"Warning: Core services file not found: {args.core_services}")
            core_services = []
        
        # Extract dashboard services
        if Path(args.dashboard).exists():
            dashboard_services = extract_services_from_dashboard_values(args.dashboard, 'frontegg-dashboard')
            if args.verbose:
                print(f"Extracted {len(dashboard_services)} services from dashboard")
        else:
            print(f"Warning: Dashboard file not found: {args.dashboard}")
            dashboard_services = []
        
        # Combine all services
        all_services = core_services + dashboard_services
        
        if args.verbose:
            print(f"\nTotal services found: {len(all_services)}")
            for service in all_services:
                print(f"  - {service['service_name']} ({service['chart']}): {service['app_version']}")
        
        # Save to files
        core_file = output_dir / 'core_services.json'
        dashboard_file = output_dir / 'dashboard_services.json'
        all_file = output_dir / 'all_services.json'
        
        with open(core_file, 'w') as f:
            json.dump(core_services, f, indent=2)
        
        with open(dashboard_file, 'w') as f:
            json.dump(dashboard_services, f, indent=2)
        
        with open(all_file, 'w') as f:
            json.dump(all_services, f, indent=2)
        
        if args.verbose:
            print(f"\nOutput files created:")
            print(f"  - {core_file}")
            print(f"  - {dashboard_file}")
            print(f"  - {all_file}")
        
        # Output for GitHub Actions (if running in CI)
        if 'GITHUB_ACTIONS' in os.environ:
            github_output = os.environ.get('GITHUB_OUTPUT')
            if github_output:
                with open(github_output, 'a') as f:
                    f.write(f"all-services={json.dumps(all_services)}\n")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    import os
    sys.exit(main())
