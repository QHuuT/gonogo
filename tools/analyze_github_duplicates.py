#!/usr/bin/env python3
"""
Analyze duplicate user story IDs in GitHub issues
"""

import requests
import re
import os
from collections import defaultdict

def analyze_github_duplicates():
    # GitHub API setup
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("No GITHUB_TOKEN found, using public API (rate limited)")

    headers = {}
    if github_token:
        headers['Authorization'] = f'token {github_token}'

    # Fetch GitHub issues
    print("Fetching GitHub issues...")
    url = "https://api.github.com/repos/QHuuT/gonogo/issues"
    params = {'state': 'all', 'per_page': 100}

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print(f"Failed to fetch issues: {response.status_code}")
        return

    issues = response.json()
    print(f"Found {len(issues)} total GitHub issues")

    # Extract user story IDs
    user_story_counts = defaultdict(list)
    user_story_pattern = r'\bUS-(\d+)\b'

    for issue in issues:
        title = issue.get('title', '')
        body = issue.get('body', '') or ''

        # Look for US-XXXXX patterns in title and body
        matches = re.findall(user_story_pattern, title + ' ' + body)

        for match in matches:
            us_id = f"US-{match.zfill(5)}"
            user_story_counts[us_id].append({
                'issue_number': issue['number'],
                'title': title,
                'state': issue['state']
            })

    # Find duplicates
    print(f"\n=== User Story ID Analysis ===")
    print(f"Total unique user story IDs found: {len(user_story_counts)}")

    duplicates = {us_id: issues for us_id, issues in user_story_counts.items() if len(issues) > 1}

    if duplicates:
        print(f"\nFound {len(duplicates)} duplicate user story IDs:")
        for us_id, issue_list in duplicates.items():
            print(f"\n{us_id}:")
            for issue_info in issue_list:
                print(f"  #{issue_info['issue_number']}: {issue_info['title']} ({issue_info['state']})")
    else:
        print("No duplicate user story IDs found")

    # Count by ID pattern
    id_patterns = defaultdict(int)
    for us_id in user_story_counts.keys():
        if 'US-0000' in us_id:
            id_patterns['US-0000X (single digit)'] += 1
        elif 'US-000' in us_id:
            id_patterns['US-000XX (double digit)'] += 1
        else:
            id_patterns['Other patterns'] += 1

    print(f"\n=== ID Pattern Distribution ===")
    for pattern, count in id_patterns.items():
        print(f"{pattern}: {count}")

if __name__ == "__main__":
    analyze_github_duplicates()