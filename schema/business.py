from typing import Optional
from pydantic import BaseModel


class BusinessIn(BaseModel):
    business_name: str
    city: str = 'Unspecified'
    region: str = 'Unspecified'
    business_description: Optional[str] = None