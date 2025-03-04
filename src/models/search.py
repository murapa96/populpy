from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

Base = declarative_base()

class Search(Base):
    __tablename__ = 'searches'
    
    id = Column(Integer, primary_key=True)
    query = Column(String)
    country = Column(String)
    timestamp = Column(DateTime, default=datetime.now)
    results = Column(JSON)
    settings = Column(JSON)

class SearchManager:
    def __init__(self, db_path="searches.db"):
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def save_search(self, query, country, results, settings):
        search = Search(
            query=query,
            country=country,
            results=results,
            settings=settings
        )
        self.session.add(search)
        self.session.commit()
        return search

    def add_search(self, query, country=None, results=None, settings=None):
        """Add a search to the history database"""
        if country is None and settings and 'country' in settings:
            country = settings['country']
        
        # Convert results to JSON serializable format if needed
        if results:
            try:
                # Test JSON serialization
                json.dumps(results)
            except (TypeError, OverflowError):
                results = str(results)
        
        # Convert settings to JSON serializable format
        if settings:
            try:
                # Test JSON serialization
                json.dumps(settings)
            except (TypeError, OverflowError):
                settings = str(settings)
                
        search = Search(
            query=query,
            country=country,
            results=results,
            settings=settings
        )
        self.session.add(search)
        self.session.commit()
        return search

    def get_recent_searches(self, limit=10):
        return self.session.query(Search).order_by(Search.timestamp.desc()).limit(limit).all()

    def get_search_by_id(self, search_id):
        """Get a specific search by ID"""
        try:
            search_id = int(search_id)
            return self.session.query(Search).get(search_id)
        except (ValueError, TypeError):
            return None

    def delete_search(self, search_id):
        search = self.session.query(Search).get(search_id)
        if search:
            self.session.delete(search)
            self.session.commit()
            return True
        return False
