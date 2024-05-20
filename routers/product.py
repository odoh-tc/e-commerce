from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from database import engine
from sqlalchemy.orm import Session
import models
from fastapi import File, UploadFile
import secrets
from PIL import Image
from schema.product import ProductIn, ProductUpdate
from schema.user import UserIn, UserRole
from database import get_db
from services.auth import get_current_user




product_router = APIRouter(
    prefix="/product",
    tags=["Product"],
    responses={404: {"description": "Not found"}},
    # summary="API endpoints for managing products.",
    # description="This router provides endpoints for creating, retrieving, updating, and deleting products."
)


db_dependency = Annotated[Session, Depends(get_db)]
models.Base.metadata.create_all(bind=engine)

@product_router.post("/products")
async def add_new_product(db: db_dependency, product: ProductIn, user: UserIn = Depends(get_current_user)):

    """
    Add a new product.

    This endpoint allows a business owner to add a new product. If no specific business is 
    associated with the product, it will be added to a default business entity.

    Args:
        db (Session): Database session dependency.
        product (ProductIn): Pydantic model containing product details.
        user (UserIn): The current user, retrieved through dependency injection.

    Returns:
        dict: A response dict with status, message, and serialized product data.

    """
    if user.role != UserRole.BUSINESS_OWNER:
        raise HTTPException(status_code=403, detail="Only business owners can add a new product")

    product_data = product.model_dump()
    if product_data["original_price"] > 0:
        product_data["percentage_discount"] = ((product_data["original_price"] - product_data["new_price"]) / product_data["original_price"]) * 100

        product_obj = models.Product(**product_data)
        
        # Fetch or create the default business
        default_business = db.query(models.Business).filter_by(business_name='Default Business').first()
        if not default_business:
            default_business = models.Business(
                business_name="Default Business",
                city="Unspecified",
                region="Unspecified",
                business_description="Default business entity for products without specified business",
                logo="default_logo.jpg",
            )
            db.add(default_business)
            db.commit()

        # Check if the product includes the business_id
        if "business_id" in product_data and product_data["business_id"]:
            business_id = product_data["business_id"]
            # Fetch the business associated with the provided business_id
            business = db.query(models.Business).filter_by(id=business_id).first()
            if not business:
                raise HTTPException(status_code=404, detail="Business not found with the provided business_id")
        else:
            # If no business_id provided, associate product with default business
            business = default_business

        # Check if the business is the default business
        is_default_business = business.business_name == 'Default Business'

        # If it's the default business and it doesn't have an owner, skip authorization check
        if is_default_business and not business.owner_id:
            product_obj.business = business
        else:
            # Check if the business belongs to the current user
            if business.owner_id != user.id:
                raise HTTPException(status_code=403, detail="You are not authorized to associate a product with this business")
            product_obj.business = business

        db.add(product_obj)
        db.commit()

        # Serialize the product object for response
        product_data = product_obj.serialize()

        return {
            "status": "ok",
            "data": "Product added successfully",
            "product": product_data
        }
    else:
        raise HTTPException(status_code=400, detail="Original price cannot be 0")




@product_router.get("/", status_code=status.HTTP_200_OK)
async def get_all_products(db: db_dependency, 
                           user: UserIn = Depends(get_current_user),
                           page: int = Query(1, description="Page number", gt=0), 
                           page_size: int = Query(10, description="Number of items per page", gt=0)):
    
    """
    Retrieve all products with pagination.

    This endpoint allows an authenticated user to retrieve a paginated list of all products. 
    The user can specify the page number and the number of items per page.

    Args:
        db (Session): Database session dependency.
        user (UserIn): The current user, retrieved through dependency injection.
        page (int): The page number to retrieve, defaults to 1.
        page_size (int): The number of items per page, defaults to 10.

    Returns:
        dict: A response dict with status and a list of product data.

    Raises:
        HTTPException: If the user is not authenticated (401).

    """
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized, please login")

    # Calculate the offset based on the page number and page size
    offset = (page - 1) * page_size
    
    # Query all products with pagination
    products = db.query(models.Product).offset(offset).limit(page_size).all()

    return {
        "status": "ok",
        "data": products
    }


@product_router.get("/{id}", status_code=status.HTTP_200_OK)
async def get_specific_product(db: db_dependency, id: int,
                               user: UserIn = Depends(get_current_user)):

    """
    Retrieve specific product details.

    This endpoint allows an authenticated user to retrieve details of a specific product by its ID.
    It also includes information about the business that owns the product.

    Args:
        db (Session): Database session dependency.
        id (int): The ID of the product to retrieve.
        user (UserIn): The current user, retrieved through dependency injection.

    Returns:
        dict: A response dict with status, product data, and business details.

    Raises:
        HTTPException: If the user is not authenticated (401).
        HTTPException: If the product is not found (404).
        HTTPException: If the business associated with the product is not found (404).

    """

    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized, please login")

    product = db.query(models.Product).filter_by(id=id).first()

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    business = db.query(models.Business).filter_by(id=product.business_id).first()
    if business is None:
        raise HTTPException(status_code=404, detail="Business not found for the product")

    if business.owner:
        owner_email = business.owner.email
    else:
        owner_email = None

    return {
        "status": "ok",
        "data": product.serialize(),
        "business_details": {
            "name": business.business_name,
            "city": business.city,
            "region": business.region,
            "description": business.business_description,
            "logo": business.logo,
            "business_id": business.id,
            "owner_id": business.owner_id,
            "email": owner_email,
            "join_date": business.owner.join_date.strftime("%b %d %Y %H:%M:%S") if business.owner else None
        },
    }







