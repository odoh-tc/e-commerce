from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Query, status
from database import engine
import models
from database import get_db
from schema.order import OrderIn, OrderStatus
from schema.user import UserIn, UserRole
from services.auth import get_current_user



db_dependency = Annotated[Session, Depends(get_db)]


order_router = APIRouter(
    prefix="/order",
    tags=["Order"],
    responses={404: {"description": "Not found"}},
    # summary="API endpoints for managing orders.",
    # description="This router provides endpoints for creating, retrieving, updating, and deleting orders."
)

models.Base.metadata.create_all(bind=engine)



@order_router.post("/", status_code=status.HTTP_201_CREATED)
async def create_order(db: db_dependency, order: OrderIn, user: UserIn = Depends(get_current_user)):
    """
     Create a new order.

    This endpoint allows a customer to create a new order by specifying the product and quantity.
    The total price is calculated based on the product's price and the quantity ordered. The product
    quantity is also adjusted based on the order.

    Args:
        db (Session): Database session dependency.
        order (OrderIn): Pydantic model containing order details.
        user (UserIn): The current user, retrieved through dependency injection.

    Returns:
        dict: A response dict with status, message, and serialized order data.

    Raises:
        HTTPException: If the user is not a customer (403).
        HTTPException: If the product is not found (404).
        HTTPException: If the product is out of stock (400).
    """
    if user.role != UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="Only customers can create an order")
    
    product = db.query(models.Product).filter_by(id=order.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.quantity < 1:
        raise HTTPException(status_code=400, detail="Product out of stock")

    # Calculate the total price based on the product's price and the quantity
    order_total_price = product.new_price * order.quantity

    # Deduct product quantity
    product.quantity -= order.quantity

    new_order = models.Order(
        product_id=order.product_id,
        user_id=user.id,
        total_price=order_total_price,
        status=OrderStatus.pending
    )
    
    db.add(new_order)
    db.commit()

    # Serialize the new_order object
    serialized_order = new_order.serialize()

    return {"status": "ok", "data": "Order created successfully", "order": serialized_order}


@order_router.put("/status/{id}", status_code=status.HTTP_200_OK)
async def update_order_status(db: db_dependency, id: int, status: OrderStatus, 
                              user: UserIn = Depends(get_current_user)):
    """
    Update the status of an order.

    This endpoint allows a business owner to update the status of an order associated with their products.
    The business owner must be the owner of the business associated with the product in the order.

    Args:
        db (Session): Database session dependency.
        id (int): The ID of the order to update.
        status (OrderStatus): The new status for the order.
        user (UserIn): The current user, retrieved through dependency injection.

    Returns:
        dict: A response dict with status, message, and serialized order data.

    Raises:
        HTTPException: If the user is not a business owner (403).
        HTTPException: If the order is not found (404).
        HTTPException: If the user is not the owner of the business associated with the product in the order (403).
    """
    # Check if the user is a business owner
    if user.role != UserRole.BUSINESS_OWNER:
        raise HTTPException(status_code=403, detail="Only business owners can update the status of their orders")

    # Query the order to update
    order_to_update = db.query(models.Order).filter_by(id=id).first()
    if not order_to_update:
        raise HTTPException(status_code=404, detail="Order not found")

    # Query the product associated with the order
    product = order_to_update.product

    # Check if the user is the owner of the business associated with the product
    if user.id != product.business.owner_id:
        raise HTTPException(status_code=403, detail="Only the owner of the business can update the status of orders related to their products")

    # Update the order status
    order_to_update.status = status
    db.commit()

    return {"status": "ok", "data": "Order status updated successfully",
            "order": order_to_update.serialize()}




@order_router.get("/", status_code=status.HTTP_200_OK)
async def get_all_orders(db: db_dependency, 
                         user: UserIn = Depends(get_current_user),
                         page: int = Query(1, description="Page number", gt=0), 
                         page_size: int = Query(10, description="Number of items per page", gt=0)):
    """
    Retrieve all orders for a customer with pagination.

    This endpoint allows a customer to retrieve their orders with pagination support. The user can
    specify the page number and the number of items per page.

    Args:
        db (Session): Database session dependency.
        user (UserIn): The current user, retrieved through dependency injection.
        page (int): The page number to retrieve, defaults to 1.
        page_size (int): The number of items per page, defaults to 10.

    Returns:
        dict: A response dict with status and a list of serialized orders.

    Raises:
        HTTPException: If the user is not a customer (403).

    """ 
    if user.role != UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="Only customers can retrieve their orders")

    # Calculate the offset based on the page number and page size
    offset = (page - 1) * page_size
    
    # Query all orders associated with the user with pagination
    user_orders = db.query(models.Order).filter_by(user_id=user.id).offset(offset).limit(page_size).all()

    serialized_orders = [order.serialize() for order in user_orders]

    return {"status": "ok", "data": serialized_orders}




@order_router.put("/{id}", status_code=status.HTTP_200_OK)
async def update_order(db: db_dependency, id: int, order: OrderIn, user: UserIn = Depends(get_current_user)):

    """
    Update the quantity of an order.

    This endpoint allows a customer to update the quantity of an order they have placed.

    Args:
        db (Session): Database session dependency.
        id (int): The ID of the order to update.
        order (OrderIn): Pydantic model containing the new order details.
        user (UserIn): The current user, retrieved through dependency injection.

    Returns:
        dict: A response dict with status and serialized updated order data.

    Raises:
        HTTPException: If the user is not a customer (403).
        HTTPException: If the order is not found (404).

    """
    if user.role != UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="Only customers can update their orders")

    order_to_update = db.query(models.Order).filter_by(id=id).first()
    if not order_to_update:
        raise HTTPException(status_code=404, detail="Order not found")
    


    order_to_update.quantity = order.quantity

    db.commit()

    return {"status": "ok", "data": "Order updated successfully",
            "order": order_to_update.serialize()}




@order_router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_order(db: db_dependency, id: int, user: UserIn = Depends(get_current_user)):

    """
    Delete an order.

    This endpoint allows a customer to delete an order they have placed. Only the customer who 
    placed the order can delete it.

    Args:
        db (Session): Database session dependency.
        id (int): The ID of the order to delete.
        user (UserIn): The current user, retrieved through dependency injection.

    Returns:
        dict: A response dict with status and a confirmation message.

    Raises:
        HTTPException: If the user is not a customer (403).
        HTTPException: If the order is not found (404).

    """
    # Check if the user is a customer
    if user.role != UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="Only customers can delete their orders")
    
    order = db.query(models.Order).filter_by(id=id, user_id=user.id).first()
    
    # If the order does not exist or does not belong to the user, raise an HTTPException
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Delete the order
    db.delete(order)
    db.commit()
    
    return {"status": "ok", "data": "Order deleted successfully"}


