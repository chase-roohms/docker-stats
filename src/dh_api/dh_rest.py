import requests
import json
import time
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class DockerHubRestApi:
    """
    A wrapper for the Docker Hub REST API with built-in rate limiting support.
    Caches repository data to minimize API calls.
    
    Args:
        base_url: Base URL for Docker Hub API (default: https://hub.docker.com)
        cache_timeout_sec: Cache timeout in seconds (default: 300)
    """
    
    def __init__(self, base_url: str = "https://hub.docker.com", cache_timeout_sec: int = 300):
        """Initialize the Docker Hub API client with session and default headers."""
        self.base_url = base_url.rstrip('/')
        self.cache_timeout_sec = cache_timeout_sec
        # Cache for repository data to minimize API calls
        self.cached_repositories = {}
        
        # Create persistent session for connection pooling
        self.session = requests.Session()
        
        # Set default headers
        headers = {
            'Accept': 'application/json',
        }
        self.session.headers.update(headers)
        
        # Rate limiting tracking
        self.last_request_time = 0
        self.min_sleep_time = 0.5  # Minimum 0.5s between requests
        
        logger.info(f"Initialized Docker Hub API client for base URL: {self.base_url}")
    
    def _sleep_between_requests(self) -> None:
        """Ensure minimum time between requests (0.5 seconds)."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_sleep_time:
            sleep_time = self.min_sleep_time - elapsed
            logger.debug(f"Sleeping for {sleep_time:.2f}s to maintain rate limit")
            time.sleep(sleep_time)
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> requests.Response:
        """
        Make a request to the Docker Hub API with rate limiting and retry logic.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint (e.g., '/v2/repositories/owner/repo')
            params: Query parameters
            data: Request body data
            max_retries: Maximum number of retry attempts
            
        Returns:
            Response object
            
        Raises:
            requests.HTTPError: If the request fails after all retries
        """
        # Ensure minimum time between requests
        self._sleep_between_requests()
        
        # Construct full URL
        url = urljoin(self.base_url, endpoint.lstrip('/'))
        
        retry_count = 0
        backoff_time = 1
        
        while retry_count <= max_retries:
            try:
                logger.debug(f"Making {method} request to {url}")
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data
                )
                
                self.last_request_time = time.time()
                
                # Handle rate limiting (429)
                if response.status_code == 429:
                    retry_after = response.headers.get('Retry-After')
                    if retry_after:
                        wait_time = int(retry_after)
                    else:
                        wait_time = backoff_time
                    
                    logger.warning(
                        f"Rate limited (status {response.status_code}). "
                        f"Waiting {wait_time}s before retry {retry_count + 1}/{max_retries}"
                    )
                    time.sleep(wait_time)
                    retry_count += 1
                    backoff_time *= 2  # Exponential backoff
                    continue
                
                # Raise for other HTTP errors
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                retry_count += 1
                if retry_count > max_retries:
                    logger.error(f"Request failed after {max_retries} retries: {e}")
                    raise
                
                logger.warning(f"Request failed, retrying ({retry_count}/{max_retries}): {e}")
                time.sleep(backoff_time)
                backoff_time *= 2  # Exponential backoff
        
        raise requests.HTTPError(f"Request failed after {max_retries} retries")
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a GET request to the Docker Hub API.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            JSON response as dictionary
        """
        response = self._make_request('GET', endpoint, params=params)
        return response.json()
    
    def close(self) -> None:
        """Close the requests session."""
        self.session.close()
        logger.info("Closed Docker Hub API session")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def get_all_repos_for_namespace(self, namespace: str) -> List[Dict[str, Any]]:
        """
        Get all repositories for the specified namespace/user.
        
        Args:
            namespace: The Docker Hub namespace/username
            
        Returns:
            List of repositories
        """
        logger.info(f"Fetching repository list for namespace: {namespace}")
        repos = []
        url = f"/v2/repositories/{namespace}/"
        page = 1
        
        while url:
            logger.debug(f"Fetching page {page} from {url}")
            response = self._make_request('GET', url)
            data = response.json()
            
            results = data.get('results', [])
            repos.extend(results)
            
            # Check for next page
            url = data.get('next')
            if url:
                # Docker Hub returns full URLs, extract just the path
                if url.startswith('http'):
                    from urllib.parse import urlparse
                    parsed = urlparse(url)
                    url = parsed.path + ('?' + parsed.query if parsed.query else '')
            page += 1
        
        logger.info(f"Found {len(repos)} repositories for {namespace}")
        
        # Cache each individual repository
        curr_time = time.time()
        for repo_data in repos:
            repo_name = repo_data.get('name')
            namespace_name = repo_data.get('namespace')
            if repo_name and namespace_name:
                repo_full_name = f"{namespace_name}/{repo_name}"
                self.cached_repositories[repo_full_name] = (curr_time, repo_data)
                logger.debug(f"Cached repository: {repo_full_name}")
        
        return repos
    
    def get_repository(self, repo: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Get the cached repository data or fetch it if not cached.
        
        Args:
            repo: The repository in format 'owner/name'
            use_cache: Whether to use cached data (default: True)
            
        Returns:
            Dictionary with repository data
        """
        curr_time = time.time()
        cached = self.cached_repositories.get(repo)
        
        if use_cache and cached:
            cached_time, data = cached
            if curr_time - cached_time < self.cache_timeout_sec:
                logger.debug(f"Using cached data for {repo}")
                return data
        
        logger.info(f"Fetching repository data for {repo}")
        url = f"/v2/repositories/{repo}"
        response = self._make_request('GET', url)
        data = response.json()
        self.cached_repositories[repo] = (curr_time, data)
        return data
    
    def get_repo_pull_count(self, repo: str, use_cache: bool = True) -> int:
        """
        Get the number of pulls for a Docker Hub repository.
        
        Args:
            repo: The repository in format 'owner/name'
            use_cache: Whether to use cached data (default: True)
            
        Returns:
            Number of pulls
        """
        repo_data = self.get_repository(repo, use_cache)
        return repo_data.get("pull_count", 0)
    
    def get_repo_description(self, repo: str, use_cache: bool = True) -> str:
        """
        Get the description of a Docker Hub repository.
        
        Args:
            repo: The repository in format 'owner/name'
            use_cache: Whether to use cached data (default: True)
            
        Returns:
            Repository description
        """
        repo_data = self.get_repository(repo, use_cache)
        return repo_data.get("description", "")
    
    def get_repo_last_updated(self, repo: str, use_cache: bool = True) -> str:
        """
        Get the last updated timestamp of a Docker Hub repository.
        
        Args:
            repo: The repository in format 'owner/name'
            use_cache: Whether to use cached data (default: True)
            
        Returns:
            Last updated timestamp
        """
        repo_data = self.get_repository(repo, use_cache)
        return repo_data.get("last_updated", "")
    
    def get_repo_star_count(self, repo: str, use_cache: bool = True) -> int:
        """
        Get the number of stars for a Docker Hub repository.
        
        Args:
            repo: The repository in format 'owner/name'
            use_cache: Whether to use cached data (default: True)
            
        Returns:
            Number of stars
        """
        repo_data = self.get_repository(repo, use_cache)
        return repo_data.get("star_count", 0)
