import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

DATABASE_URL = "sqlite:///./backend/app.db"

# Ensure the directory exists
os.makedirs(os.path.dirname(DATABASE_URL.replace("sqlite:///", "")), exist_ok=True)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
class QueryHistory(Base):
    __tablename__ = "query_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True) # 0 for guest
    query_text = Column(String)
    domain = Column(String) # 'law' or 'insurance'
    response = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

class ViolationReport(Base):
    __tablename__ = "violation_reports"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    bank_name = Column(String, index=True)
    violation_type = Column(String) # e.g. 'Ghost Insurance', 'Forced Bundling'
    location_state = Column(String) # e.g. 'Maharashtra', 'Karnataka'
    severity = Column(String) # 'High', 'Medium', 'Low'
    timestamp = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
