from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
import models
from schema.order import OrderStatus
from services.auth import get_current_user
from schema.user import UserIn, UserRole
from database import get_db
from logger import logger
from database import engine


admin_router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    responses={404: {"description": "Not found"}},
    # summary="API endpoints for admin operations.",
    # description="This router provides endpoints for performing administrative tasks, such as managing users and roles."
)

models.Base.metadata.create_all(bind=engine)

db_dependency = Annotated[Session, Depends(get_db)]


@admin_router.get("/", status_code=status.HTTP_200_OK)
async def list_users(
    db: db_dependency,
    page: int = Query(1, description="Page number", gt=0),
    page_size: int = Query(10, description="Number of items per page", gt=0),
    user: UserIn = Depends(get_current_user),
):
    """
    Retrieves a list of users with pagination. Only admins can access this endpoint.

    Args:
    db (Session): A database session object.
    page (int): The page number to retrieve. Defaults to 1.
    page_size (int): The number of items per page. Defaults to 10.
    user (UserIn): The authenticated user object.

    Returns:
    List[models.User]: A list of users.

    Raises:
    HTTPException: If the user is not an admin or if a database error occurs.
    """
    try:
        if user is None or user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Only admins can access this endpoint")

        # Calculate the offset based on the page number and page size
        offset = (page - 1) * page_size

        # Query users with pagination
        users = db.query(models.User).offset(offset).limit(page_size).all()

        if not users:
            return {
                "status": "ok",
                "message": "No users found"
            }

        return users

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error occurred: {e}")
        raise HTTPException(status_code=400, detail="Something went wrong. Please try again later")



@admin_router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_user(db: db_dependency, id: int, user: UserIn = Depends(get_current_user)):
    """
    Deletes a user by id. Only admins can access this endpoint.

    Args:
    db (Session): A database session object.
    id (int): The id of the user to be deleted.
    user (UserIn): The authenticated user object.

    Returns:
    dict: A dictionary containing a success message if the user is deleted successfully.

    Raises:
    HTTPException: If the user is not an admin or if a database error occurs.
    """
    try:
        if user is None or user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Only admins can access this endpoint")
        
        user_to_delete = db.query(models.User).filter_by(id=id).first()

        if not user_to_delete:
            raise HTTPException(status_code=404, detail="User not found")

        db.delete(user_to_delete)
        db.commit()

        return {
            "status": "ok",
            "message": "User deleted successfully"
        }

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error occurred: {e}")
        raise HTTPException(status_code=400, detail="Something went wrong. Please try again later")



@admin_router.get("/get_products", status_code=status.HTTP_200_OK)
async def list_products( db: db_dependency,
                         page: int = Query(1, description="Page number", gt=0), 
                        page_size: int = Query(10, description="Number of items per page", gt=0),
                       user: UserIn = Depends(get_current_user)):
    
    """
    Retrieves a list of products with pagination. Only admins can access this endpoint.

    Args:
    db (Session): A database session object.
    page (int): The page number to retrieve. Defaults to 1.
    page_size (int): The number of items per page. Defaults to 10.
    user (UserIn): The authenticated user object.

    Returns:
    List[models.Product]: A list of products.

    Raises:
    HTTPException: If the user is not an admin or if a database error occurs.
    """
    
    try:
        if user is None or user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Only admins can access this endpoint")
        
        # Calculate the offset based on the page number and page size
        offset = (page - 1) * page_size
        
        # Query products with pagination
        products = db.query(models.Product).offset(offset).limit(page_size).all()

        if not products:
            return {
                "status": "ok",
                "message": "No products found"
            }

        return products
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error occurred: {e}")
        raise HTTPException(status_code=400, detail="Something went wrong. Please try again later")


@admin_router.delete("/delete_products/{id}", status_code=status.HTTP_200_OK)
async def delete_products(db: db_dependency, id: int, user: UserIn = Depends(get_current_user)):
    """
    Deletes a product by id. Only admins can access this endpoint.

    Args:
    db (Session): A database session object.
    id (int): The id of the product to be deleted.
    user (UserIn): The authenticated user object.

    Returns:
    dict: A dictionary containing a success message if the product is deleted successfully.

    Raises:
    HTTPException: If the user is not an admin or if a database error occurs.
    """
    try:
        if user is None or user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Only admins can access this endpoint")
        
        product_to_delete = db.query(models.Product).filter_by(id=id).first()

        if not product_to_delete:
            raise HTTPException(status_code=404, detail="Product not found")

        db.delete(product_to_delete)
        db.commit()

        return {
            "status": "ok",
            "message": "Product deleted successfully"
        }

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error occurred: {e}")
        raise HTTPException(status_code=400, detail="Something went wrong. Please try again later")



@admin_router.get("/get_orders", status_code=status.HTTP_200_OK)
async def list_orders(db: db_dependency, page: int = Query(1, description="Page number", gt=0), 
                      page_size: int = Query(10, description="Number of items per page", gt=0)
                      ,user: UserIn = Depends(get_current_user)):
    
    """

    Retrieves a list of orders with pagination. Only admins can access this endpoint.

    Args:
    db (Session): A database session object.
    page (int): The page number to retrieve. Defaults to 1.
    page_size (int): The number of items per page. Defaults to 10.
    user (UserIn): The authenticated user object.

    Returns:
    List[models.Order]: A list of orders.

    Raises:
    HTTPException: If the user is not an admin or if a database error occurs.
    """
    try: 
        if user is None or user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Only admins can access this endpoint")
        
        # Calculate the offset based on the page number and page size
        offset = (page - 1) * page_size
        
        # Query orders with pagination
        orders = db.query(models.Order).offset(offset).limit(page_size).all()

        if not orders:
            return {
                "status": "ok",
                "message": "No orders found"
            }

        return orders
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error occurred: {e}")
        raise HTTPException(status_code=400, detail="Something went wrong. Please try again later")




@admin_router.put("/{id}", status_code=status.HTTP_200_OK)
async def update_order_status(
    db: db_dependency,
    id: int,
    new_status: OrderStatus,
    user: UserIn = Depends(get_current_user),
):
    """
    Updates the status of an order by its ID. Only admins can access this endpoint.

    Args:
    db (Session): A database session object.
    id (int): The ID of the order to be updated.
    new_status (OrderStatus): The new status of the order.
    user (UserIn): The authenticated user object.

    Returns:
    dict: A dictionary containing a success message if the order status is updated successfully.

    Raises:
    HTTPException: If the user is not an admin or if a database error occurs.
    """
    try:
        if user is None or user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Only admins can access this endpoint")
        
        order_to_update = db.query(models.Order).filter_by(id=id).first()

        if not order_to_update:
            raise HTTPException(status_code=404, detail="Order not found")

        order_to_update.status = new_status
        db.commit()

        return {
            "status": "ok",
            "message": "Order status updated successfully"
        }

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error occurred: {e}")
        raise HTTPException(status_code=400, detail="Something went wrong. Please try again later")
















