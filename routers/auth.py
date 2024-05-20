from typing import Annotated
from fastapi import Depends, HTTPException, Request, APIRouter, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from database import get_db
from database import engine
import models
from services.auth import token_generator, very_token


auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)
db_dependency = Annotated[Session, Depends(get_db)]

models.Base.metadata.create_all(bind=engine)


templates = Jinja2Templates(directory="templates")

@auth_router.post('/token', status_code=status.HTTP_201_CREATED)
async def generate_token(db: db_dependency, request_form: OAuth2PasswordRequestForm = Depends()):
    """
    Generates an access token for the user.

    Args:
    request_form (OAuth2PasswordRequestForm): The form data containing the username and password.

    Returns:
    dict: A dictionary containing the generated access token and its type.

    """
    token = await token_generator(db, request_form.username, request_form.password)
    return {
        'access_token': token,
        'token_type': 'bearer',
    }



@auth_router.get('/verification', response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def email_verification(db: db_dependency, request: Request, token: str):
    """
    Verifies the user's email by setting the 'is_verified' attribute to True in the database.

    Args:
    db (Session): The database session.
    request (Request): The HTTP request object.
    token (str): The token to be verified.

    Returns:
    dict: A dictionary containing the HTML response for the verification page.

    Raises:
    HTTPException: If the token is invalid or expired.

    """
    user = await very_token(db, token)

    if user and not user.is_verified:
        user.is_verified = True
        db.commit()
        return templates.TemplateResponse("verification.html", {"username": user.username, "request": request})
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
