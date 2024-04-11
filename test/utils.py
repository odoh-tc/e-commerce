# import pytest
# from sqlalchemy import create_engine, text
# from sqlalchemy.pool import StaticPool
# from sqlalchemy.orm import sessionmaker
# from fastapi.testclient import TestClient
# from database import Base
# from main import app
# from models import User
# from services.auth import pwd_context


# SQLALCHEMY_DATABASE_URL = "sqlite:///./testdb.db"

# engine = create_engine(SQLALCHEMY_DATABASE_URL,
#                        connect_args={"check_same_thread": False},
#                        poolclass=StaticPool)


# TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False,  bind=engine)

# Base.metadata.create_all(bind=engine)


# session = TestingSessionLocal()

# client = TestClient(app)


# @pytest.fixture
# def test_user():
#     user = User(
#         username="maximo",
#         email="max@gmail.com",
#         hashed_password=pwd_context.hash('max'),
#         role="admin",
#     )

#     session.add(user)
#     session.commit()
#     yield user
#     with engine.connect() as connection:
#         connection.execute(text("DELETE FROM users;"))
#         connection.commit()
                             