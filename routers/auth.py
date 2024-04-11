from fastapi import Depends, HTTPException, Request, APIRouter, status
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from database import session
from database import engine
import models
from services.auth import token_generator, very_token


auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

models.Base.metadata.create_all(bind=engine)


templates = Jinja2Templates(directory="templates")

@auth_router.post('/token', status_code=status.HTTP_201_CREATED)
async def generate_token(request_form: OAuth2PasswordRequestForm = Depends()):
    token = await token_generator(request_form.username, request_form.password)
    return {
        'access_token': token,
        'token_type': 'bearer',
    }



@auth_router.get('/verification', response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def email_verification(request: Request, token: str):
    user = very_token(token)

    if user and not user.is_verified:
        user.is_verified = True
        session.commit()
        return templates.TemplateResponse("verification.html", {"username": user.username})
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

