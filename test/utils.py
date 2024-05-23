from datetime import datetime
import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from models import Product, User
from schema.user import UserRole
from database import SQLALCHEMY_DATABASE_URL
from main import app

# Set the TESTING environment variable
os.environ['TESTING'] = '1'

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency to use the test database
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Override the current user dependency
def override_current_user():
    user = User(id=1, username="testuser", email="testuser@example.com", is_verified=True, role=UserRole.CUSTOMER)
    return user

# Create a TestClient instance
client = TestClient(app)



