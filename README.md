# dev-stats

Automated tracking of statistics for my Docker Hub images and GitHub repositories.

## Overview

This repository fetches statistics from Docker Hub and GitHub every 6 hours via GitHub Actions and stores them in JSON files. The data is consumed by [chase-roohms.github.io](https://github.com/chase-roohms/chase-roohms.github.io/blob/bc7fab9eca0da81eac0deaeb2ae439d28ac4b5e4/src/utils/projectStats.ts#L58C1-L58C111) to display project metrics.

## Features

- **Docker Hub Stats**: Automatically fetches all repositories for a specified namespace
  - Pull counts
  - Star counts
  - Repository descriptions
  - Last updated timestamps
  
- **GitHub Stats**: Automatically fetches all repositories for a user
  - Star counts
  - Fork counts
  - Watcher counts
  - Open issues counts

## Project Structure

```
docker-stats/
├── src/
│   ├── fetch-dockerhub-stats.py  # Fetch Docker Hub statistics
│   ├── fetch-github-stats.py     # Fetch GitHub statistics
│   ├── dh_api/                   # Docker Hub API module
│   │   ├── __init__.py
│   │   └── dh_rest.py
│   └── gh_api/                   # GitHub API module
│       ├── __init__.py
│       └── gh_rest.py
├── data/
│   ├── dockerhub-stats.json      # Docker Hub statistics output
│   └── github-stats.json         # GitHub statistics output
├── fetch_stats.py                # Legacy Docker Hub stats script
└── requirements.txt
```

## Usage

### Docker Hub Statistics

Fetches all repositories for the configured namespace:

```bash
pip install -r requirements.txt
cd src
python fetch-dockerhub-stats.py
```

Configure the namespace in `src/fetch-dockerhub-stats.py`:
```python
namespace = "neonvariant"  # Change to your Docker Hub namespace
```

### GitHub Statistics

Fetches all repositories for the configured user:

```bash
pip install -r requirements.txt
cd src
python fetch-github-stats.py
```

Configure the owner in `src/fetch-github-stats.py`:
```python
requester = gh_api.GitHubRestApi(owner="chase-roohms")
```

### Automated Updates

Both scripts run every 6 hours via GitHub Actions to keep statistics current.

## Output Format

### Docker Hub Stats (`data/dockerhub-stats.json`)

```json
{
  "last_updated": "2026-01-20T12:00:00Z",
  "totals": {
    "total_pulls": 5000,
    "total_stars": 25
  },
  "repositories": {
    "neonvariant/mythicmate": {
      "pull_count": 3000,
      "star_count": 15,
      "description": "Repository description",
      "last_updated": "2026-01-20T10:00:00Z"
    }
  }
}
```

### GitHub Stats (`data/github-stats.json`)

```json
{
  "last_updated": "2026-01-20T12:00:00Z",
  "totals": {
    "total_stars": 100,
    "total_forks": 20,
    "total_watchers": 50,
    "total_open_issues": 5
  },
  "repositories": {
    "docker-stats": {
      "stars": 10,
      "forks": 2,
      "watchers": 5,
      "open_issues": 1,
      "description": "Repository description"
    }
  }
}
```

## API Modules

Both API modules feature:
- Rate limiting with automatic backoff
- Request retry logic with exponential backoff
- Repository data caching (5-minute TTL)
- Context manager support for proper session cleanup
- Comprehensive logging
