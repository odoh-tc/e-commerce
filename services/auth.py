from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from typing import List
from dotenv import dotenv_values
import smtplib, ssl
from models import User
import jwt
from database import session
import models
from logger import logger
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm



pwd_context = CryptContext(schemes=['bcrypt'], deprecated="auto")
config_credentials = dotenv_values(".env")

oath2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/token')


async def authenticate_user(username, password):
    user = session.query(User).filter(User.username == username).first()
    if user and verify_password(password, user.password):
        return user
    return False


async def token_generator(username: str, password: str):
    user = await authenticate_user(username, password)

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


async def get_current_user(token: str = Depends(oath2_scheme)):
    try:
        payload = jwt.decode(token, config_credentials['SECRET'], algorithms=['HS256'])
        user = session.query(User).filter(User.id == payload.get("id")).first()

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


async def very_token(token: str):
    try:
        payload = jwt.decode(token, config_credentials["SECRET"],
                            algorithms=['HS256'])
        user = session.query(models.User).filter(models.User.id == payload.get("id")).first()

    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user



if "EMAIL" not in config_credentials or "PASS" not in config_credentials:
    raise ValueError("Email or password not found in .env file")


SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = config_credentials["EMAIL"]
SENDER_PASSWORD = config_credentials["PASS"]

# PORT = 465

async def send_email(receiver_email: str, instance: models.User):
    try:
        token_data = {
            "id": instance.id,
            "username": instance.username,
        }

        token = jwt.encode(token_data, config_credentials["SECRET"], algorithm='HS256')

        subject = "Account Verification"

        body = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta http-equiv="X-UA-Compatible" content="IE=edge">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body>
            <div style="display: flex; align-items: center; justify-content: center; flex-direction: column;">
                <h3>Account Verification</h3>
                <br>
                <p>Thanks for choosing EasyShopas. Please click on the button below to verify your account</p>
                <a style="margin-top: 1rem; padding: 1rem; border-radius: 0.5rem; font-size: 1rem;
                text-decoration: none; background: #0275d8; color: white;"
                href="http://localhost:8000/auth/verification?token={token}">
                    Verify your Account
                </a>
                <p>Please kindly ignore this email if you did not register for EasyShopas.</p>
            </div>
        </body>
        </html>
        """

        message = f"Subject: {subject}\n"
        message += f"MIME-Version: 1.0\n"
        message += f"Content-type: text/html\n\n"
        message += body

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, receiver_email, message)

    except Exception as e:
        logger.error(f"Error sending email to {receiver_email}: {e}")

        print(f"Error sending email: {e}")