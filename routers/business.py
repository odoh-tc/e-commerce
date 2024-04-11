from fastapi import APIRouter, Depends, HTTPException, status
from database import engine
import models
from fastapi import File, UploadFile
import secrets
from PIL import Image
from schema.user import UserIn
from database import session
from services.auth import get_current_user
from schema.business import BusinessIn
from schema.user import UserRole



business_router = APIRouter(
    prefix="/business",
    tags=["Business"],
    responses={404: {"description": "Not found"}},
)


models.Base.metadata.create_all(bind=engine)


@business_router.post("/", status_code=status.HTTP_201_CREATED)
async def create_business(business: BusinessIn, user: UserIn = Depends(get_current_user)):
    if user.role != UserRole.BUSINESS_OWNER:
        raise HTTPException(status_code=403, detail="Only business owners can create a business")
    try:
        # Create a new business object
        business_obj = models.Business(**business.model_dump(), owner=user)
        session.add(business_obj)
        session.commit()

        return {"status": "ok", 
                "data": "Business created successfully",
                "business": business_obj}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail="Failed to create business")




@business_router.post("/business_logo/{id}", status_code=status.HTTP_201_CREATED)
async def upload_business_logo(id: int, file: UploadFile = File(...), 
                               user: UserIn = Depends(get_current_user)):
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
        business = session.query(models.Business).filter(models.Business.id == id, models.Business.owner == user).first()
        if business:
            business.logo = token_name
            session.commit() 
    except Exception as e:
        session.rollback() 
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update business logo: " + str(e),
        )
    finally:
        session.close()

    file_url = "localhost:8000" + generated_name[1:]
    return {"status": "ok",
            "data": "Business logo uploaded and database updated successfully",
            "file_url": file_url}


@business_router.get("/me", status_code=status.HTTP_200_OK)
async def get_user_business(user: UserIn = Depends(get_current_user)):
    if user.role != UserRole.BUSINESS_OWNER:
        raise HTTPException(status_code=403, detail="Only business owners can retrieve their businesses")

    # Query all businesses owned by the user
    businesses = session.query(models.Business).filter_by(owner=user).all()

    if businesses:
        business_data_list = []
        # Iterate over each business to retrieve associated products
        for business in businesses:
            products = session.query(models.Product).filter_by(business_id=business.id).all()

            # Serialize the business and product data for each business
            business_data = {
                "business": {
                    "id": business.id,
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
async def update_business(id: int, 
                          business_update: BusinessIn,
                            user: UserIn = Depends(get_current_user)):
    if user.role != UserRole.BUSINESS_OWNER:
        raise HTTPException(status_code=403, detail="Only business owners can update their businesses")
    info = business_update.model_dump()
    # Retrieve the business associated with the user
    business = session.query(models.Business).filter_by(id=id).first()
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")
    business_owner = business.owner
    if user == business_owner:
        # Update the business fields
        business.business_name = info["business_name"]
        business.city = info["city"]
        business.region = info["region"]
        business.business_description = info["business_description"]
        session.commit() 
        return {"status": "ok", "data": "Business updated successfully"}
    
    else:
        raise HTTPException(
            status_code=403, 
            detail="You are not authorized to update this business"
        )



@business_router.get("/default", status_code=status.HTTP_200_OK)
async def get_default_business(user: UserIn = Depends(get_current_user)):
    if user.role != UserRole.BUSINESS_OWNER:
        raise HTTPException(status_code=403, detail="Only business owners can access the default business")

    # Query the default business by its name
    default_business = session.query(models.Business).filter_by(business_name='Default Business').first()

    if default_business:
        # Query all products associated with the default business
        products = session.query(models.Product).filter_by(business_id=default_business.id).all()

        # Serialize the business and product data
        business_data = {
            "business": {
                "id": default_business.id,
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
async def delete_business(id: int, 
                          user: UserIn = Depends(get_current_user)):
    if user.role != UserRole.BUSINESS_OWNER:
        raise HTTPException(status_code=403, detail="Only business owners can delete their businesses")
    # Check if the business exists
    business = session.query(models.Business).filter(models.Business.id == id).first()
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

    # Check if the current user is the owner of the business
    if business.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to delete this business")

    # Delete the business from the database
    session.delete(business)
    session.commit()

    return {"status": "ok", "message": "Business deleted successfully"}

