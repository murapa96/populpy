from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime
import json
import os
import threading
from typing import List, Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

class Search(Base):
    """
    Database model representing a user search query and its results
    """
    __tablename__ = 'searches'
    
    id = Column(Integer, primary_key=True)
    query = Column(String)
    country = Column(String)
    timestamp = Column(DateTime, default=datetime.now)
    results = Column(JSON)
    settings = Column(JSON)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Search object to dictionary representation"""
        return {
            "id": self.id,
            "query": self.query,
            "country": self.country,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "results": self.results,
            "settings": self.settings
        }

class SearchManager:
    """
    Thread-safe manager class for handling search history operations
    """
    # Class variable to track instances per thread
    _instances = {}
    _lock = threading.RLock()
    
    @classmethod
    def get_instance(cls, db_path: Optional[str] = None) -> 'SearchManager':
        """
        Get or create a SearchManager instance for the current thread
        
        Args:
            db_path: Path to the SQLite database file
            
        Returns:
            Thread-specific SearchManager instance
        """
        thread_id = threading.get_ident()
        with cls._lock:
            if thread_id not in cls._instances:
                cls._instances[thread_id] = cls(db_path)
            return cls._instances[thread_id]
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the SearchManager with a database connection
        
        Args:
            db_path: Path to the SQLite database file. If None, uses 'searches.db' or 
                    the DATABASE_PATH environment variable if set.
        """
        if db_path is None:
            db_path = os.environ.get('DATABASE_PATH', 'searches.db')
        
        # Create engine with the 'check_same_thread=False' option for SQLite
        self.engine = create_engine(
            f'sqlite:///{db_path}',
            connect_args={"check_same_thread": False}  # Allow SQLite to be used across threads
        )
        Base.metadata.create_all(self.engine)
        
        # Create thread-local session factory
        self.Session = scoped_session(
            sessionmaker(bind=self.engine, 
                         expire_on_commit=False)  # Prevent detached instance errors
        )
        
        logger.info(f"Initialized SearchManager with database: {db_path}")
    
    def add_search(self, query: str, country: Optional[str] = None, 
                  results: Optional[Dict[str, Any]] = None, 
                  settings: Optional[Dict[str, Any]] = None) -> Search:
        """
        Add a search to the history database
        
        Args:
            query: The search query string
            country: Country code for the search (e.g., 'ES', 'US')
            results: Dictionary containing search results
            settings: Dictionary containing search settings/parameters
            
        Returns:
            The created Search object
        """
        if country is None and settings and 'country' in settings:
            country = settings['country']
        
        # Convert results to JSON serializable format if needed
        serialized_results = self._ensure_json_serializable(results)
        
        # Convert settings to JSON serializable format
        serialized_settings = self._ensure_json_serializable(settings)
                
        search = Search(
            query=query,
            country=country,
            results=serialized_results,
            settings=serialized_settings
        )
        
        # Create a new session for this operation
        session = self.Session()
        try:
            session.add(search)
            session.commit()
            logger.debug(f"Added search for query '{query}' to database")
            return search
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding search to database: {str(e)}")
            # Create a minimal search object to return
            return Search(query=query, country=country)
        finally:
            session.close()

    def _ensure_json_serializable(self, data: Any) -> Any:
        """
        Ensure data is JSON serializable by testing serialization
        
        Args:
            data: Any data structure to check
            
        Returns:
            JSON serializable version of the data
        """
        if data is None:
            return {}
            
        try:
            # Test JSON serialization
            json.dumps(data)
            return data
        except (TypeError, OverflowError) as e:
            logger.warning(f"Data is not JSON serializable: {str(e)}")
            # Convert to string representation as fallback
            try:
                return str(data)
            except Exception:
                return {}

    def get_recent_searches(self, limit: int = 10) -> List[Search]:
        """
        Get recent searches ordered by timestamp
        
        Args:
            limit: Maximum number of searches to return
            
        Returns:
            List of Search objects
        """
        session = self.Session()
        try:
            searches = session.query(Search).order_by(Search.timestamp.desc()).limit(limit).all()
            # Clone the results to avoid cross-thread access issues
            return [self._clone_search(search) for search in searches]
        except Exception as e:
            logger.error(f"Error retrieving recent searches: {str(e)}")
            return []
        finally:
            session.close()
            
    def _clone_search(self, search: Search) -> Search:
        """Create a detached copy of a Search object to avoid cross-thread issues"""
        if search is None:
            return None
            
        return Search(
            id=search.id,
            query=search.query,
            country=search.country,
            timestamp=search.timestamp,
            results=search.results,
            settings=search.settings
        )

    def get_search_by_id(self, search_id: Union[int, str]) -> Optional[Search]:
        """
        Get a specific search by ID
        
        Args:
            search_id: The ID of the search to retrieve
            
        Returns:
            Search object if found, None otherwise
        """
        session = self.Session()
        try:
            search_id_int = int(search_id)
            search = session.query(Search).get(search_id_int)
            return self._clone_search(search)  # Return a detached copy
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid search ID: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving search by ID: {str(e)}")
            return None
        finally:
            session.close()

    def delete_search(self, search_id: Union[int, str]) -> bool:
        """
        Delete a search by ID
        
        Args:
            search_id: The ID of the search to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        session = self.Session()
        try:
            search_id_int = int(search_id)
            search = session.query(Search).get(search_id_int)
            if search:
                session.delete(search)
                session.commit()
                logger.info(f"Deleted search with ID {search_id}")
                return True
            logger.warning(f"Search with ID {search_id} not found for deletion")
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting search: {str(e)}")
            return False
        finally:
            session.close()
    
    def close(self) -> None:
        """
        Close the session and clean up resources
        """
        self.Session.remove()
        
    def __del__(self) -> None:
        """
        Ensure resources are cleaned up when the instance is garbage collected
        """
        try:
            self.close()
        except:
            pass
