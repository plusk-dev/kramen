from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from config import DATABASE_URL

Base = declarative_base()

class Integration(Base):
    __tablename__ = 'integration'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    uuid = Column(String, nullable=False, unique=True)
    icon = Column(String, nullable=False)
    limit = Column(Integer, nullable=False, default=1000)  # Default rate limit
    auth_structure = Column(JSON, nullable=True)  # JSON field for authentication structure
    created = Column(DateTime, default=datetime.utcnow, nullable=False)

# Create an SQLite engine (or any other database you prefer)
engine = create_engine(DATABASE_URL)

# Create all tables
Base.metadata.create_all(engine)

# Create a session maker
Session = sessionmaker(bind=engine)
session = Session()