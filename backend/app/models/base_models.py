from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel as PydanticBaseModel, ConfigDict

class BaseModel(PydanticBaseModel):
    """Base model for all data models"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None

class TimeStampedModel(BaseModel):
    """Base model with created_at and updated_at timestamps"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = 1
    page_size: int = 50
    sort_by: Optional[str] = None
    sort_order: str = "desc"