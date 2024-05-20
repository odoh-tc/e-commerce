from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from database import engine
from sqlalchemy.orm import Session
import models
from fastapi import File, UploadFile
import secrets
from PIL import Image
from schema.user import UserIn
from database import get_db
from services.auth import get_current_user
from schema.business import BusinessIn
from schema.user import UserRole



business_router = APIRouter(
    prefix="/business",
    tags=["Business"],
    responses={404: {"description": "Not found"}},
    # summary="API endpoints for managing businesses.",
    # description="This router provides endpoints for creating, retrieving, updating, and deleting businesses."
)

db_dependency = Annotated[Session, Depends(get_db)]

models.Base.metadata.create_all(bind=engine)


@business_router.post("/", status_code=status.HTTP_201_CREATED)
async def create_business(db: db_dependency, business: BusinessIn, user: UserIn = Depends(get_current_user)):
    """
    Create a new business.

    Parameters:
    - db (Session): A database session object.
    - business (BusinessIn): A dictionary containing the business data to be created.
    - user (UserIn): A dictionary containing the user data.

    Returns:
    - dict: A dictionary containing the status, data, and the created business object.

    Raises:
    - HTTPException: If the user role is not 'BUSINESS_OWNER'.
    """
    if user.role != UserRole.BUSINESS_OWNER:
        raise HTTPException(status_code=403, detail="Only business owners can create a business")
    try:
        # Create a new business object
        business_obj = models.Business(**business.model_dump(), owner=user)
        db.add(business_obj)
        db.commit()

        return {"status": "ok", 
                "data": "Business created successfully",
                "business": business_obj}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create business")




@business_router.post("/business_logo/{id}", status_code=status.HTTP_201_CREATED)
async def upload_business_logo(db: db_dependency, id: int, file: UploadFile = File(...), 
                               user: UserIn = Depends(get_current_user)):
    """
    Upload a business logo.

    Parameters:
    - db (Session): A database session object.
    - id (int): The ID of the business to which the logo will be uploaded.
    - file (UploadFile): The file object containing the business logo.
    - user (UserIn): A dictionary containing the user data.

    Returns:
    - dict: A dictionary containing the status, data, and the file URL of the uploaded business logo.

    Raises:
    - HTTPException: If the user role is not 'BUSINESS_OWNER' or if the file extension is not supported.
    """
    if user.role != UserRole.BUSINESS_OWNER:
        raise HTTPException(status_code=403, detail="Only business owners can upload a business logo")
    FILEPATH = "./static/images/"
    filename = file.filename
    extension = filename.split(".")[-1]  # Get the extension
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

    # Resize the image using Pillow
    img = Image.open(generated_name)
    img = img.resize(size=(200, 200))
    img.save(generated_name)

    try:
        business = db.query(models.Business).filter(models.Business.id == id, models.Business.owner == user).first()
        if business:
            business.logo = token_name
            db.commit() 
    except Exception as e:
        db.rollback() 
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update business logo: " + str(e),
        )
    finally:
        db.close()

    file_url = "localhost:8000" + generated_name[1:]
    return {"status": "ok",
            "data": "Business logo uploaded and database updated successfully",
            "file_url": file_url}



@business_router.get("/me", status_code=status.HTTP_200_OK)
async def get_user_business(db: db_dependency, 
                            user: UserIn = Depends(get_current_user),
                            page: int = Query(1, description="Page number", gt=0), 
                            page_size: int = Query(10, description="Number of items per page", gt=0)):
    """
    Retrieve the user's businesses with pagination.

    Parameters:
    - db (Session): A database session object.
    - user (UserIn): A dictionary containing the user data.
    - page (int): The page number.
    - page_size (int): The number of items per page.

    Returns:
    - dict: A dictionary containing the status and the list of businesses owned by the user with pagination.

    Raises:
    - HTTPException: If the user role is not 'BUSINESS_OWNER'.
    """
    if user.role != UserRole.BUSINESS_OWNER:
        raise HTTPException(status_code=403, detail="Only business owners can retrieve their businesses")

    # Calculate the offset based on the page number and page size
    offset = (page - 1) * page_size

    # Query all businesses owned by the user with pagination
    businesses = db.query(models.Business).filter_by(owner=user).offset(offset).limit(page_size).all()

    if businesses:
        business_data_list = []
        # Iterate over each business to retrieve associated products
        for business in businesses:
            products = db.query(models.Product).filter_by(business_id=business.id).all()

            # Serialize the business and product data for each business
            business_data = {
                "business": {
                    "business_id": business.id,
                    "business_name": business.business_name,
                    "city": business.city,
                    "region": business.region,
                    "business_description": business.business_description,
                },
                "products": [product.serialize() for product in products]
            }
            business_data_list.append(business_data)

        return {"status": "ok", "data": business_data_list}
    else:
        raise HTTPException(status_code=404, detail="No businesses found for the user")  





