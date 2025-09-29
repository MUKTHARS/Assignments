from typing import Optional, List
from datetime import datetime, date
from pydantic import Field, BaseModel, ConfigDict
from bson import ObjectId
from .base_models import BaseModel as Base, TimeStampedModel

class PyObjectId(str):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        return {
            'type': 'str',
            'str_format': 'objectid'
        }

class ProductDocument(TimeStampedModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)
    description: Optional[str] = None
    sku: str = Field(..., min_length=1, max_length=100)
    stock_quantity: int = Field(default=0, ge=0)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class CustomerDocument(TimeStampedModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class OrderItemDocument(Base):
    product_id: PyObjectId
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., gt=0)
    subtotal: float = Field(..., gt=0)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class OrderDocument(TimeStampedModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    customer_id: PyObjectId
    order_date: date
    total_amount: float = Field(..., gt=0)
    status: str = Field(default="pending", max_length=50)
    shipping_address: Optional[str] = None
    payment_method: Optional[str] = Field(None, max_length=100)
    payment_status: Optional[str] = Field(default="pending", max_length=50)
    items: List[OrderItemDocument] = Field(default_factory=[])
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )