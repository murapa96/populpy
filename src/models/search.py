from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

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

    def get_recent_searches(self, limit=10):
        return self.session.query(Search).order_by(Search.timestamp.desc()).limit(limit).all()

    def delete_search(self, search_id):
        search = self.session.query(Search).get(search_id)
        if search:
            self.session.delete(search)
            self.session.commit()
