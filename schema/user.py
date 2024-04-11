from enum import Enum
import re
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
from database import SessionLocal



session = SessionLocal()

class UserRole(str, Enum):
    BUSINESS_OWNER = "business_owner"
    CUSTOMER = "customer"
    ADMIN = "admin"


class UserIn(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: UserRole = Field(..., description="Select your role (customer or business_owner)", example="customer")



    class Config:
        schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "securepassword",
                "role": "customer"
            }
        }


    @validator('username')
    def validate_username(cls, username):
        if len(username) < 6:
            raise ValueError('Username must be at least 6 characters long')
        pattern = r'^[a-zA-Z0-9_-]+$'

        if re.fullmatch(pattern, username):
            return username
        else:
            raise ValueError('Invalid username format')
        
    
    @validator('password')
    def validate_password(cls, password):
        has_upper = re.search(r"[A-Z]", password)
        has_lower = re.search(r"[a-z]", password)
        has_digit = re.search(r"\d", password)
        has_special = re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)

        if has_upper and has_lower and has_digit and has_special and len(password) >= 8:
            return password
        else:
            raise ValueError('Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, one digit, and one special character')
        

    
    @classmethod
    def sanitize_fields(cls, input_field):
        return re.sub(r'[^\w\s.!@#$%^&*(),.?":{}|<>]', '', input_field)
    
    @validator('username', pre=True)
    def sanitize_username(cls, username):
        return cls.sanitize_fields(username)
    

    @validator('password', pre=True)
    def sanitize_password(cls, password):
        sanitized_password = cls.sanitize_fields(password)
        return sanitized_password





class UserUpdate(BaseModel):
    username: Optional[str]
    password: Optional[str]


    @validator('username')
    def validate_username(cls, username):
        if len(username) < 6:
            raise ValueError('Username must be at least 6 characters long')
        pattern = r'^[a-zA-Z0-9_-]+$'

        if re.fullmatch(pattern, username):
            return username
        else:
            raise ValueError('Invalid username format')
        
    
    @validator('password')
    def validate_password(cls, password):
        has_upper = re.search(r"[A-Z]", password)
        has_lower = re.search(r"[a-z]", password)
        has_digit = re.search(r"\d", password)
        has_special = re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)

        if has_upper and has_lower and has_digit and has_special and len(password) >= 8:
            return password
        else:
            raise ValueError('Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, one digit, and one special character')
        

    
    @classmethod
    def sanitize_fields(cls, input_field):
        return re.sub(r'[^\w\s.!@#$%^&*(),.?":{}|<>]', '', input_field)
    
    @validator('username', pre=True)
    def sanitize_username(cls, username):
        return cls.sanitize_fields(username)
    

    @validator('password', pre=True)
    def sanitize_password(cls, password):
        sanitized_password = cls.sanitize_fields(password)
        return sanitized_password











