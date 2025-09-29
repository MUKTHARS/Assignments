# Models package initialization
from .base_models import BaseModel, BaseResponse, TimeStampedModel, PaginationParams
from .postgres_models import Product, Customer, Order, OrderItem
from .mongodb_models import ProductDocument, CustomerDocument, OrderDocument, OrderItemDocument

__all__ = [
    'BaseModel',
    'BaseResponse',
    'TimeStampedModel', 
    'PaginationParams',
    'Product', 'Customer', 'Order', 'OrderItem',
    'ProductDocument', 'CustomerDocument', 'OrderDocument', 'OrderItemDocument'
]