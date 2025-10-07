from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import date

class DatabaseInterface(ABC):
    """Abstract base class for database implementations"""
    
    @abstractmethod
    async def connect(self):
        """Connect to the database"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Disconnect from the database"""
        pass
    
    @abstractmethod
    async def initialize_sample_data(self):
        """Initialize sample data only if needed"""
        pass
    
    @abstractmethod
    async def _ensure_schema(self):
        """Ensure database schema exists"""
        pass
    
    # Analytics methods
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
    async def get_all_time_revenue(self) -> float:
        pass
    
    @abstractmethod
    async def get_all_customers(self) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def get_all_products(self) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def get_recent_orders(self, limit: int = 10) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def execute_custom_query(self, query: str) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def execute_dynamic_query(self, table: str, fields: List[str], filters: Dict[str, Any], 
                                  sort_by: str = None, sort_order: str = "desc", limit: int = 50,
                                  query_type: str = "general", operation: str = "get") -> List[Dict[str, Any]]:
        pass
    
    # Additional analytics methods
    @abstractmethod
    async def get_least_sold_products(self, limit: int = 5) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def get_repeat_customers(self) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def get_inactive_customers(self, days_threshold: int = 30) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def get_peak_revenue_month(self, year: int = None) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def get_customer_product_preferences(self) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def get_costliest_product(self) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def get_cheapest_product(self) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def get_product_price_range(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def get_average_product_price(self) -> float:
        pass
    
    @abstractmethod
    async def get_monthly_revenue(self, months: int = 1, last_month: bool = False) -> float:
        pass
    
    @abstractmethod
    async def get_all_categories(self) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def get_product_reviews(self, product_id: str) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def get_products_by_search(self, search_term: str) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def get_inventory_status(self) -> List[Dict[str, Any]]:
        pass

        