@product_router.post("/product_image/{id}",status_code=status.HTTP_201_CREATED)
async def upload_product_image(db: db_dependency, id: int, file: UploadFile = File(...),
                             user: UserIn = Depends(get_current_user)):
    
    """
    Upload a product image.

    This endpoint allows an authenticated business owner to upload an image for a specific product.
    The image is resized to 200x200 pixels before being saved.

    Args:
        db (Session): Database session dependency.
        id (int): The ID of the product to associate the image with.
        file (UploadFile): The image file to upload.
        user (UserIn): The current user, retrieved through dependency injection.

    Returns:
        dict: A response dict with status, a message, and the URL of the uploaded image.

    Raises:
        HTTPException: If the user is not a business owner (403).
        HTTPException: If the file extension is not supported (400).
        HTTPException: If the user is not the owner of the product (403).
        HTTPException: If the product is not found (404).
        HTTPException: If there is an error updating the database (500).

    """
    if user.role != UserRole.BUSINESS_OWNER:
        raise HTTPException(status_code=403, detail="Only business owners can upload product pictures")

    FILEPATH = "./static/images/"
    filename = file.filename
    extension = filename.split(".")[-1]
    if extension not in ["jpg", "png"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File extension not supported",
        )

    token_name = secrets.token_hex(10) + "." + extension
    generated_name = FILEPATH + token_name
    file_content = await file.read()

    with open(generated_name, "wb") as f:
        f.write(file_content)


    img = Image.open(generated_name)
    img = img.resize(size=(200, 200))
    img.save(generated_name)

    try:
        product = db.query(models.Product).filter(models.Product.id == id).first()
        if product:
            business = product.business
            owner = business.owner
            if user == owner:
                product.product_image = token_name
                db.commit() 
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not the owner of this product",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update database: " + str(e),
        )
    finally:
        db.close()

    file_url = "localhost:8000" + generated_name[1:]
    return {
        "status": "ok",
        "data": "File uploaded and database updated successfully",
        "file_url": file_url
    }

    

@product_router.put("/{id}", status_code=status.HTTP_200_OK)
async def update_product(db: db_dependency, id: int, product_update: ProductUpdate, user: UserIn = Depends(get_current_user)):

    """
    Update a product.

    This endpoint allows an authenticated business owner to update details of a specific product.

    Args:
        db (Session): Database session dependency.
        id (int): The ID of the product to update.
        product_update (ProductUpdate): The updated product information.
        user (UserIn): The current user, retrieved through dependency injection.

    Returns:
        dict: A response dict with status, a message, and the updated product data.

    Raises:
        HTTPException: If the user is not a business owner (403).
        HTTPException: If the product is not found (404).
        HTTPException: If the business associated with the product is not found (404).
        HTTPException: If the user is not the owner of the product's business (403).
        HTTPException: If there is an error updating the database (500).
    """
    if user.role != UserRole.BUSINESS_OWNER:
        raise HTTPException(status_code=403, detail="Only business owners can update a product")
    # Retrieve the product from the database
    product = db.query(models.Product).filter_by(id=id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    # Retrieve the associated business
    business = db.query(models.Business).filter_by(id=product.business_id).first()
    if business is None:
        raise HTTPException(status_code=404, detail="Business not found for the product")

    # Ensure that the user is the owner of the product's business
    if user != business.owner:
        raise HTTPException(
            status_code=403, 
            detail="You are not authorized to update this product"
        )

    product.name = product_update.name
    if product_update.original_price > 0:
        product.percentage_discount = ((product_update.original_price - product_update.new_price) / product_update.original_price) * 100
    product.category = product_update.category

    db.commit() 
    return {
        "status": "ok", 
        "data": "Product updated successfully",
        "product": product.serialize()
        }



@product_router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_product(db: db_dependency, id: int, user: UserIn = Depends(get_current_user)):

    """
    Delete a product.

    This endpoint allows an authenticated business owner to delete a specific product.

    Args:
        db (Session): Database session dependency.
        id (int): The ID of the product to delete.
        user (UserIn): The current user, retrieved through dependency injection.

    Returns:
        dict: A response dict with status and a message indicating the deletion success.

    Raises:
        HTTPException: If the user is not a business owner (403).
        HTTPException: If the product is not found (404).
        HTTPException: If the business associated with the product is not found (404).
        HTTPException: If the user is not the owner of the product's business (403).

    """
    if user.role != UserRole.BUSINESS_OWNER:
        raise HTTPException(status_code=403, detail="Only business owners can delete a product")
    product = db.query(models.Product).filter_by(id=id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    business = db.query(models.Business).filter_by(id=product.business_id).first()
    if business is None:
        raise HTTPException(status_code=404, detail="Business not found for the product")

    owner = business.owner
    if user == owner:
        db.delete(product)  
        db.commit() 
        return {"status": "ok", "data": "Product deleted successfully"}
    else:
        raise HTTPException(
            status_code=403, 
            detail="You are not authorized to delete this product"
        )





