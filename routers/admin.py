from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
import models
from schema.order import OrderStatus
from services.auth import get_current_user, get_hash_password, send_email
from schema.user import UserIn, UserRole, UserUpdate
from services.user import is_email_exists, is_username_exists
from database import session
from logger import logger
from database import engine


admin_router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses={404: {"description": "Not found"}},
)
models.Base.metadata.create_all(bind=engine)

@admin_router.get("/", status_code=status.HTTP_200_OK)
async def list_users(user: UserIn = Depends(get_current_user)):
    try:
        if user is None or user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Only admins can access this endpoint")
        
        users = session.query(models.User).all()

        if not users:
            return {
                "status": "ok",
                "message": "No users found"
            }

        return users
    
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error occurred: {e}")
        raise HTTPException(status_code=400, detail="Something went wrong. Please try again later")



@admin_router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_user(id: int, user: UserIn = Depends(get_current_user)):
    try:
        if user is None or user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Only admins can access this endpoint")
        
        user_to_delete = session.query(models.User).filter_by(id=id).first()

        if not user_to_delete:
            raise HTTPException(status_code=404, detail="User not found")

        session.delete(user_to_delete)
        session.commit()

        return {
            "status": "ok",
            "message": "User deleted successfully"
        }
    
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error occurred: {e}")
        raise HTTPException(status_code=400, detail="Something went wrong. Please try again later")



@admin_router.get("/get_products", status_code=status.HTTP_200_OK)
async def list_products(user: UserIn = Depends(get_current_user)):
    try:
        if user is None or user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Only admins can access this endpoint")
        
        products = session.query(models.Product).all()

        if not products:
            return {
                "status": "ok",
                "message": "No products found"
            }

        return products
    
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error occurred: {e}")
        raise HTTPException(status_code=400, detail="Something went wrong. Please try again later")



@admin_router.delete("/delete_products/{id}", status_code=status.HTTP_200_OK)
async def delete_products(id: int, user: UserIn = Depends(get_current_user)):
    try:
        if user is None or user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Only admins can access this endpoint")
        
        product_to_delete = session.query(models.Product).filter_by(id=id).first()

        if not product_to_delete:
            raise HTTPException(status_code=404, detail="Product not found")

        session.delete(product_to_delete)
        session.commit()

        return {
            "status": "ok",
            "message": "Product deleted successfully"
        }
    
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error occurred: {e}")
        raise HTTPException(status_code=400, detail="Something went wrong. Please try again later")



@admin_router.get("/get_orders", status_code=status.HTTP_200_OK)
async def list_orders(user: UserIn = Depends(get_current_user)):
    try: 
        if user is None or user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Only admins can access this endpoint")
        
        orders = session.query(models.Order).all()

        if not orders:
            return {
                "status": "ok",
                "message": "No orders found"
            }

        return orders
    
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error occurred: {e}")
        raise HTTPException(status_code=400, detail="Something went wrong. Please try again later")





@admin_router.put("/{id}", status_code=status.HTTP_200_OK)
async def update_order_status(id: int, new_status: OrderStatus, user: UserIn = Depends(get_current_user)):
    try:
        if user is None or user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Only admins can access this endpoint")
        
        order_to_update = session.query(models.Order).filter_by(id=id).first()

        if not order_to_update:
            raise HTTPException(status_code=404, detail="Order not found")

        order_to_update.status = new_status
        session.commit()

        return {
            "status": "ok",
            "message": "Order status updated successfully"
        }
    
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error occurred: {e}")
        raise HTTPException(status_code=400, detail="Something went wrong. Please try again later")


















