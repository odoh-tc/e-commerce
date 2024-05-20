from fastapi import FastAPI, status
from fastapi.staticfiles import StaticFiles
from logger import logger
# from middleware import ecommerce_middleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from database import engine
import models
from routers.user import user_router
from routers.auth import auth_router
from routers.product import product_router
from routers.business import business_router
from routers.order import order_router
from routers.admin import admin_router


app = FastAPI(
    title="E-commerce Application",
    description="A robust e-commerce backend application built with FastAPI. This app features role-based access control, allowing business owners to create and manage multiple businesses, each with its own products, while customers can place and manage orders. Additionally, an admin role is included to perform various administrative operations.",
    version="1.0.0"
)
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(product_router)
app.include_router(business_router)
app.include_router(order_router)





logger.info("starting app")
# app.add_middleware(BaseHTTPMiddleware, dispatch=ecommerce_middleware)
app.mount("/static", StaticFiles(directory="static"), name="static")

models.Base.metadata.create_all(bind=engine)


allowed_origins = ["*"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,       
    allow_methods=["GET", "POST", "PUT", "DELETE"],  
    allow_headers=["*"],     
)


@app.get("/", status_code=status.HTTP_200_OK)
async def home():
    return {"message": "Welcome to our home page!"}