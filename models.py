"""
Models module that re-exports the models from src/models/search.py
This file exists for backward compatibility.
"""
from src.models.search import Search, SearchManager

# Re-export the models
__all__ = ['Search', 'SearchManager']
