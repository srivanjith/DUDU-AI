from pydantic import BaseModel, Field
from typing import Optional

class ProductSchema(BaseModel):
    name: str = Field(..., max_length=120)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    sku: str = Field(..., regex=r'^[A-Z0-9_-]{4,16}$')
    stock: int = Field(default=0, ge=0)
