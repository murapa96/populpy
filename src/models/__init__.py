from datetime import datetime
import json
import os
from typing import List, Dict, Optional

class Search:
    def __init__(self, id: int, query: str, timestamp: datetime, settings: Dict, country: str):
        self.id = id
        self.query = query
        self.timestamp = timestamp
        self.settings = settings
        self.country = country

class SearchManager:
    def __init__(self):
        self.searches_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'data',
            'searches.json'
        )
        self._ensure_data_dir()
        self.searches = self._load_searches()

    def _ensure_data_dir(self):
        os.makedirs(os.path.dirname(self.searches_file), exist_ok=True)

    def _load_searches(self) -> List[Search]:
        if not os.path.exists(self.searches_file):
            return []
        try:
            with open(self.searches_file, 'r') as f:
                data = json.load(f)
                return [
                    Search(
                        id=s['id'],
                        query=s['query'],
                        timestamp=datetime.fromisoformat(s['timestamp']),
                        settings=s['settings'],
                        country=s['country']
                    )
                    for s in data
                ]
        except:
            return []

    def _save_searches(self):
        with open(self.searches_file, 'w') as f:
            json.dump([
                {
                    'id': s.id,
                    'query': s.query,
                    'timestamp': s.timestamp.isoformat(),
                    'settings': s.settings,
                    'country': s.country
                }
                for s in self.searches
            ], f)

    def add_search(self, query: str, settings: Dict, country: Optional[str] = None) -> Search:
        new_id = max([s.id for s in self.searches], default=0) + 1
        search = Search(
            id=new_id,
            query=query,
            timestamp=datetime.now(),
            settings=settings,
            country=country or 'global'  # Default to 'global' if no country provided
        )
        self.searches.append(search)
        self._save_searches()
        return search

    def get_recent_searches(self, limit: int = 10) -> List[Search]:
        return sorted(
            self.searches,
            key=lambda x: x.timestamp,
            reverse=True
        )[:limit]

    def delete_search(self, search_id: int):
        self.searches = [s for s in self.searches if s.id != search_id]
        self._save_searches()

    def clear_history(self):
        self.searches = []
        self._save_searches()
