from fastapi import APIRouter, Depends, HTTPException, status
from database import engine
import models
from fastapi import File, UploadFile
import secrets
from PIL import Image
from schema.product import ProductIn, ProductUpdate
from schema.user import UserIn, UserRole
from database import session
from services.auth import get_current_user




product_router = APIRouter(
    prefix="/product",
    tags=["Product"],
    responses={404: {"description": "Not found"}},
)


models.Base.metadata.create_all(bind=engine)

@product_router.post("/products")
async def add_new_product(product: ProductIn, user: UserIn = Depends(get_current_user)):
    if user.role != UserRole.BUSINESS_OWNER:
        raise HTTPException(status_code=403, detail="Only business owners can add a new product")

    product_data = product.model_dump()
    if product_data["original_price"] > 0:
        product_data["percentage_discount"] = ((product_data["original_price"] - product_data["new_price"]) / product_data["original_price"]) * 100

        product_obj = models.Product(**product_data)
        
        # Fetch or create the default business
        default_business = session.query(models.Business).filter_by(business_name='Default Business').first()
        if not default_business:
            default_business = models.Business(
                business_name="Default Business",
                city="Unspecified",
                region="Unspecified",
                business_description="Default business entity for products without specified business",
                logo="default_logo.jpg",
            )
            session.add(default_business)
            session.commit()

        # Check if the product includes the business_id
        if "business_id" in product_data and product_data["business_id"]:
            business_id = product_data["business_id"]
            # Fetch the business associated with the provided business_id
            business = session.query(models.Business).filter_by(id=business_id).first()
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

        session.add(product_obj)
        session.commit()

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
async def get_all_products(user: UserIn = Depends(get_current_user)):

    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized, please login")
    products = session.query(models.Product).all()
    return {
        "status": "ok",
        "data": products
    }



@product_router.get("/{id}", status_code=status.HTTP_200_OK)
async def get_specific_product(id: int,
                                user: UserIn = Depends(get_current_user)):
    
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized, please login")
    
    product = session.query(models.Product).filter_by(id=id).first()

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    business = session.query(models.Business).filter_by(id=product.business_id).first()
    if business is None:
        raise HTTPException(status_code=404, detail="Business not found for the product")

    owner = business.owner

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
            "email": owner.email,
            "join_date": owner.join_date.strftime("%b %d %Y %H:%M:%S")
        },
    }






@product_router.post("/product_image/{id}",status_code=status.HTTP_201_CREATED)
async def create_product_image(id: int, file: UploadFile = File(...),
                             user: UserIn = Depends(get_current_user)):
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
        product = session.query(models.Product).filter(models.Product.id == id).first()
        if product:
            business = product.business
            owner = business.owner
            if user == owner:
                product.product_image = token_name
                session.commit() 
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
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update database: " + str(e),
        )
    finally:
        session.close()

    file_url = "localhost:8000" + generated_name[1:]
    return {
        "status": "ok",
        "data": "File uploaded and database updated successfully",
        "file_url": file_url
    }

    

@product_router.put("/{id}", status_code=status.HTTP_200_OK)
async def update_product(id: int, product_update: ProductUpdate, user: UserIn = Depends(get_current_user)):
    if user.role != UserRole.BUSINESS_OWNER:
        raise HTTPException(status_code=403, detail="Only business owners can update a product")
    # Retrieve the product from the database
    product = session.query(models.Product).filter_by(id=id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    # Retrieve the associated business
    business = session.query(models.Business).filter_by(id=product.business_id).first()
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

    session.commit() 
    return {
        "status": "ok", 
        "data": "Product updated successfully",
        "product": product.serialize()
        }



@product_router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_product(id: int, user: UserIn = Depends(get_current_user)):
    if user.role != UserRole.BUSINESS_OWNER:
        raise HTTPException(status_code=403, detail="Only business owners can delete a product")
    product = session.query(models.Product).filter_by(id=id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    business = session.query(models.Business).filter_by(id=product.business_id).first()
    if business is None:
        raise HTTPException(status_code=404, detail="Business not found for the product")

    owner = business.owner
    if user == owner:
        session.delete(product)  
        session.commit() 
        return {"status": "ok", "data": "Product deleted successfully"}
    else:
        raise HTTPException(
            status_code=403, 
            detail="You are not authorized to delete this product"
        )





