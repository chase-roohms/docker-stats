# docker-stats

Automated tracking of Docker Hub pull counts for published container images.

## Overview

This repository fetches download statistics from Docker Hub every 6 hours via GitHub Actions and stores them in `stats.json`. The data is consumed by [chase-roohms.github.io](https://github.com/chase-roohms/chase-roohms.github.io/blob/bc7fab9eca0da81eac0deaeb2ae439d28ac4b5e4/src/utils/projectStats.ts#L58C1-L58C111) to display project metrics.

## Tracked Repositories

Repositories are defined in `dockerhub-repos.yml`:
- neonvariant/mythicmate
- neonvariant/dumpsterr

## Usage

Manual update:
```bash
pip install -r requirements.txt
python fetch_stats.py
```

Automated updates run every 6 hours via GitHub Actions.

## Output Format

Stats are stored in `stats.json`:
```json
{
  "last_updated": "2026-01-13T12:00:00Z",
  "repositories": {
    "neonvariant/mythicmate": {
      "pull_count": 1234,
      "description": "...",
      "last_updated": "..."
    }
  }
}
```
