from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from typing import Annotated, List
from dotenv import dotenv_values
import smtplib, ssl
from models import User
import jwt
from database import get_db
import models
from logger import logger
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm


db_dependency = Annotated[Session, Depends(get_db)]
pwd_context = CryptContext(schemes=['bcrypt'], deprecated="auto")
config_credentials = dotenv_values(".env")

oath2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/token')


async def authenticate_user(db: db_dependency, username, password):
    user = db.query(User).filter(User.username == username).first()
    if user and verify_password(password, user.password):
        return user
    return False


async def token_generator(db: db_dependency, username: str, password: str):
    user = await authenticate_user(db, username, password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token_data = {
        "id": user.id,
        "username": user.username
    }

    token = jwt.encode(token_data, config_credentials['SECRET'])

    return token


async def get_current_user(db: db_dependency, token: str = Depends(oath2_scheme)):
    try:
        payload = jwt.decode(token, config_credentials['SECRET'], algorithms=['HS256'])
        user = db.query(User).filter(User.id == payload.get("id")).first()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except jwt.exceptions.DecodeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication error",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user



def get_hash_password(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


async def very_token(db: db_dependency, token: str):
    try:
        payload = jwt.decode(token, config_credentials["SECRET"],
                            algorithms=['HS256'])
        user = db.query(models.User).filter(models.User.id == payload.get("id")).first()

    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user



