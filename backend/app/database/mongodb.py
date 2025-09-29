from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import json

from .base import DatabaseInterface

class MongoDB(DatabaseInterface):
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.client = None
        self.db = None

    async def connect(self):
        try:
            self.client = AsyncIOMotorClient(self.connection_string)
            self.db = self.client.get_database()
            print("MongoDB connected successfully")
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            raise

    async def disconnect(self):
        if self.client:
            self.client.close()

    async def get_weekly_revenue(self, start_date: date, end_date: date) -> float:
        pipeline = [
            {
                "$match": {
                    "order_date": {
                        "$gte": start_date.isoformat(),
                        "$lte": end_date.isoformat()
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_revenue": {"$sum": "$total_amount"}
                }
            }
        ]
        
        cursor = self.db.orders.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        return result[0]["total_revenue"] if result else 0.0

    async def get_daily_sales(self, target_date: date) -> List[Dict[str, Any]]:
        pipeline = [
            {
                "$match": {
                    "order_date": target_date.isoformat()
                }
            },
            {
                "$lookup": {
                    "from": "customers",
                    "localField": "customer_id",
                    "foreignField": "_id",
                    "as": "customer"
                }
            },
            {
                "$lookup": {
                    "from": "order_items",
                    "localField": "_id",
                    "foreignField": "order_id",
                    "as": "items"
                }
            },
            {
                "$project": {
                    "order_id": "$_id",
                    "customer_name": {"$arrayElemAt": ["$customer.name", 0]},
                    "total_amount": 1,
                    "status": 1,
                    "item_count": {"$size": "$items"}
                }
            }
        ]
        
        cursor = self.db.orders.aggregate(pipeline)
        return await cursor.to_list(length=None)

    async def get_top_products(self, limit: int = 10) -> List[Dict[str, Any]]:
        pipeline = [
            {
                "$unwind": "$items"
            },
            {
                "$lookup": {
                    "from": "products",
                    "localField": "items.product_id",
                    "foreignField": "_id",
                    "as": "product"
                }
            },
            {
                "$unwind": "$product"
            },
            {
                "$group": {
                    "_id": {
                        "product_id": "$items.product_id",
                        "name": "$product.name",
                        "category": "$product.category"
                    },
                    "total_sold": {"$sum": "$items.quantity"},
                    "total_revenue": {
                        "$sum": {
                            "$multiply": ["$items.quantity", "$items.unit_price"]
                        }
                    }
                }
            },
            {
                "$project": {
                    "name": "$_id.name",
                    "category": "$_id.category",
                    "total_sold": 1,
                    "total_revenue": 1,
                    "_id": 0
                }
            },
            {
                "$sort": {"total_revenue": -1}
            },
            {
                "$limit": limit
            }
        ]
        
        cursor = self.db.orders.aggregate(pipeline)
        return await cursor.to_list(length=None)

    async def get_customer_orders(self, customer_id: str) -> List[Dict[str, Any]]:
        pipeline = [
            {
                "$match": {"customer_id": customer_id}
            },
            {
                "$lookup": {
                    "from": "order_items",
                    "localField": "_id",
                    "foreignField": "order_id",
                    "as": "items"
                }
            },
            {
                "$project": {
                    "order_id": "$_id",
                    "order_date": 1,
                    "total_amount": 1,
                    "status": 1,
                    "item_count": {"$size": "$items"}
                }
            },
            {
                "$sort": {"order_date": -1}
            }
        ]
        
        cursor = self.db.orders.aggregate(pipeline)
        return await cursor.to_list(length=None)

    async def get_sales_by_category(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        pipeline = [
            {
                "$match": {
                    "order_date": {
                        "$gte": start_date.isoformat(),
                        "$lte": end_date.isoformat()
                    }
                }
            },
            {
                "$unwind": "$items"
            },
            {
                "$lookup": {
                    "from": "products",
                    "localField": "items.product_id",
                    "foreignField": "_id",
                    "as": "product"
                }
            },
            {
                "$unwind": "$product"
            },
            {
                "$group": {
                    "_id": "$product.category",
                    "order_count": {"$addToSet": "$_id"},
                    "total_quantity": {"$sum": "$items.quantity"},
                    "total_revenue": {
                        "$sum": {
                            "$multiply": ["$items.quantity", "$items.unit_price"]
                        }
                    }
                }
            },
            {
                "$project": {
                    "category": "$_id",
                    "order_count": {"$size": "$order_count"},
                    "total_quantity": 1,
                    "total_revenue": 1
                }
            },
            {
                "$sort": {"total_revenue": -1}
            }
        ]
        
        cursor = self.db.orders.aggregate(pipeline)
        return await cursor.to_list(length=None)

    async def get_monthly_revenue_trend(self, months: int = 6) -> List[Dict[str, Any]]:
        end_date = date.today()
        start_date = end_date - timedelta(days=30*months)
        
        pipeline = [
            {
                "$match": {
                    "order_date": {
                        "$gte": start_date.isoformat(),
                        "$lte": end_date.isoformat()
                    }
                }
            },
            {
                "$group": {
                    "_id": {
                        "year": {"$year": {"$dateFromString": {"dateString": "$order_date"}}},
                        "month": {"$month": {"$dateFromString": {"dateString": "$order_date"}}}
                    },
                    "monthly_revenue": {"$sum": "$total_amount"},
                    "order_count": {"$sum": 1}
                }
            },
            {
                "$project": {
                    "month": {
                        "$dateFromParts": {
                            "year": "$_id.year",
                            "month": "$_id.month",
                            "day": 1
                        }
                    },
                    "monthly_revenue": 1,
                    "order_count": 1,
                    "_id": 0
                }
            },
            {
                "$sort": {"month": 1}
            }
        ]
        
        cursor = self.db.orders.aggregate(pipeline)
        return await cursor.to_list(length=None)

    async def execute_custom_query(self, query: str) -> List[Dict[str, Any]]:
        try:
            # For MongoDB, we'll parse simple queries or use aggregation pipeline
            if query.strip().lower().startswith('db.'):
                # This is a simple MongoDB query format
                collection_name = query.split('.')[1]
                collection = self.db[collection_name]
                cursor = collection.find()
                return await cursor.to_list(length=100)
            else:
                # Try to parse as aggregation pipeline
                pipeline = json.loads(query)
                collection = self.db.orders  # Default collection
                cursor = collection.aggregate(pipeline)
                return await cursor.to_list(length=100)
        except Exception as e:
            raise Exception(f"Query execution error: {str(e)}")

    async def get_all_customers(self) -> List[Dict[str, Any]]:
        cursor = self.db.customers.find().sort("_id", 1)
        return await cursor.to_list(length=None)

    async def get_all_products(self) -> List[Dict[str, Any]]:
        cursor = self.db.products.find().sort("_id", 1)
        return await cursor.to_list(length=None)

    async def get_recent_orders(self, limit: int = 10) -> List[Dict[str, Any]]:
        pipeline = [
            {
                "$lookup": {
                    "from": "customers",
                    "localField": "customer_id",
                    "foreignField": "_id",
                    "as": "customer"
                }
            },
            {
                "$project": {
                    "id": "$_id",
                    "customer_id": 1,
                    "customer_name": {"$arrayElemAt": ["$customer.name", 0]},
                    "order_date": 1,
                    "total_amount": 1,
                    "status": 1,
                    "_id": 0
                }
            },
            {
                "$sort": {"order_date": -1}
            },
            {
                "$limit": limit
            }
        ]
        cursor = self.db.orders.aggregate(pipeline)
        return await cursor.to_list(length=None)

    async def initialize_sample_data(self):
        """Initialize sample data for testing"""
        # Check if data already exists
        products_count = await self.db.products.count_documents({})
        
        if products_count > 0:
            return  # Data already exists
        
        # Insert sample products
        products = [
            {
                "_id": str(i),
                "name": name,
                "category": category,
                "price": price,
                "created_at": datetime.utcnow()
            }
            for i, (name, category, price) in enumerate([
                ("Laptop", "Electronics", 999.99),
                ("Smartphone", "Electronics", 699.99),
                ("Headphones", "Electronics", 149.99),
                ("T-Shirt", "Clothing", 29.99),
                ("Jeans", "Clothing", 59.99),
                ("Book", "Education", 19.99),
                ("Coffee Mug", "Home", 12.99),
            ], 1)
        ]
        
        await self.db.products.insert_many(products)
        
        # Insert sample customers
        customers = [
            {
                "_id": str(i),
                "name": name,
                "email": email,
                "created_at": datetime.utcnow()
            }
            for i, (name, email) in enumerate([
                ("John Doe", "john@example.com"),
                ("Jane Smith", "jane@example.com"),
                ("Bob Johnson", "bob@example.com"),
            ], 1)
        ]
        
        await self.db.customers.insert_many(customers)
        
        # Insert sample orders and order items
        orders = []
        order_items = []
        
        for i in range(1, 21):
            order_date = (date.today() - timedelta(days=(i-1)*2)).isoformat()
            customer_id = str((i % 3) + 1)
            total_amount = i * 50
            
            order = {
                "_id": str(i),
                "customer_id": customer_id,
                "order_date": order_date,
                "total_amount": total_amount,
                "status": "completed",
                "created_at": datetime.utcnow()
            }
            orders.append(order)
            
            # Add order items
            for j in range(1, 4):
                product_id = str(((i + j - 1) % 7) + 1)
                order_item = {
                    "order_id": str(i),
                    "product_id": product_id,
                    "quantity": j,
                    "unit_price": (int(product_id) * 10) + 9.99,
                    "created_at": datetime.utcnow()
                }
                order_items.append(order_item)
        
        await self.db.orders.insert_many(orders)
        await self.db.order_items.insert_many(order_items)

    async def execute_dynamic_query(self, table: str, fields: List[str], filters: Dict[str, Any], 
                                  sort_by: str = None, sort_order: str = "desc", limit: int = 50,
                                  query_type: str = "general", operation: str = "get") -> List[Dict[str, Any]]:
        """Execute dynamic queries based on table and fields with enhanced capabilities"""
        
        collection = self.db[table]
        
        # Handle product price queries dynamically
        if table == "products" and any(keyword in str(filters) for keyword in ['costliest', 'cheapest', 'price_range']):
            return await self._handle_product_price_queries_mongo(filters)
        
        # Build projection
        projection = {"_id": 0}
        if fields != ["*"]:
            for field in fields:
                projection[field] = 1
        
        # Build query filters
        query_filter = {}
        for key, value in filters.items():
            query_filter[key] = value
        
        cursor = collection.find(query_filter, projection)
        return await cursor.to_list(length=100)

    async def _handle_product_price_queries_mongo(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle product price queries for MongoDB"""
        
        operation = filters.get('operation', '')
        
        if 'costliest' in operation or 'most_expensive' in operation:
            pipeline = [
                {"$sort": {"price": -1}},
                {"$limit": 1},
                {"$project": {"name": 1, "category": 1, "price": 1, "_id": 0}}
            ]
        elif 'cheapest' in operation or 'least_expensive' in operation:
            pipeline = [
                {"$sort": {"price": 1}},
                {"$limit": 1},
                {"$project": {"name": 1, "category": 1, "price": 1, "_id": 0}}
            ]
        elif 'price_range' in operation:
            pipeline = [
                {"$group": {
                    "_id": None,
                    "min_price": {"$min": "$price"},
                    "max_price": {"$max": "$price"},
                    "avg_price": {"$avg": "$price"},
                    "product_count": {"$sum": 1}
                }},
                {"$project": {"_id": 0, "min_price": 1, "max_price": 1, "avg_price": 1, "product_count": 1}}
            ]
        elif 'average_price' in operation:
            pipeline = [
                {"$group": {
                    "_id": None,
                    "avg_price": {"$avg": "$price"}
                }},
                {"$project": {"_id": 0, "avg_price": 1}}
            ]
        else:
            # Fallback to get all products sorted by price
            pipeline = [
                {"$sort": {"price": -1}},
                {"$limit": 10},
                {"$project": {"name": 1, "category": 1, "price": 1, "_id": 0}}
            ]
        
        cursor = self.db.products.aggregate(pipeline)
        return await cursor.to_list(length=10)

    async def get_least_sold_products(self, limit: int = 5) -> List[Dict[str, Any]]:
        pipeline = [
            {
                "$unwind": "$items"
            },
            {
                "$lookup": {
                    "from": "products",
                    "localField": "items.product_id",
                    "foreignField": "_id",
                    "as": "product"
                }
            },
            {
                "$unwind": "$product"
            },
            {
                "$group": {
                    "_id": {
                        "product_id": "$items.product_id",
                        "name": "$product.name",
                        "category": "$product.category"
                    },
                    "total_sold": {"$sum": "$items.quantity"},
                    "total_revenue": {
                        "$sum": {
                            "$multiply": ["$items.quantity", "$items.unit_price"]
                        }
                    }
                }
            },
            {
                "$project": {
                    "name": "$_id.name",
                    "category": "$_id.category",
                    "total_sold": 1,
                    "total_revenue": 1,
                    "_id": 0
                }
            },
            {
                "$sort": {"total_sold": 1, "total_revenue": 1}
            },
            {
                "$limit": limit
            }
        ]
        
        cursor = self.db.orders.aggregate(pipeline)
        return await cursor.to_list(length=None)

    async def get_repeat_customers(self) -> List[Dict[str, Any]]:
        pipeline = [
            {
                "$group": {
                    "_id": "$customer_id",
                    "order_count": {"$sum": 1},
                    "total_spent": {"$sum": "$total_amount"}
                }
            },
            {
                "$match": {
                    "order_count": {"$gt": 1}
                }
            },
            {
                "$lookup": {
                    "from": "customers",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "customer"
                }
            },
            {
                "$unwind": "$customer"
            },
            {
                "$project": {
                    "id": "$_id",
                    "name": "$customer.name",
                    "email": "$customer.email",
                    "order_count": 1,
                    "total_spent": 1,
                    "_id": 0
                }
            },
            {
                "$sort": {"order_count": -1, "total_spent": -1}
            }
        ]
        
        cursor = self.db.orders.aggregate(pipeline)
        return await cursor.to_list(length=None)

    async def get_all_time_revenue(self) -> float:
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_revenue": {"$sum": "$total_amount"}
                }
            }
        ]
        
        cursor = self.db.orders.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        return result[0]["total_revenue"] if result else 0.0

    async def get_inactive_customers(self, days_threshold: int = 30) -> List[Dict[str, Any]]:
        cutoff_date = (datetime.utcnow() - timedelta(days=days_threshold)).date().isoformat()
        
        pipeline = [
            {
                "$group": {
                    "_id": "$customer_id",
                    "last_order_date": {"$max": "$order_date"}
                }
            },
            {
                "$match": {
                    "$or": [
                        {"last_order_date": {"$lt": cutoff_date}},
                        {"last_order_date": None}
                    ]
                }
            },
            {
                "$lookup": {
                    "from": "customers",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "customer"
                }
            },
            {
                "$unwind": "$customer"
            },
            {
                "$project": {
                    "id": "$_id",
                    "name": "$customer.name",
                    "email": "$customer.email",
                    "last_order_date": 1,
                    "days_since_last_order": {
                        "$divide": [
                            {"$subtract": [datetime.utcnow(), {"$dateFromString": {"dateString": "$last_order_date"}}]},
                            1000 * 60 * 60 * 24  # Convert milliseconds to days
                        ]
                    },
                    "_id": 0
                }
            },
            {
                "$sort": {"days_since_last_order": -1}
            }
        ]
        
        cursor = self.db.orders.aggregate(pipeline)
        return await cursor.to_list(length=None)

    async def get_peak_revenue_month(self, year: int = None) -> Dict[str, Any]:
        if year is None:
            year = datetime.utcnow().year
            
        pipeline = [
            {
                "$match": {
                    "$expr": {
                        "$eq": [{"$year": {"$dateFromString": {"dateString": "$order_date"}}}, year]
                    }
                }
            },
            {
                "$group": {
                    "_id": {
                        "year": {"$year": {"$dateFromString": {"dateString": "$order_date"}}},
                        "month": {"$month": {"$dateFromString": {"dateString": "$order_date"}}}
                    },
                    "monthly_revenue": {"$sum": "$total_amount"},
                    "order_count": {"$sum": 1}
                }
            },
            {
                "$sort": {"monthly_revenue": -1}
            },
            {
                "$limit": 1
            },
            {
                "$project": {
                    "month": {
                        "$dateFromParts": {
                            "year": "$_id.year",
                            "month": "$_id.month",
                            "day": 1
                        }
                    },
                    "monthly_revenue": 1,
                    "order_count": 1,
                    "_id": 0
                }
            }
        ]
        
        cursor = self.db.orders.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        return result[0] if result else {}

    async def get_customer_product_preferences(self) -> List[Dict[str, Any]]:
        pipeline = [
            {
                "$unwind": "$items"
            },
            {
                "$lookup": {
                    "from": "customers",
                    "localField": "customer_id",
                    "foreignField": "_id",
                    "as": "customer"
                }
            },
            {
                "$lookup": {
                    "from": "products",
                    "localField": "items.product_id",
                    "foreignField": "_id",
                    "as": "product"
                }
            },
            {
                "$unwind": "$customer"
            },
            {
                "$unwind": "$product"
            },
            {
                "$group": {
                    "_id": {
                        "customer_id": "$customer_id",
                        "customer_name": "$customer.name",
                        "product_id": "$items.product_id",
                        "product_name": "$product.name",
                        "category": "$product.category"
                    },
                    "total_quantity": {"$sum": "$items.quantity"},
                    "times_ordered": {"$addToSet": "$_id"}
                }
            },
            {
                "$project": {
                    "customer_id": "$_id.customer_id",
                    "customer_name": "$_id.customer_name",
                    "product_id": "$_id.product_id",
                    "product_name": "$_id.product_name",
                    "category": "$_id.category",
                    "total_quantity": 1,
                    "times_ordered": {"$size": "$times_ordered"},
                    "_id": 0
                }
            },
            {
                "$sort": {"customer_name": 1, "total_quantity": -1}
            }
        ]
        
        cursor = self.db.orders.aggregate(pipeline)
        return await cursor.to_list(length=None)

    async def get_costliest_product(self) -> List[Dict[str, Any]]:
        return await self._handle_product_price_queries_mongo({"operation": "costliest"})

    async def get_cheapest_product(self) -> List[Dict[str, Any]]:
        return await self._handle_product_price_queries_mongo({"operation": "cheapest"})

    async def get_product_price_range(self) -> Dict[str, Any]:
        result = await self._handle_product_price_queries_mongo({"operation": "price_range"})
        return result[0] if result else {}

    async def get_average_product_price(self) -> float:
        result = await self._handle_product_price_queries_mongo({"operation": "average_price"})
        return result[0]["avg_price"] if result and "avg_price" in result[0] else 0.0