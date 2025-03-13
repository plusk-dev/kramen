from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from config import DATABASE_URL

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    limit = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    pfp = Column(String, nullable=False)
    sign_up_method = Column(String)
    
    api_keys = relationship('APIKey', back_populates='user')
    integrations = relationship('Integration', back_populates='owner')

class APIKey(Base):
    __tablename__ = 'api_key'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    key_hash = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)

    created = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    user = relationship('User', back_populates='api_keys')

class Integration(Base):
    __tablename__ = 'integration'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    uuid = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    created = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    owner = relationship('User', back_populates='integrations')

# Create an SQLite engine (or any other database you prefer)
engine = create_engine(DATABASE_URL)

# Create all tables
Base.metadata.create_all(engine)

# Create a session maker
Session = sessionmaker(bind=engine)
session = Session()