@business_router.put("/{id}", status_code=status.HTTP_200_OK)
async def update_business(db: db_dependency, id: int, 
                          business_update: BusinessIn,
                            user: UserIn = Depends(get_current_user)):
    """
    Update a business object.

    Parameters:
    - db (Session): A database session object.
    - id (int): The ID of the business to be updated.
    - business_update (BusinessIn): A dictionary containing the updated business data.
    - user (UserIn): A dictionary containing the user data.

    Returns:
    - dict: A dictionary containing the status and the updated business object.

    Raises:
    - HTTPException: If the user role is not 'BUSINESS_OWNER' or if the business does not exist.
    """
    if user.role != UserRole.BUSINESS_OWNER:
        raise HTTPException(status_code=403, detail="Only business owners can update their businesses")
    info = business_update.model_dump()
    # Retrieve the business associated with the user
    business = db.query(models.Business).filter_by(id=id).first()
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")
    business_owner = business.owner
    if user == business_owner:
        # Update the business fields
        business.business_name = info["business_name"]
        business.city = info["city"]
        business.region = info["region"]
        business.business_description = info["business_description"]
        db.commit() 
        return {"status": "ok", "data": "Business updated successfully"}
    
    else:
        raise HTTPException(
            status_code=403, 
            detail="You are not authorized to update this business"
        )



@business_router.get("/default", status_code=status.HTTP_200_OK)
async def get_default_business(db: db_dependency, user: UserIn = Depends(get_current_user)):
    """
    Retrieve the default business.

    Parameters:
    - db (Session): A database session object.
    - user (UserIn): A dictionary containing the user data.

    Returns:
    - dict: A dictionary containing the status and the default business object.

    Raises:
    - HTTPException: If the user role is not 'BUSINESS_OWNER'.
    """
    if user.role != UserRole.BUSINESS_OWNER:
        raise HTTPException(status_code=403, detail="Only business owners can access the default business")

    # Query the default business by its name
    default_business = db.query(models.Business).filter_by(business_name='Default Business').first()

    if default_business:
        # Query all products associated with the default business
        products = db.query(models.Product).filter_by(business_id=default_business.id).all()

        # Serialize the business and product data
        business_data = {
            "business": {
                "business_id": default_business.id,
                "business_name": default_business.business_name,
                "city": default_business.city,
                "region": default_business.region,
                "business_description": default_business.business_description,
                # Add other business fields as needed
            },
            "products": [product.serialize() for product in products]
        }

        return {"status": "ok", "data": business_data}
    else:
        raise HTTPException(status_code=404, detail="Default Business not found")


@business_router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_business(db: db_dependency, id: int, 
                          user: UserIn = Depends(get_current_user)):
    """
    Delete a business object.

    Parameters:
    - db (Session): A database session object.
    - id (int): The ID of the business to be deleted.
    - user (UserIn): A dictionary containing the user data.

    Returns:
    - dict: A dictionary containing the status and the message indicating that the business has been deleted successfully.

    Raises:
    - HTTPException: If the user role is not 'BUSINESS_OWNER' or if the business does not exist or if the current user is not the owner of the business.
    """
    if user.role != UserRole.BUSINESS_OWNER:
        raise HTTPException(status_code=403, detail="Only business owners can delete their businesses")
    # Check if the business exists
    business = db.query(models.Business).filter(models.Business.id == id).first()
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

    # Check if the current user is the owner of the business
    if business.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to delete this business")

    # Delete the business from the database
    db.delete(business)
    db.commit()

    return {"status": "ok", "message": "Business deleted successfully"}