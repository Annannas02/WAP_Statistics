from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

# Create SQLite engine and session
engine = create_engine('sqlite:///router_data.db')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)