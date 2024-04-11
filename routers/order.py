from fastapi import APIRouter, Depends, HTTPException, status
from database import engine
import models
from database import session
from schema.order import OrderIn, OrderStatus
from schema.user import UserIn, UserRole
from services.auth import get_current_user





order_router = APIRouter(
    prefix="/order",
    tags=["Order"],
    responses={404: {"description": "Not found"}},
)

models.Base.metadata.create_all(bind=engine)



@order_router.post("/", status_code=status.HTTP_201_CREATED)
async def create_order(order: OrderIn, user: UserIn = Depends(get_current_user)):
    if user.role != UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="Only customers can create an order")
    
    product = session.query(models.Product).filter_by(id=order.product_id).first()
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
    
    session.add(new_order)
    session.commit()

    # Serialize the new_order object
    serialized_order = new_order.serialize()

    return {"status": "ok", "data": "Order created successfully", "order": serialized_order}


@order_router.put("/status/{id}", status_code=status.HTTP_200_OK)
async def update_order_status(id: int, status: OrderStatus, 
                              user: UserIn = Depends(get_current_user)):
    # Check if the user is a business owner
    if user.role != UserRole.BUSINESS_OWNER:
        raise HTTPException(status_code=403, detail="Only business owners can update the status of their orders")

    # Query the order to update
    order_to_update = session.query(models.Order).filter_by(id=id).first()
    if not order_to_update:
        raise HTTPException(status_code=404, detail="Order not found")

    # Query the product associated with the order
    product = order_to_update.product

    # Check if the user is the owner of the business associated with the product
    if user.id != product.business.owner_id:
        raise HTTPException(status_code=403, detail="Only the owner of the business can update the status of orders related to their products")

    # Update the order status
    order_to_update.status = status
    session.commit()

    return {"status": "ok", "data": "Order status updated successfully",
            "order": order_to_update.serialize()}


@order_router.get("/", status_code=status.HTTP_200_OK)
async def get_all_orders(user: UserIn = Depends(get_current_user)):
    if user.role != UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="Only customers can retrieve their orders")
    # Query all orders associated with the user
    user_orders = session.query(models.Order).filter_by(user_id=user.id).all()

    serialized_orders = [order.serialize() for order in user_orders]

    return {"status": "ok", "data": serialized_orders}



@order_router.put("/{id}", status_code=status.HTTP_200_OK)
async def update_order(id: int, order: OrderIn, user: UserIn = Depends(get_current_user)):
    if user.role != UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="Only customers can update their orders")

    order_to_update = session.query(models.Order).filter_by(id=id).first()
    if not order_to_update:
        raise HTTPException(status_code=404, detail="Order not found")
    


    order_to_update.quantity = order.quantity

    session.commit()

    return {"status": "ok", "data": "Order updated successfully",
            "order": order_to_update.serialize()}


@order_router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_order(id: int, user: UserIn = Depends(get_current_user)):
    # Check if the user is a customer
    if user.role != UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="Only customers can delete their orders")
    
    order = session.query(models.Order).filter_by(id=id, user_id=user.id).first()
    
    # If the order does not exist or does not belong to the user, raise an HTTPException
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Delete the order
    session.delete(order)
    session.commit()
    
    return {"status": "ok", "data": "Order deleted successfully"}


