# dev-stats

Automated tracking of statistics for my Docker Hub images, GitHub repositories, and blog analytics.

## Overview

This repository fetches statistics from Docker Hub, GitHub, and Google Analytics every 6 hours via GitHub Actions and stores them in JSON files. The data is consumed by [chase-roohms.github.io](https://github.com/chase-roohms/chase-roohms.github.io/blob/bc7fab9eca0da81eac0deaeb2ae439d28ac4b5e4/src/utils/projectStats.ts#L58C1-L58C111) to display project metrics.

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

- **Google Analytics Stats**: Fetches page view statistics for blog posts
  - Total page views per blog post
  - All-time statistics
  - Historical tracking

## Project Structure

```
dev-stats/
├── src/
│   ├── fetch-dockerhub-stats.py      # Fetch Docker Hub statistics
│   ├── fetch-github-stats.py         # Fetch GitHub statistics
│   ├── fetch-google-analytics-stats.py # Fetch Google Analytics statistics
│   ├── dh_api/                       # Docker Hub API module
│   │   ├── __init__.py
│   │   └── dh_rest.py
│   ├── gh_api/                       # GitHub API module
│   │   ├── __init__.py
│   │   └── gh_rest.py
│   └── ga_api/                       # Google Analytics API module
│       ├── __init__.py
│       └── ga_rest.py
├── data/
│   ├── dockerhub-stats.json          # Docker Hub statistics output
│   ├── github-stats.json             # GitHub statistics output
│   └── google-analytics-stats.json   # Google Analytics statistics output
├── fetch_stats.py                    # Legacy Docker Hub stats script
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

ConfGoogle Analytics Statistics

Fetches page view statistics for blog posts:

```bash
pip install -r requirements.txt
cd src
python fetch-google-analytics-stats.py
```

**Configuration via environment variables:**

```bash
# Required: Your GA4 Property ID
export GA4_PROPERTY_ID="123456789"

# For local development: Path to service account credentials JSON file
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"

# For GitHub Actions: Service account credentials as JSON string
export GOOGLE_CREDENTIALS_JSON='{"type":"service_account","project_id":"..."}'

# Optional: Blog path prefix (default: "/blog/")
export BLOG_PATH_PREFIX="/blog/"
```

**Setting up Google Analytics API access:**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Analytics Data API
4. Create a service account:
   - Go to "IAM & Admin" > "Service Accounts"
   - Click "Create Service Account"
   - Grant it the "Viewer" role
   - Create and download a JSON key file
5. Add the service account email to your Google Analytics property:
   - Go to Google Analytics Admin
   - Select your property
   - Go to "Property Access Management"
   - Add the service account email with "Viewer" permissions

**For GitHub Actions (Recommended - Workload Identity Federation):**

This is the most secure method as it doesn't require storing service account keys.

1. **Set up Workload Identity Federation in Google Cloud:**
   ```bash
   # Set variables
   PROJECT_ID="your-project-id"
   PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)")
   SERVICE_ACCOUNT="analytics-reader@${PROJECT_ID}.iam.gserviceaccount.com"
   WORKLOAD_IDENTITY_POOL="github-pool"
   WORKLOAD_IDENTITY_PROVIDER="github-provider"
   REPO="chase-roohms/dev-stats"  # Your GitHub repo
   
   echo "Project ID: ${PROJECT_ID}"
   echo "Project Number: ${PROJECT_NUMBER}"
   
   # Enable required APIs
   gcloud services enable iamcredentials.googleapis.com --project="${PROJECT_ID}"
   gcloud services enable analyticsdata.googleapis.com --project="${PROJECT_ID}"
   
   # Create Workload Identity Pool
   gcloud iam workload-identity-pools create "${WORKLOAD_IDENTITY_POOL}" \
     --project="${PROJECT_ID}" \
     --location="global" \
     --display-name="GitHub Actions Pool"
   
   # Create Workload Identity Provider
   gcloud iam workload-identity-pools providers create-oidc "${WORKLOAD_IDENTITY_PROVIDER}" \
     --project="${PROJECT_ID}" \
     --location="global" \
     --workload-identity-pool="${WORKLOAD_IDENTITY_POOL}" \
     --display-name="GitHub Provider" \
     --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
     --attribute-condition="assertion.repository == 'chase-roohms/dev-stats'" \
     --issuer-uri="https://token.actions.githubusercontent.com"
   
   # Allow the GitHub repo to impersonate the service account
   gcloud iam service-accounts add-iam-policy-binding "${SERVICE_ACCOUNT}" \
     --project="${PROJECT_ID}" \
     --role="roles/iam.workloadIdentityUser" \
     --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${WORKLOAD_IDENTITY_POOL}/attribute.repository/${REPO}"
   ```

2. **Add GitHub repository secrets:**
   - Go to your GitHub repository settings
   - Navigate to "Secrets and variables" > "Actions"
   - Create these repository secrets:
     - `GA4_PROPERTY_ID`: Your GA4 property ID (e.g., "516541379")
     - `GCP_WORKLOAD_IDENTITY_PROVIDER`: Full provider name (e.g., `projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider`)
     - `GCP_SERVICE_ACCOUNT`: Service account email (e.g., `analytics-reader@PROJECT_ID.iam.gserviceaccount.com`)

3. **The workflow will authenticate automatically** - see [.github/workflows/get-stats.yml](.github/workflows/get-stats.yml) for the implementation

**Alternative: Using Service Account Keys (Less Secure):**

If you can't use Workload Identity Federation:

1. Copy the entire contents of your service account JSON file
2. Go to your GitHub repository settings
3. Navigate to "Secrets and variables" > "Actions"
4. Create these repository secrets:
   - `GA4_PROPERTY_ID`: Your GA4 property ID
   - `GOOGLE_CREDENTIALS_JSON`: Paste the entire JSON file contents

### Automated Updates

Allester = gh_api.GitHubRestApi(owner="chase-roohms")
```

### Automated Updates

Both scripts run every 6 hours via GitHub Actions to keep statistics current.

### Google Analytics Stats (`data/google-analytics-stats.json`)

```json
{
  "last_updated": "2026-01-30T12:00:00Z",
  "property_id": "516541379",
  "blog_path_prefix": "/blog/",
  "totals": {
    "total_blog_posts": 25,
    "total_page_views": 50000
  },
  "blog_posts": {
    "/blog/my-first-post/": {
      "page_views": 5000,
      "last_fetched": "2026-01-30T12:00:00Z"
    }
  }
}
```

## API Modules

All three API modules feature:
- Rate limiting with automatic backoff
- Request retry logic with exponential backoff (GitHub/Docker Hub)
- Data caching (5-minute TTL)
- Comprehensive logging

The Google Analytics module uses the official `google-analytics-data` Python client library.
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
    "dev-stats": {
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
