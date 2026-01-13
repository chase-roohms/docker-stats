#!/usr/bin/env python3
"""Fetch Docker Hub statistics for repositories listed in dockerhub-repos.yml"""

import yaml
import json
import requests
from datetime import datetime, UTC


def main():
    # Read repos from yaml file
    with open('dockerhub-repos.yml', 'r') as f:
        repos = yaml.safe_load(f)
    
    # Fetch stats for each repo
    stats = {
        "last_updated": datetime.now(UTC).isoformat(),
        "repositories": {}
    }
    
    for repo in repos:
        print(f"Fetching stats for {repo}...")
        try:
            # Docker Hub API v2
            url = f"https://hub.docker.com/v2/repositories/{repo}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            stats["repositories"][repo] = {
                "pull_count": data.get("pull_count", 0),
                "description": data.get("description", ""),
                "last_updated": data.get("last_updated", "")
            }
            print(f"  ✓ {repo}: {data.get('pull_count', 0)} pulls")
        except Exception as e:
            print(f"  ✗ Error fetching {repo}: {e}")
            stats["repositories"][repo] = {
                "error": str(e)
            }
    
    # Write stats to json file
    with open('stats.json', 'w') as f:
        json.dump(stats, f, indent=2)
    
    print("\nStats saved to stats.json")


if __name__ == "__main__":
    main()
