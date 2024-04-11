from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
# from sqlalchemy.ext.declarative import declarative_base


# Define the SQLAlchemy database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///database.db"


# Create the SQLAlchemy engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create a sessionmaker to create sessions for interacting with the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


session = SessionLocal()

# Create a base class for your SQLAlchemy models
Base = declarative_base()

