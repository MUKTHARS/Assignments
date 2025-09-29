from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, date

class DatabaseInterface(ABC):
    
    @abstractmethod
    async def connect(self):
        pass
    
    @abstractmethod
    async def disconnect(self):
        pass
    
    @abstractmethod
    async def get_weekly_revenue(self, start_date: date, end_date: date) -> float:
        pass
    
    @abstractmethod
    async def get_daily_sales(self, target_date: date) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def get_top_products(self, limit: int = 10) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def get_customer_orders(self, customer_id: str) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def get_sales_by_category(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def get_monthly_revenue_trend(self, months: int = 6) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def execute_custom_query(self, query: str) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def initialize_sample_data(self):
        pass