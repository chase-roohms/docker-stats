#!/usr/bin/env python3
"""Fetch Google Analytics statistics for blog posts"""

import ga_api
import json
import os
from datetime import datetime, UTC


def main():
    # Configuration
    # TODO: Replace with your GA4 property ID
    property_id = os.environ.get("GA4_PROPERTY_ID", "YOUR_PROPERTY_ID")
    
    # Credentials: supports both file path (local) and JSON string (CI/CD)
    credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", None)
    credentials_json = os.environ.get("GOOGLE_CREDENTIALS_JSON", None)
    
    # Blog path prefix (adjust based on your blog structure)
    blog_path_prefix = os.environ.get("BLOG_PATH_PREFIX", "/blog/")
    
    # Load existing stats if they exist
    old_stats = {}
    stats_file = 'data/google-analytics-stats.json'
    if os.path.exists(stats_file):
        with open(stats_file, 'r') as f:
            old_stats = json.load(f)
    
    print(f"Connecting to Google Analytics property: {property_id}")
    requester = ga_api.GoogleAnalyticsApi(
        property_id=property_id,
        credentials_path=credentials_path,
        credentials_json=credentials_json
    )
    
    # Fetch page views for all blog posts
    print(f"Fetching page views for blog posts with prefix '{blog_path_prefix}'...")
    blog_views = requester.get_blog_post_views(blog_path_prefix=blog_path_prefix)
    
    # Build new stats structure
    new_blog_posts = {}
    total_views = 0
    
    for page_path, views in sorted(blog_views.items(), key=lambda x: x[1], reverse=True):
        print(f"  ✓ {page_path}: {views:,} views")
        total_views += views
        
        new_blog_posts[page_path] = {
            "page_views": views,
            "last_fetched": datetime.now(UTC).isoformat()
        }
    
    # Build the complete stats object
    new_stats = {
        "last_updated": datetime.now(UTC).isoformat(),
        "property_id": property_id,
        "blog_path_prefix": blog_path_prefix,
        "totals": {
            "total_blog_posts": len(blog_views),
            "total_page_views": total_views
        },
        "blog_posts": new_blog_posts
    }
    
    # Add history tracking
    if old_stats and "history" in old_stats:
        history = old_stats["history"]
    else:
        history = []
    
    # Add current snapshot to history
    history.append({
        "timestamp": new_stats["last_updated"],
        "total_blog_posts": new_stats["totals"]["total_blog_posts"],
        "total_page_views": new_stats["totals"]["total_page_views"]
    })
    
    # Keep only last 100 history entries
    new_stats["history"] = history[-100:]
    
    # Save stats to file
    os.makedirs(os.path.dirname(stats_file), exist_ok=True)
    with open(stats_file, 'w') as f:
        json.dump(new_stats, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Total blog posts: {new_stats['totals']['total_blog_posts']}")
    print(f"  Total page views: {new_stats['totals']['total_page_views']:,}")
    print(f"{'='*60}")
    print(f"\nStats saved to {stats_file}")
    
    # Show changes if old stats exist
    if old_stats and "totals" in old_stats:
        old_total_views = old_stats["totals"].get("total_page_views", 0)
        old_total_posts = old_stats["totals"].get("total_blog_posts", 0)
        
        views_diff = new_stats["totals"]["total_page_views"] - old_total_views
        posts_diff = new_stats["totals"]["total_blog_posts"] - old_total_posts
        
        print(f"\nChanges since last update:")
        print(f"  Page views: {views_diff:+,}")
        print(f"  Blog posts: {posts_diff:+,}")


if __name__ == "__main__":
    main()
