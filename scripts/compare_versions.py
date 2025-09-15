#!/usr/bin/env python3
"""
Compare Helm versions with AppState production versions and generate summary.
"""

import json
import sys
import argparse
from datetime import datetime
from pathlib import Path


def generate_summary(updates_needed, up_to_date, no_appstate_version):
    """Generate markdown summary of version comparison"""
    summary_lines = [
        "## Microservices Version Comparison",
        f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        "",
        f"### Summary",
        f"- 🔄 **{len(updates_needed)}** services need updates",
        f"- ✅ **{len(up_to_date)}** services are up to date", 
        f"- ⚠️ **{len(no_appstate_version)}** services have no AppState version",
        ""
    ]
    
    if updates_needed:
        summary_lines.extend([
            "### 🔄 Services Needing Updates",
            "| Service | Chart | Helm Version | AppState Version |",
            "|---------|-------|--------------|------------------|"
        ])
        for update in updates_needed:
            summary_lines.append(f"| {update['service']} | {update['chart']} | `{update['helm_version']}` | `{update['appstate_version']}` |")
        summary_lines.append("")
    
    if up_to_date:
        summary_lines.extend([
            "### ✅ Up to Date Services",
            "| Service | Chart | Version |",
            "|---------|-------|---------|"
        ])
        for service in up_to_date:
            summary_lines.append(f"| {service['service']} | {service['chart']} | `{service['version']}` |")
        summary_lines.append("")
    
    if no_appstate_version:
        summary_lines.extend([
            "### ⚠️ Services Without AppState Version",
            "| Service | Chart | Helm Version |",
            "|---------|-------|--------------|"
        ])
        for service in no_appstate_version:
            summary_lines.append(f"| {service['service']} | {service['chart']} | `{service['helm_version']}` |")
    
    return "\n".join(summary_lines)


def main():
    parser = argparse.ArgumentParser(description='Compare Helm and AppState versions')
    parser.add_argument('--services-file', 
                       default='all_services.json',
                       help='JSON file containing services')
    parser.add_argument('--appstate-file', 
                       default='appstate_versions.json',
                       help='JSON file containing AppState versions')
    parser.add_argument('--output', 
                       default='comparison_results.json',
                       help='Output file for comparison results')
    parser.add_argument('--summary-file', 
                       help='Optional file to save markdown summary')
    parser.add_argument('--verbose', '-v', 
                       action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    try:
        # Load data
        if not Path(args.services_file).exists():
            print(f"Error: Services file not found: {args.services_file}", file=sys.stderr)
            return 1
        
        if not Path(args.appstate_file).exists():
            print(f"Error: AppState versions file not found: {args.appstate_file}", file=sys.stderr)
            return 1
        
        with open(args.services_file, 'r') as f:
            services = json.load(f)
        
        with open(args.appstate_file, 'r') as f:
            appstate_versions = json.load(f)
        
        updates_needed = []
        no_appstate_version = []
        up_to_date = []
        
        print("=== VERSION COMPARISON SUMMARY ===")
        print(f"Generated at: {datetime.utcnow().isoformat()}Z")
        print()
        
        for service in services:
            service_name = service['service_name']
            helm_version = service['app_version']
            chart = service['chart']
            
            appstate_info = appstate_versions.get(service_name, {})
            appstate_version = appstate_info.get('version')
            
            if not appstate_version or appstate_version.startswith('found-in-'):
                no_appstate_version.append({
                    'service': service_name,
                    'chart': chart,
                    'helm_version': helm_version,
                    'reason': 'No version found in AppState' if not appstate_version else f'Found but no version extracted ({appstate_version})'
                })
            elif appstate_version != helm_version:
                updates_needed.append({
                    'service': service_name,
                    'chart': chart,
                    'helm_version': helm_version,
                    'appstate_version': appstate_version,
                    'action': 'update_needed'
                })
            else:
                up_to_date.append({
                    'service': service_name,
                    'chart': chart,
                    'version': helm_version
                })
        
        # Print summary
        print(f"📊 SUMMARY:")
        print(f"  • Services needing updates: {len(updates_needed)}")
        print(f"  • Services up to date: {len(up_to_date)}")
        print(f"  • Services without AppState version: {len(no_appstate_version)}")
        print()
        
        if updates_needed:
            print("🔄 SERVICES NEEDING UPDATES:")
            for update in updates_needed:
                print(f"  • {update['service']} ({update['chart']})")
                print(f"    Helm: {update['helm_version']} → AppState: {update['appstate_version']}")
            print()
        
        if args.verbose and up_to_date:
            print("✅ UP TO DATE SERVICES:")
            for service in up_to_date:
                print(f"  • {service['service']} ({service['chart']}): {service['version']}")
            print()
        
        if no_appstate_version:
            print("⚠️  SERVICES WITHOUT APPSTATE VERSION:")
            for service in no_appstate_version:
                print(f"  • {service['service']} ({service['chart']}): {service['helm_version']}")
                if args.verbose:
                    print(f"    Reason: {service['reason']}")
            print()
        
        # Generate summary
        summary = generate_summary(updates_needed, up_to_date, no_appstate_version)
        
        # Save results
        results = {
            'updates_needed': updates_needed,
            'up_to_date': up_to_date,
            'no_appstate_version': no_appstate_version,
            'summary': summary,
            'has_updates': len(updates_needed) > 0,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        
        if args.summary_file:
            with open(args.summary_file, 'w') as f:
                f.write(summary)
        
        if args.verbose:
            print(f"Results saved to: {args.output}")
            if args.summary_file:
                print(f"Summary saved to: {args.summary_file}")
        
        # Output for GitHub Actions (if running in CI)
        if 'GITHUB_ACTIONS' in os.environ:
            github_output = os.environ.get('GITHUB_OUTPUT')
            if github_output:
                has_updates = "true" if len(updates_needed) > 0 else "false"
                with open(github_output, 'a') as f:
                    f.write(f"has-updates={has_updates}\n")
                    f.write(f"updates-needed={json.dumps(updates_needed)}\n")
                    # Handle multiline summary for GitHub Actions
                    summary_escaped = summary.replace('\n', '%0A').replace('\r', '%0D')
                    f.write(f"summary={summary_escaped}\n")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    import os
    sys.exit(main())
