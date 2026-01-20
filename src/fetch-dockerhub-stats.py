#!/usr/bin/env python3
"""Fetch Docker Hub statistics for repositories"""

import dh_api
import json
import os
from datetime import datetime, UTC


def main():
    # Docker Hub namespace/owner to fetch repositories for
    namespace = "neonvariant"
    
    # Load existing stats if they exist
    old_stats = {}
    stats_file = 'data/dockerhub-stats.json'
    if os.path.exists(stats_file):
        with open(stats_file, 'r') as f:
            old_stats = json.load(f)
    
    requester = dh_api.DockerHubRestApi()
    
    # Get all repos for the namespace
    repos_data = requester.get_all_repos_for_namespace(namespace)
    repos = [f"{repo['namespace']}/{repo['name']}" for repo in repos_data]
    
    # Fetch stats for each repo
    new_repositories = {}
    sum_pulls = 0
    sum_stars = 0
    
    for repo in repos:
        print(f"Fetching stats for {repo}...")
        try:
            pull_count = requester.get_repo_pull_count(repo=repo)
            sum_pulls += pull_count
            star_count = requester.get_repo_star_count(repo=repo)
            sum_stars += star_count
            description = requester.get_repo_description(repo=repo)
            last_updated = requester.get_repo_last_updated(repo=repo)
            
            new_repositories[repo] = {
                "pull_count": pull_count,
                "star_count": star_count,
                "description": description,
                "last_updated": last_updated
            }
            print(f"  ✓ {repo}: {pull_count} pulls, {star_count} stars")
        except Exception as e:
            print(f"  ✗ Error fetching {repo}: {e}")
            new_repositories[repo] = {
                "error": str(e)
            }
    
    # Calculate totals
    totals = {
        "total_pulls": sum_pulls,
        "total_stars": sum_stars
    }
    
    print(f"\nTotal Pulls: {sum_pulls}, Total Stars: {sum_stars}")
    
    # Check if there are any actual changes to repository data
    old_repositories = old_stats.get("repositories", {})
    old_totals = old_stats.get("totals", {})
    has_changes = new_repositories != old_repositories or totals != old_totals
    
    # Only update timestamp if there are changes
    stats = {
        "last_updated": datetime.now(UTC).isoformat() if has_changes else old_stats.get("last_updated", datetime.now(UTC).isoformat()),
        "totals": totals,
        "repositories": new_repositories
    }
    
    # Write stats to json file
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    if has_changes:
        print(f"\nChanges detected! Stats saved to {stats_file}")
    else:
        print(f"\nNo changes detected. {stats_file} unchanged.")
    
    requester.close()


if __name__ == "__main__":
    main()
