from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
import models
from services.auth import get_current_user, get_hash_password 
from schema.user import UserIn, UserRole, UserUpdate
from services.user import is_email_exists, is_username_exists
from database import get_db
from logger import logger
from database import engine


user_router = APIRouter(
    prefix="/user",
    tags=["User"],
    responses={404: {"description": "Not found"}},
    # summary="API endpoints for managing users.",
    # description="This router provides endpoints for user registration, login, profile update, and other user-related operations."
)

models.Base.metadata.create_all(bind=engine)
db_dependency = Annotated[Session, Depends(get_db)]



@user_router.post('/registration', status_code=status.HTTP_201_CREATED)
async def user_registration(db: db_dependency, user: UserIn):
    """
    Registers a new user.

    Parameters:
    - db (db_dependency): A dependency that provides a database session.
    - user (UserIn): A UserIn object containing the user's registration information.

    Returns:
    - A dictionary containing a success message and the newly registered user's information.

    Raises:
    - HTTPException with status code 400 and "Username already exists" detail if the username already exists in the database.
    - HTTPException with status code 400 and "Email already exists" detail if the email already exists in the database.
    - HTTPException with status code 400 and "Something went wrong. Please try again later" detail if a database error occurs.
    """
    try: 
        user_info = user.model_dump()
        user_info["password"] = get_hash_password(user.password)
        user_info["role"] = user.role.value

        new_user = models.User(**user_info)

        if is_username_exists(db, user.username):
            raise HTTPException(status_code=400, detail="Username already exists")
        if is_email_exists(db, user.email):
            raise HTTPException(status_code=400, detail="Email already exists")
        
        db.add(new_user)
        db.commit()

        return {
                "status": "ok",
                "data": f"Hello {new_user.username}, Thanks for choosing our services. Please check your email inbox and click on the link to confirm your registration"
            }
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error occurred: {e}")
        raise HTTPException(status_code=400, detail="Something went wrong. Please try again later")





@user_router.post('/me', status_code=status.HTTP_201_CREATED)
async def user_login(
    db: db_dependency,
    user: UserIn = Depends(get_current_user),
    business_page: int = Query(1, description="Page number for businesses", gt=0),
    business_page_size: int = Query(10, description="Number of businesses per page", gt=0),
    product_page: int = Query(1, description="Page number for products", gt=0),
    product_page_size: int = Query(10, description="Number of products per page", gt=0),
    order_page: int = Query(1, description="Page number for orders", gt=0),
    order_page_size: int = Query(10, description="Number of orders per page", gt=0),
):
    """
    Retrieves user's profile along with their businesses, products, and orders.

    Parameters:
    - db (db_dependency): A dependency that provides a database session.
    - user (UserIn): A UserIn object containing the user's login information.
    - business_page (int): The page number for businesses.
    - business_page_size (int): The number of businesses per page.
    - product_page (int): The page number for products.
    - product_page_size (int): The number of products per page.
    - order_page (int): The page number for orders.
    - order_page_size (int): The number of orders per page.

    Returns:
    - A dictionary containing a success message and the user's profile along with their businesses, products, and orders.

    Raises:
    - HTTPException with status code 401 and "Unauthorized, please login" detail if the user is not authenticated.
    """
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized, please login")

    if user.role == UserRole.BUSINESS_OWNER:
        # Calculate the offset for businesses
        business_offset = (business_page - 1) * business_page_size

        # Retrieve businesses associated with the user with pagination
        businesses = db.query(models.Business).filter(models.Business.owner_id == user.id).offset(business_offset).limit(business_page_size).all()

        business_data = []
        for business in businesses:
            # Calculate the offset for products
            product_offset = (product_page - 1) * product_page_size

            # Retrieve products associated with the business with pagination
            products = db.query(models.Product).filter(models.Product.business_id == business.id).offset(product_offset).limit(product_page_size).all()

            business_details = {
                "business_id": business.id,
                "business_name": business.business_name,
                "city": business.city,
                "region": business.region,
                "business_description": business.business_description,
                "logo": "localhost:8000/static/images/" + business.logo,
            }

            serialized_products = [product.serialize() for product in products]

            business_data.append({
                "business_details": business_details,
                "products": serialized_products
            })

        user_details = {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "verified": user.is_verified,
            "joined_date": user.join_date.strftime("%b %d %Y %H:%M:%S") if user.join_date else None,
        }

        return {
            "status": "ok",
            "data": {
                "user_details": user_details,
                "businesses": business_data
            }
        }

    elif user.role == UserRole.CUSTOMER:
        # Calculate the offset for orders
        order_offset = (order_page - 1) * order_page_size

        # Retrieve orders associated with the user with pagination
        orders = db.query(models.Order).filter(models.Order.user_id == user.id).offset(order_offset).limit(order_page_size).all()

        user_details = {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "verified": user.is_verified,
            "joined_date": user.join_date.strftime("%b %d %Y %H:%M:%S") if user.join_date else None,
        }

        if orders:
            serialized_orders = [order.serialize() for order in orders]
            return {
                "status": "ok",
                "data": {
                    "user_details": user_details,
                    "orders": serialized_orders
                }
            }
        else:
            return {
                "status": "ok",
                "data": {
                    "user_details": user_details,
                    "orders": []
                }
            }





@user_router.put('/', status_code=status.HTTP_200_OK)
async def update_profile(db: db_dependency, user_update: UserUpdate, 
                         user: UserIn = Depends(get_current_user)):
    """
    Updates the profile of the currently authenticated user.
   
    Parameters:
    - db (db_dependency): A dependency that provides a database session.
    - user_update (UserUpdate): A UserUpdate object containing the updated user information.
    - user (UserIn): A UserIn object containing the user's login information.

    Returns:
    - A dictionary containing a success message and the updated user's information.

    Raises:
    - HTTPException with status code 401 and "Unauthorized, please login" detail if the user is not authenticated.
    - HTTPException with status code 400 and "Something went wrong. Please try again later" detail if a database error occurs.
    """
    try: 
        if not user:
            raise HTTPException(status_code=401, detail="Unauthorized, please login")
        
        db_user = db.query(models.User).filter(models.User.id == user.id).first()

        if user_update.username:
            db_user.username = user_update.username
        if user_update.password:
            db_user.password = get_hash_password(user_update.password)

        db.commit()

        db.refresh(db_user)

        return {
                "status": "ok",
                "data": "Profile updated successfully",
                "user": db_user
            }
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error occurred: {e}")
        raise HTTPException(status_code=400, detail="Something went wrong. Please try again later")