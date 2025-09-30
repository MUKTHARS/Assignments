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
            # Extract database name from connection string
            if "mongodb://" in self.connection_string:
                parts = self.connection_string.split("/")
                if len(parts) > 3:
                    db_name = parts[-1]
                    if "?" in db_name:
                        db_name = db_name.split("?")[0]
                else:
                    db_name = "shopping_db"
            else:
                db_name = "shopping_db"
            
            self.db = self.client[db_name]
            print(f"✅ MongoDB connected successfully to database: {db_name}")
            
            # Verify connection
            collections = await self.db.list_collection_names()
            print(f"📊 Available collections: {collections}")
            
        except Exception as e:
            print(f"❌ Error connecting to MongoDB: {e}")
            raise

    async def disconnect(self):
        if self.client:
            self.client.close()

    async def initialize_sample_data(self):
        """Initialize sample data for testing"""
        print("🔄 Initializing MongoDB sample data...")
        
        # Clear existing data to ensure clean state
        try:
            await self.db.products.drop()
            await self.db.customers.drop()
            await self.db.orders.drop()
            print("✅ Cleared existing collections")
        except Exception as e:
            print(f"ℹ️ No existing collections to clear: {e}")

        # Create sample products
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
        
        try:
            await self.db.products.insert_many(products)
            print(f"✅ Inserted {len(products)} products")
        except Exception as e:
            print(f"❌ Error inserting products: {e}")

        # Create sample customers
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
        
        try:
            await self.db.customers.insert_many(customers)
            print(f"✅ Inserted {len(customers)} customers")
        except Exception as e:
            print(f"❌ Error inserting customers: {e}")

        # Create sample orders with embedded items
        orders = []
        for i in range(1, 21):
            order_date = (date.today() - timedelta(days=(i-1)*2)).isoformat()
            customer_id = str((i % 3) + 1)
            total_amount = i * 50
            
            # Create order with embedded items
            order = {
                "_id": str(i),
                "customer_id": customer_id,
                "order_date": order_date,
                "total_amount": total_amount,
                "status": "completed",
                "created_at": datetime.utcnow(),
                "items": []  # Initialize empty items array
            }
            
            # Add 1-3 items to each order
            num_items = (i % 3) + 1
            for j in range(1, num_items + 1):
                product_id = str(((i + j - 1) % 7) + 1)
                order_item = {
                    "product_id": product_id,
                    "quantity": j,
                    "unit_price": (int(product_id) * 10) + 9.99
                }
                order["items"].append(order_item)
            
            orders.append(order)
        
        try:
            await self.db.orders.insert_many(orders)
            print(f"✅ Inserted {len(orders)} orders with embedded items")
            
            # Verify data insertion
            products_count = await self.db.products.count_documents({})
            customers_count = await self.db.customers.count_documents({})
            orders_count = await self.db.orders.count_documents({})
            print(f"📊 Data verification - Products: {products_count}, Customers: {customers_count}, Orders: {orders_count}")
            
        except Exception as e:
            print(f"❌ Error inserting orders: {e}")

        print("✅ MongoDB sample data initialization completed")






    async def get_weekly_revenue(self, start_date: date, end_date: date) -> float:
        try:
            pipeline = [
                {
                    "$match": {
                        "order_date": {
                            "$gte": start_date.isoformat(),
                            "$lte": end_date.isoformat()
                        },
                        "status": "completed"
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
        except Exception as e:
            print(f"❌ Error in get_weekly_revenue: {e}")
            return 0.0

    async def get_daily_sales(self, target_date: date) -> List[Dict[str, Any]]:
        try:
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
                    "$addFields": {
                        "item_count": {
                            "$cond": {
                                "if": {"$isArray": "$items"},
                                "then": {"$size": "$items"},
                                "else": 0
                            }
                        }
                    }
                },
                {
                    "$project": {
                        "order_id": "$_id",
                        "customer_name": {"$arrayElemAt": ["$customer.name", 0]},
                        "total_amount": 1,
                        "status": 1,
                        "item_count": 1,
                        "_id": 0
                    }
                }
            ]
            
            cursor = self.db.orders.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            print(f"✅ Daily sales for {target_date}: {len(results)} orders")
            return results
        except Exception as e:
            print(f"❌ Error in get_daily_sales: {e}")
            return []



    async def get_top_products(self, limit: int = 10) -> List[Dict[str, Any]]:
        try:
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
                        "_id": "$product.name",
                        "name": {"$first": "$product.name"},
                        "category": {"$first": "$product.category"},
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
                        "name": 1,
                        "category": 1,
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
            results = await cursor.to_list(length=None)
            print(f"✅ Top products: {len(results)} results")
            return results
        except Exception as e:
            print(f"❌ Error in get_top_products: {e}")
            return []

    async def get_customer_orders(self, customer_id: str) -> List[Dict[str, Any]]:
        try:
            pipeline = [
                {
                    "$match": {
                        "customer_id": customer_id
                    }
                },
                {
                    "$addFields": {
                        "item_count": {
                            "$cond": {
                                "if": {"$isArray": "$items"},
                                "then": {"$size": "$items"},
                                "else": 0
                            }
                        }
                    }
                },
                {
                    "$project": {
                        "order_id": "$_id",
                        "order_date": 1,
                        "total_amount": 1,
                        "status": 1,
                        "item_count": 1,
                        "_id": 0
                    }
                },
                {
                    "$sort": {"order_date": -1}
                }
            ]
            
            cursor = self.db.orders.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            print(f"✅ Customer {customer_id} orders: {len(results)} results")
            return results
        except Exception as e:
            print(f"❌ Error in get_customer_orders: {e}")
            return []

    

    async def get_sales_by_category(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        try:
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
                        "total_revenue": 1,
                        "_id": 0
                    }
                },
                {
                    "$sort": {"total_revenue": -1}
                }
            ]
            
            cursor = self.db.orders.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            print(f"✅ Sales by category: {len(results)} categories")
            return results
        except Exception as e:
            print(f"❌ Error in get_sales_by_category: {e}")
            return []
    async def debug_data_structure(self):
        """Debug method to check data structure"""
        try:
            # Check orders structure
            sample_order = await self.db.orders.find_one()
            print(f"📋 Sample order structure: {list(sample_order.keys()) if sample_order else 'No orders'}")
            if sample_order and 'items' in sample_order:
                print(f"📦 Sample items: {sample_order['items'][:2] if sample_order['items'] else 'No items'}")
            
            # Check products structure
            sample_product = await self.db.products.find_one()
            print(f"📋 Sample product structure: {list(sample_product.keys()) if sample_product else 'No products'}")
            
            # Count documents
            orders_count = await self.db.orders.count_documents({})
            products_count = await self.db.products.count_documents({})
            print(f"📊 Counts - Orders: {orders_count}, Products: {products_count}")
            
        except Exception as e:
            print(f"❌ Debug error: {e}")
    
    
    
    async def get_monthly_revenue_trend(self, months: int = 6) -> List[Dict[str, Any]]:
        try:
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
                    "$addFields": {
                        "order_date_parsed": {
                            "$dateFromString": {
                                "dateString": "$order_date"
                            }
                        }
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "year": {"$year": "$order_date_parsed"},
                            "month": {"$month": "$order_date_parsed"}
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
            results = await cursor.to_list(length=None)
            print(f"✅ Monthly revenue trend: {len(results)} months")
            return results
        except Exception as e:
            print(f"❌ Error in get_monthly_revenue_trend: {e}")
            return []
    
    
    async def get_all_time_revenue(self) -> float:
        try:
            pipeline = [
                {
                    "$match": {
                        "status": "completed"
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
            revenue = result[0]["total_revenue"] if result else 0.0
            print(f"✅ All time revenue: ${revenue:,.2f}")
            return revenue
        except Exception as e:
            print(f"❌ Error in get_all_time_revenue: {e}")
            return 0.0

    async def get_all_customers(self) -> List[Dict[str, Any]]:
        try:
            cursor = self.db.customers.find().sort("_id", 1)
            results = await cursor.to_list(length=None)
            print(f"✅ All customers: {len(results)} customers")
            return results
        except Exception as e:
            print(f"❌ Error in get_all_customers: {e}")
            return []

    async def get_all_products(self) -> List[Dict[str, Any]]:
        try:
            cursor = self.db.products.find().sort("_id", 1)
            results = await cursor.to_list(length=None)
            print(f"✅ All products: {len(results)} products")
            return results
        except Exception as e:
            print(f"❌ Error in get_all_products: {e}")
            return []

    async def get_recent_orders(self, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            pipeline = [
                {
                    "$match": {
                        "status": "completed"
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
            results = await cursor.to_list(length=None)
            print(f"✅ Recent orders: {len(results)} orders")
            return results
        except Exception as e:
            print(f"❌ Error in get_recent_orders: {e}")
            return []

   
    async def execute_custom_query(self, query: str) -> List[Dict[str, Any]]:
        try:
            if query.strip().lower().startswith('db.'):
                collection_name = query.split('.')[1]
                collection = self.db[collection_name]
                cursor = collection.find()
                return await cursor.to_list(length=100)
            else:
                pipeline = json.loads(query)
                collection = self.db.orders
                cursor = collection.aggregate(pipeline)
                return await cursor.to_list(length=100)
        except Exception as e:
            raise Exception(f"Query execution error: {str(e)}")

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

    async def get_monthly_revenue(self, months: int = 1, last_month: bool = False) -> float:
        """Get revenue for a specific month"""
        try:
            today = date.today()
            if last_month:
                # Get previous month
                if today.month == 1:
                    start_date = date(today.year - 1, 12, 1)
                else:
                    start_date = date(today.year, today.month - 1, 1)
                end_date = date(start_date.year, start_date.month, 1) + timedelta(days=32)
                end_date = end_date.replace(day=1) - timedelta(days=1)
            else:
                # Get current month
                start_date = date(today.year, today.month, 1)
                end_date = today
            
            pipeline = [
                {
                    "$match": {
                        "order_date": {
                            "$gte": start_date.isoformat(),
                            "$lte": end_date.isoformat()
                        },
                        "status": "completed"
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "monthly_revenue": {"$sum": "$total_amount"}
                    }
                }
            ]
            
            cursor = self.db.orders.aggregate(pipeline)
            result = await cursor.to_list(length=1)
            revenue = result[0]["monthly_revenue"] if result else 0.0
            month_name = start_date.strftime('%B %Y')
            print(f"✅ Monthly revenue for {month_name}: ${revenue:,.2f}")
            return revenue
        except Exception as e:
            print(f"❌ Error in get_monthly_revenue: {e}")
            return 0.0    