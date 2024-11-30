import requests
from duckduckgo_search import ddg
from typing import List, Dict

class SearchProvider:
    def search(self, query: str, num_results: int = 5) -> List[Dict]:
        raise NotImplementedError

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
        response = requests.get(url, params=params)
        if response.status_code == 200:
            items = response.json().get('items', [])
            return [{'title': item['title'], 'link': item['link']} for item in items]
        return []

class DuckDuckGoProvider(SearchProvider):
    def search(self, query: str, num_results: int = 5) -> List[Dict]:
        results = ddg(query, max_results=num_results)
        return [{'title': r['title'], 'link': r['link']} for r in results]

class BingSearchProvider(SearchProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    def search(self, query: str, num_results: int = 5) -> List[Dict]:
        headers = {'Ocp-Apim-Subscription-Key': self.api_key}
        url = f"https://api.bing.microsoft.com/v7.0/search?q={query}&count={num_results}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            items = response.json().get('webPages', {}).get('value', [])
            return [{'title': item['name'], 'link': item['url']} for item in items]
        return []
