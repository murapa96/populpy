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
    related_searches = Column(JSON)
    settings = Column(JSON)

    @classmethod
    def create_tables(cls, engine):
        Base.metadata.create_all(engine)

class SearchManager:
    def __init__(self, db_path='sqlite:///searches.db'):
        self.engine = create_engine(db_path)
        Search.create_tables(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def save_search(self, query, country, related_searches, settings):
        session = self.Session()
        try:
            search = Search(
                query=query,
                country=country,
                related_searches=related_searches,
                settings=settings
            )
            session.add(search)
            session.commit()
            return search
        finally:
            session.close()

    def get_recent_searches(self, limit=10):
        session = self.Session()
        try:
            return session.query(Search).order_by(Search.timestamp.desc()).limit(limit).all()
        finally:
            session.close()

    def get_search_by_id(self, search_id):
        session = self.Session()
        try:
            return session.query(Search).filter(Search.id == search_id).first()
        finally:
            session.close()

    def delete_search(self, search_id):
        session = self.Session()
        try:
            search = session.query(Search).filter(Search.id == search_id).first()
            if search:
                session.delete(search)
                session.commit()
                return True
            return False
        finally:
            session.close()
