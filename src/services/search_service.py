"""
Service for managing search operations across different providers.
"""
from typing import List, Dict, Any, Optional
import logging
import requests

from src.services.search_providers import (
    GoogleSearchProvider,
    DuckDuckGoSearchProvider,
    BingSearchProvider
)

logger = logging.getLogger(__name__)

class SearchAPIError(Exception):
    """Exception raised for errors in the search API."""
    pass

class ConfigurationError(Exception):
    """Exception raised for errors in the configuration."""
    pass

class SearchService:
    """
    Service to coordinate search operations across different search providers
    """
    
    @staticmethod
    def get_all_results(query: str, providers: List[str], config: Dict[str, str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get search results from all specified providers
        
        Args:
            query: The search query
            providers: List of provider names ('Google', 'DuckDuckGo', 'Bing')
            config: Configuration dictionary with API keys and other settings
        
        Returns:
            Dictionary with provider names as keys and lists of search results as values
        
        Raises:
            ConfigurationError: If the required API keys are missing
            SearchAPIError: If there's an error with the search API
            ValueError: If an invalid provider is specified
        """
        if not query:
            raise ValueError("Search query cannot be empty")
            
        results = {}
        
        for provider in providers:
            try:
                if provider == 'Google':
                    # Validate Google configuration
                    api_key = config.get('api_key')
                    cx = config.get('cx')
                    if not api_key or not cx:
                        logger.warning("Missing Google API key or search engine ID")
                        results[provider] = []
                        continue
                        
                    # Create provider and perform search
                    google_provider = GoogleSearchProvider(api_key, cx)
                    results[provider] = google_provider.search(query)
                    
                elif provider == 'DuckDuckGo':
                    # DuckDuckGo doesn't require API keys
                    ddg_provider = DuckDuckGoSearchProvider()
                    results[provider] = ddg_provider.search(query)
                    
                elif provider == 'Bing':
                    # Validate Bing configuration
                    bing_api_key = config.get('bing_api_key')
                    if not bing_api_key:
                        logger.warning("Missing Bing API key")
                        results[provider] = []
                        continue
                        
                    # Create provider and perform search
                    bing_provider = BingSearchProvider(bing_api_key)
                    results[provider] = bing_provider.search(query)
                    
                else:
                    logger.warning(f"Unsupported provider: {provider}")
                    results[provider] = []
                    
            except Exception as e:
                logger.error(f"Error searching with provider {provider}: {str(e)}")
                results[provider] = []
        
        return results
