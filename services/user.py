from database import session
from models import User



def is_username_exists(username: str) -> bool:
    user = session.query(User).filter(User.username == username).first()
    return user is not None

def is_email_exists(email: str) -> bool:
    user = session.query(User).filter(User.email == email).first()
    return user is not None