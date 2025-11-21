import os
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database configuration
ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL")
SYNC_DATABASE_URL = os.getenv("SYNC_DATABASE_URL")  # Sync URL for metadata operations

# Create async engine for runtime operations
async_engine = create_async_engine(ASYNC_DATABASE_URL, 
                                #    echo=True, 
                                   future=True)

# Create sync engine for metadata operations (create_all, drop_all)
sync_engine = create_engine(SYNC_DATABASE_URL, 
                            # echo=True, 
                            future=True)

# Create async session
AsyncSessionLocal = sessionmaker(
    bind=async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Base class for models
Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

def create_tables():
    """Create all tables in the database"""
    print("Available tables to create:", Base.metadata.tables.keys())
    Base.metadata.create_all(bind=sync_engine)


def drop_tables():
    """Drop all tables in the database"""
    Base.metadata.drop_all(bind=sync_engine)