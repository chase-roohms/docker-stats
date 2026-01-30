import time
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class GoogleAnalyticsApi:
    """
    A wrapper for the Google Analytics Data API (GA4) with built-in rate limiting support.
    Uses the Google Analytics Data API v1 to fetch page view statistics.
    
    Args:
        property_id: GA4 property ID (e.g., "123456789")
        credentials_path: Path to service account credentials JSON file
        cache_timeout_sec: Cache timeout in seconds (default: 300)
    """
    
    def __init__(self, property_id: str, credentials_path: Optional[str] = None, credentials_json: Optional[str] = None, cache_timeout_sec: int = 300):
        """Initialize the Google Analytics API client.
        
        Args:
            property_id: GA4 property ID
            credentials_path: Path to service account credentials JSON file (for local development)
            credentials_json: Service account credentials as JSON string (for CI/CD)
            cache_timeout_sec: Cache timeout in seconds
        """
        self.property_id = property_id
        self.credentials_path = credentials_path
        self.credentials_json = credentials_json
        self.cache_timeout_sec = cache_timeout_sec
        
        # Cache for page view data to minimize API calls
        self.cached_page_views = {}
        self.cache_timestamp = None
        
        # Rate limiting tracking
        self.last_request_time = 0
        self.min_sleep_time = 0.1  # Minimum 0.1s between requests
        
        # Initialize the Google Analytics client
        self._initialize_client()
        
        logger.info(f"Initialized Google Analytics API client for property: {self.property_id}")
    
    def _initialize_client(self) -> None:
        """Initialize the Google Analytics Data API client with authentication."""
        try:
            from google.analytics.data_v1beta import BetaAnalyticsDataClient
            from google.oauth2 import service_account
            import json as json_module
            
            credentials = None
            
            # Priority: credentials_json > credentials_path > default
            if self.credentials_json:
                # Load credentials from JSON string (for CI/CD)
                credentials_info = json_module.loads(self.credentials_json)
                credentials = service_account.Credentials.from_service_account_info(
                    credentials_info,
                    scopes=['https://www.googleapis.com/auth/analytics.readonly']
                )
                logger.info("Loaded credentials from JSON string")
            elif self.credentials_path:
                # Load credentials from file (for local development)
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=['https://www.googleapis.com/auth/analytics.readonly']
                )
                logger.info(f"Loaded credentials from file: {self.credentials_path}")
            
            if credentials:
                self.client = BetaAnalyticsDataClient(credentials=credentials)
            else:
                # Use default credentials (from environment)
                self.client = BetaAnalyticsDataClient()
                logger.info("Using default credentials from environment")
                
            logger.info("Successfully initialized Google Analytics Data API client")
        except ImportError:
            logger.error("google-analytics-data package not installed. Install with: pip install google-analytics-data")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Google Analytics client: {e}")
            raise
    
    def _sleep_between_requests(self) -> None:
        """Ensure minimum time between requests to respect rate limits."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_sleep_time:
            sleep_time = self.min_sleep_time - elapsed
            logger.debug(f"Sleeping for {sleep_time:.2f}s to maintain rate limit")
            time.sleep(sleep_time)
    
    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid."""
        if not self.cache_timestamp:
            return False
        elapsed = time.time() - self.cache_timestamp
        return elapsed < self.cache_timeout_sec
    
    def get_all_page_views(self, date_range_days: Optional[int] = None) -> Dict[str, int]:
        """
        Fetch page view counts for all pages.
        
        Args:
            date_range_days: Number of days to look back (None = all time since GA4 start)
        
        Returns:
            Dictionary mapping page paths to total page view counts
        """
        # Check cache first
        if self._is_cache_valid() and self.cached_page_views:
            logger.debug("Returning cached page view data")
            return self.cached_page_views
        
        self._sleep_between_requests()
        
        try:
            from google.analytics.data_v1beta.types import (
                RunReportRequest,
                Dimension,
                Metric,
                DateRange,
            )
            
            # Set date range
            if date_range_days:
                start_date = (datetime.now() - timedelta(days=date_range_days)).strftime('%Y-%m-%d')
            else:
                # GA4 was released in October 2020, but use a safe start date
                start_date = "2020-10-14"
            
            end_date = "today"
            
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                dimensions=[Dimension(name="pagePath")],
                metrics=[Metric(name="screenPageViews")],
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                limit=10000,  # Adjust based on expected number of pages
            )
            
            response = self.client.run_report(request)
            self.last_request_time = time.time()
            
            # Parse response
            page_views = {}
            for row in response.rows:
                page_path = row.dimension_values[0].value
                views = int(row.metric_values[0].value)
                page_views[page_path] = views
            
            # Update cache
            self.cached_page_views = page_views
            self.cache_timestamp = time.time()
            
            logger.info(f"Fetched page views for {len(page_views)} pages")
            return page_views
            
        except Exception as e:
            logger.error(f"Error fetching page views: {e}")
            raise
    
    def get_page_view_count(self, page_path: str, date_range_days: Optional[int] = None) -> int:
        """
        Get page view count for a specific page path.
        
        Args:
            page_path: The page path (e.g., "/blog/my-post")
            date_range_days: Number of days to look back (None = all time)
        
        Returns:
            Total page view count for the specified page
        """
        all_page_views = self.get_all_page_views(date_range_days)
        return all_page_views.get(page_path, 0)
    
    def get_blog_post_views(self, blog_path_prefix: str = "/blog/", date_range_days: Optional[int] = None) -> Dict[str, int]:
        """
        Get page view counts for all blog posts (pages starting with a specific prefix).
        
        Args:
            blog_path_prefix: The path prefix for blog posts (default: "/blog/")
            date_range_days: Number of days to look back (None = all time)
        
        Returns:
            Dictionary mapping blog post paths to page view counts
        """
        all_page_views = self.get_all_page_views(date_range_days)
        
        # Filter for blog posts
        blog_views = {
            path: views 
            for path, views in all_page_views.items() 
            if path.startswith(blog_path_prefix)
        }
        
        logger.info(f"Found {len(blog_views)} blog posts with prefix '{blog_path_prefix}'")
        return blog_views
    
    def get_total_page_views(self, date_range_days: Optional[int] = None) -> int:
        """
        Get total page views across all pages.
        
        Args:
            date_range_days: Number of days to look back (None = all time)
        
        Returns:
            Total page view count across all pages
        """
        all_page_views = self.get_all_page_views(date_range_days)
        return sum(all_page_views.values())
