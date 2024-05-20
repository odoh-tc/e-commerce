from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User



db_dependency = Annotated[Session, Depends(get_db)]

def is_username_exists(db: db_dependency, username: str) -> bool:
    user = db.query(User).filter(User.username == username).first()
    return user is not None

def is_email_exists(db: db_dependency, email: str) -> bool:
    user = db.query(User).filter(User.email == email).first()
    return user is not None