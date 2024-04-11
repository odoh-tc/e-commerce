from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
import models
from services.auth import get_current_user, get_hash_password, send_email
from schema.user import UserIn, UserRole, UserUpdate
from services.user import is_email_exists, is_username_exists
from database import session
from logger import logger
from database import engine


user_router = APIRouter(
    prefix="/user",
    tags=["User"],
    responses={404: {"description": "Not found"}},
)
models.Base.metadata.create_all(bind=engine)


@user_router.post('/registration', status_code=status.HTTP_201_CREATED)
async def user_registration(user: UserIn):
    try: 
        user_info = user.model_dump()
        user_info["password"] = get_hash_password(user.password)
        user_info["role"] = user.role.value

        new_user = models.User(**user_info)

        if is_username_exists(user.username):
            raise HTTPException(status_code=400, detail="Username already exists")
        if is_email_exists(user.email):
            raise HTTPException(status_code=400, detail="Email already exists")
        
        session.add(new_user)
        session.commit()

        # Send email for verification
        await send_email(user.email, new_user)

        return {
                "status": "ok",
                "data": f"Hello {new_user.username}, Thanks for choosing our services. Please check your email inbox and click on the link to confirm your registration"
            }
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error occurred: {e}")
        raise HTTPException(status_code=400, detail="Something went wrong. Please try again later")
    





@user_router.post('/me', status_code=status.HTTP_201_CREATED)
async def user_login(user: UserIn = Depends(get_current_user)):
    # If user is a BUSINESS_OWNER
    if user.role == UserRole.BUSINESS_OWNER:
        # Retrieve businesses associated with the user
        businesses = session.query(models.Business).filter(models.Business.owner_id == user.id).all()

        # Initialize list to hold business data
        business_data = []

        # If there are no businesses, return empty business_data
        if not businesses:
            business_data = []
        else:
            # Iterate over each business
            for business in businesses:
                # Retrieve products associated with the business
                products = session.query(models.Product).filter(models.Product.business_id == business.id).all()

                # Construct business details dictionary
                business_details = {
                    "business_name": business.business_name,
                    "city": business.city,
                    "region": business.region,
                    "business_description": business.business_description,
                    "logo": "localhost:8000/static/images/" + business.logo,
                }

                # Serialize products
                serialized_products = [product.serialize() for product in products]

                # Append business details along with products to business_data
                business_data.append({
                    "business_details": business_details,
                    "products": serialized_products
                })

        # Construct user details dictionary
        user_details = {
            "username": user.username,
            "email": user.email,
            "verified": user.is_verified,
            "joined_date": user.join_date.strftime("%b %d %Y %H:%M:%S"),
        }

        return {
            "status": "ok",
            "data": {
                "user_details": user_details,
                "businesses": business_data
            }
        }
    
    elif user.role == UserRole.CUSTOMER:
        # Retrieve orders associated with the user
        orders = session.query(models.Order).filter(models.Order.user_id == user.id).all()

        user_details = {
            "username": user.username,
            "email": user.email,
            "verified": user.is_verified,
            "joined_date": user.join_date.strftime("%b %d %Y %H:%M:%S"),
        }

        # If orders exist, serialize them
        if orders:
            serialized_orders = [order.serialize() for order in orders]
            return {
                "status": "ok",
                "data": {
                    "user_details": user_details,
                    "orders": serialized_orders
                }
            }
        # If no orders exist, return empty orders list
        else:
            return {
                "status": "ok",
                "data": {
                    "user_details": user_details,
                    "orders": []
                }
            }



@user_router.put('/', status_code=status.HTTP_200_OK)
async def update_profile(user_update: UserUpdate, 
                         user: UserIn = Depends(get_current_user)):
    
    try: 
    
        if not user:
            raise HTTPException(status_code=401, detail="Unauthorized, please login")
        
        db_user = session.query(models.User).filter(models.User.id == user.id).first()

        if user_update.username:
            db_user.username = user_update.username
        if user_update.password:
            db_user.password = get_hash_password(user_update.password)

        session.commit()

        session.refresh(db_user)

        return {
                "status": "ok",
                "data": "Profile updated successfully",
                "user": db_user
            }
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error occurred: {e}")
        raise HTTPException(status_code=400, detail="Something went wrong. Please try again later")

    