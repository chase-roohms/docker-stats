#!/usr/bin/env python3
"""Fetch Docker Hub statistics for repositories listed in dockerhub-repos.yml"""

import yaml
import json
import requests
from datetime import datetime, UTC
import os


def main():
    # Read repos from yaml file
    with open('dockerhub-repos.yml', 'r') as f:
        repos = yaml.safe_load(f)
    
    # Load existing stats if they exist
    old_stats = {}
    if os.path.exists('stats.json'):
        with open('stats.json', 'r') as f:
            old_stats = json.load(f)
    
    # Fetch stats for each repo
    new_repositories = {}
    
    for repo in repos:
        print(f"Fetching stats for {repo}...")
        try:
            # Docker Hub API v2
            url = f"https://hub.docker.com/v2/repositories/{repo}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            new_repositories[repo] = {
                "pull_count": data.get("pull_count", 0),
                "description": data.get("description", ""),
                "last_updated": data.get("last_updated", "")
            }
            print(f"  ✓ {repo}: {data.get('pull_count', 0)} pulls")
        except Exception as e:
            print(f"  ✗ Error fetching {repo}: {e}")
            new_repositories[repo] = {
                "error": str(e)
            }
    
    # Check if there are any actual changes to repository data
    old_repositories = old_stats.get("repositories", {})
    has_changes = new_repositories != old_repositories
    
    # Only update timestamp if there are changes
    stats = {
        "last_updated": datetime.now(UTC).isoformat() if has_changes else old_stats.get("last_updated", datetime.now(UTC).isoformat()),
        "repositories": new_repositories
    }
    
    # Write stats to json file
    with open('stats.json', 'w') as f:
        json.dump(stats, f, indent=2)
    
    if has_changes:
        print("\nChanges detected! Stats saved to stats.json")
    else:
        print("\nNo changes detected. stats.json unchanged.")


if __name__ == "__main__":
    main()
