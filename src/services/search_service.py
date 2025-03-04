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
                        raise ConfigurationError("Google API key and search engine ID are required")
                        
                    google_provider = GoogleSearchProvider(api_key=api_key, cx=cx)
                    results['Google'] = google_provider.search(query)
                
                elif provider == 'DuckDuckGo':
                    duckduckgo_provider = DuckDuckGoSearchProvider()
                    results['DuckDuckGo'] = duckduckgo_provider.search(query)
                
                elif provider == 'Bing':
                    # Validate Bing configuration
                    bing_api_key = config.get('bing_api_key')
                    if not bing_api_key:
                        logger.warning("Missing Bing API key")
                        raise ConfigurationError("Bing API key is required")
                        
                    bing_provider = BingSearchProvider(api_key=bing_api_key)
                    results['Bing'] = bing_provider.search(query)
                
                else:
                    logger.warning(f"Unknown search provider: {provider}")
                    results[provider] = []
            
            except ConfigurationError as e:
                logger.error(f"Configuration error with {provider}: {str(e)}")
                results[provider] = []
            
            except requests.RequestException as e:
                logger.error(f"Network error with {provider}: {str(e)}")
                results[provider] = []
                
            except SearchAPIError as e:
                logger.error(f"API error with {provider}: {str(e)}")
                results[provider] = []
                
            except Exception as e:
                # Still catch general exceptions as fallback
                logger.error(f"Unexpected error with {provider}: {str(e)}", exc_info=True)
                results[provider] = []
        
        return results
