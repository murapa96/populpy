from abc import ABC, abstractmethod
from typing import List, Dict
import requests
import logging
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

class SearchResult:
    def __init__(self, title: str, link: str):
        self.title = title
        self.link = link

    def to_dict(self) -> Dict:
        return {'title': self.title, 'link': self.link}

class SearchProvider(ABC):
    @abstractmethod
    def search(self, query: str, num_results: int = 5) -> List[Dict]:
        pass

class SearchProviderFactory(ABC):
    @abstractmethod
    def create_provider(self, **kwargs) -> SearchProvider:
        pass

class GoogleSearchProvider(SearchProvider):
    def __init__(self, api_key: str, cx: str):
        self.api_key = api_key
        self.cx = cx

    def search(self, query: str, num_results: int = 5) -> List[Dict]:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': self.api_key,
            'cx': self.cx,
            'q': query,
            'num': num_results
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            if response.status_code == 200:
                items = response.json().get('items', [])
                return [SearchResult(item['title'], item['link']).to_dict() for item in items]
            return []
        except Exception as e:
            logger.error(f"Error in GoogleSearchProvider: {str(e)}")
            return []

class DuckDuckGoSearchProvider(SearchProvider):
    def search(self, query: str, num_results: int = 5) -> List[Dict]:
        """Search using DuckDuckGo"""
        try:
            ddgs = DDGS()
            results = list(ddgs.text(query, max_results=num_results))
            return [SearchResult(r['title'], r['href']).to_dict() for r in results]
        except Exception as e:
            logger.error(f"Error in DuckDuckGoSearchProvider: {str(e)}")
            return []

class BingSearchProvider(SearchProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    def search(self, query: str, num_results: int = 5) -> List[Dict]:
        headers = {'Ocp-Apim-Subscription-Key': self.api_key}
        url = f"https://api.bing.microsoft.com/v7.0/search?q={query}&count={num_results}"
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            if response.status_code == 200:
                items = response.json().get('webPages', {}).get('value', [])
                return [SearchResult(item['name'], item['url']).to_dict() for item in items]
            return []
        except Exception as e:
            logger.error(f"Error in BingSearchProvider: {str(e)}")
            return []

class GoogleSearchProviderFactory(SearchProviderFactory):
    def create_provider(self, **kwargs) -> SearchProvider:
        api_key = kwargs.get('api_key')
        cx = kwargs.get('cx')
        if not api_key or not cx:
            raise ValueError("API key and CX are required for Google Search")
        return GoogleSearchProvider(api_key, cx)

class DuckDuckGoSearchProviderFactory(SearchProviderFactory):
    def create_provider(self, **kwargs) -> SearchProvider:
        return DuckDuckGoSearchProvider()

class BingSearchProviderFactory(SearchProviderFactory):
    def create_provider(self, **kwargs) -> SearchProvider:
        api_key = kwargs.get('api_key')
        if not api_key:
            raise ValueError("API key is required for Bing Search")
        return BingSearchProvider(api_key)

# Factory registry
PROVIDER_FACTORIES = {
    'Google': GoogleSearchProviderFactory(),
    'DuckDuckGo': DuckDuckGoSearchProviderFactory(),
    'Bing': BingSearchProviderFactory()
}
