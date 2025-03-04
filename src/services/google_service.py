"""
Google services module for interacting with Google Trends and Search APIs
"""
import requests
from pytrends.request import TrendReq
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class GoogleServiceError(Exception):
    """Base exception for Google service errors"""
    pass

class GoogleAPIError(GoogleServiceError):
    """Exception for Google API errors"""
    pass

class GoogleTrendsError(GoogleServiceError):
    """Exception for Google Trends errors"""
    pass

def get_google_related_searches(query: str, pytrends: TrendReq) -> List[str]:
    """
    Get related search queries from Google Trends
    
    Args:
        query: Main search query
        pytrends: PyTrends object with valid credentials
        
    Returns:
        List of related search queries
        
    Raises:
        GoogleTrendsError: If there's an error retrieving data from Google Trends
    """
    try:
        pytrends.build_payload([query])
        related_queries = pytrends.related_queries()
        if query in related_queries and 'top' in related_queries[query]:
            return [item['query'] for item in related_queries[query]['top'].to_dict('records')]
        return []
    except Exception as e:
        logger.error(f"Error getting related searches: {str(e)}")
        raise GoogleTrendsError(f"Failed to get related searches: {str(e)}") from e

def get_google_search_trends(query: str, pytrends: TrendReq) -> Dict[str, List]:
    """
    Get Google Trends data for a search query
    
    Args:
        query: Search query to retrieve trends for
        pytrends: PyTrends object with valid credentials
        
    Returns:
        Dictionary with dates and values lists
        
    Raises:
        GoogleTrendsError: If there's an error retrieving trends data
    """
    try:
        # Build the payload
        pytrends.build_payload([query])
        
        # Get interest over time
        interest_over_time_df = pytrends.interest_over_time()
        
        if interest_over_time_df.empty:
            logger.info(f"No trends data available for query: {query}")
            return {'dates': [], 'values': []}
            
        # Convert datetime index to strings and values to lists
        return {
            'dates': interest_over_time_df.index.astype(str).tolist(),
            'values': interest_over_time_df[query].tolist()
        }
        
    except Exception as e:
        logger.error(f"Error getting trends data: {str(e)}")
        raise GoogleTrendsError(f"Failed to get trends data: {str(e)}") from e

def create_wordcloud(related_searches: List[str], path: str, background_color: str = 'white', 
                    colormap: str = 'viridis') -> None:
    """
    Create a word cloud image from related search terms
    
    Args:
        related_searches: List of search terms to include in the word cloud
        path: Output file path for the image
        background_color: Background color for the word cloud
        colormap: Matplotlib colormap name for the word cloud
        
    Raises:
        ValueError: If related_searches is empty
        IOError: If there's an error saving the image
    """
    if not related_searches:
        logger.warning("Empty list provided for word cloud generation")
        raise ValueError("Cannot create wordcloud from empty list")
        
    try:
        text = ' '.join(related_searches)
        wordcloud = WordCloud(
            width=800, 
            height=400,
            background_color=background_color,
            colormap=colormap
        ).generate(text)
        
        plt.figure(figsize=(10,5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.savefig(path, bbox_inches='tight', pad_inches=0)
        plt.close()
        logger.info(f"Word cloud saved successfully to {path}")
    except Exception as e:
        logger.error(f"Error creating wordcloud: {str(e)}")
        raise IOError(f"Failed to create word cloud: {str(e)}") from e

def get_top_results_for_related_searches(query: str, pytrends: TrendReq, 
                                        api_key: str, cx: str) -> Dict[str, List[str]]:
    """
    Get top search results for related searches
    
    Args:
        query: Main search query to find related searches for
        pytrends: PyTrends object with valid credentials
        api_key: Google Custom Search API key
        cx: Google Custom Search Engine ID
        
    Returns:
        Dictionary with related searches as keys and lists of search results as values
        
    Raises:
        GoogleAPIError: If there's an error with the Google API
        ValueError: If API key or cx is missing
    """
    if not api_key or not cx:
        raise ValueError("API key and search engine ID are required")
        
    try:
        related_searches = get_google_related_searches(query, pytrends)
        results = {}
        
        for search in related_searches:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': api_key,
                'cx': cx,
                'q': search,
                'num': 5
            }
            
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()  # Raise exception for 4XX/5XX responses
                
                if response.status_code == 200:
                    items = response.json().get('items', [])
                    results[search] = [item['title'] for item in items]
                else:
                    logger.warning(f"Google API returned non-200 status: {response.status_code}")
                    results[search] = []
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error for search '{search}': {str(e)}")
                results[search] = []
        
        return results
        
    except Exception as e:
        logger.error(f"Error in get_top_results_for_related_searches: {str(e)}")
        raise GoogleAPIError(f"Failed to get top results: {str(e)}") from e
