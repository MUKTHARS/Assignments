from motor.motor_asyncio import AsyncIOMotorClient
from urllib.parse import urlparse 
import re
import hashlib
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import json
import random

from .base import DatabaseInterface

class MongoDB(DatabaseInterface):
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.client = None
        self.db = None

    async def connect(self):
        try:
            self.client = AsyncIOMotorClient(self.connection_string)
            
            # Dynamically extract database name from connection string
            db_name = self._extract_database_name(self.connection_string)
            
            self.db = self.client[db_name]
            print(f"✅ MongoDB connected successfully to database: {db_name}")
            
            # Verify connection and check collections
            collections = await self.db.list_collection_names()
            print(f"📊 Available collections: {collections}")
            
            # Check if we need to initialize schema
            await self._ensure_schema()
            
        except Exception as e:
            print(f"❌ Error connecting to MongoDB: {e}")
            raise

    def _extract_database_name(self, connection_string: str) -> str:
        """Dynamically extract database name from MongoDB connection string"""
        try:
            # Parse the connection string
            if connection_string.startswith('mongodb+srv://'):
                # MongoDB Atlas connection string
                pattern = r'mongodb\+srv://[^:]+:[^@]+@[^/]+/([^?]+)'
                match = re.search(pattern, connection_string)
                if match:
                    return match.group(1)
            else:
                # Standard MongoDB connection string
                parsed = urlparse(connection_string)
                if parsed.path and parsed.path != '/':
                    db_name = parsed.path[1:]  # Remove leading slash
                    if '?' in db_name:
                        db_name = db_name.split('?')[0]
                    return db_name
            
            # Default fallback - use connection string hash to create unique name
            import hashlib
            hash_obj = hashlib.md5(connection_string.encode())
            return f"shopping_db_{hash_obj.hexdigest()[:8]}"
            
        except Exception as e:
            print(f"⚠️ Could not extract database name, using default: {e}")
            return "shopping_db"

    async def _ensure_schema(self):
        """Ensure basic schema exists, create if needed"""
        existing_collections = await self.db.list_collection_names()
        
        required_collections = ['products', 'customers', 'orders', 'categories', 'reviews', 'inventory']
        
        for collection in required_collections:
            if collection not in existing_collections:
                print(f"📝 Creating collection: {collection}")
                await self.db.create_collection(collection)
        
        print("✅ Schema verification completed")


    async def disconnect(self):
        if self.client:
            self.client.close()

    async def initialize_sample_data(self):
        """Initialize comprehensive sample data for testing"""
        print("🔄 Initializing MongoDB sample data...")

        # Check if data already exists
        products_count = await self.db.products.count_documents({})
        customers_count = await self.db.customers.count_documents({})
        orders_count = await self.db.orders.count_documents({})
        
        if products_count > 0 or customers_count > 0 or orders_count > 0:
            print("ℹ️ Data already exists, skipping sample data initialization")
            return
        
        print("🔄 Initializing MongoDB sample data...")

        # Clear existing data to ensure clean state
        try:
            await self.db.products.drop()
            await self.db.customers.drop()
            await self.db.orders.drop()
            await self.db.categories.drop()
            await self.db.reviews.drop()
            await self.db.inventory.drop()
            print("✅ Cleared existing collections")
        except Exception as e:
            print(f"ℹ️ No existing collections to clear: {e}")

        # Create comprehensive categories
        categories = [
            {
                "_id": str(i),
                "name": name,
                "description": desc,
                "created_at": datetime.utcnow()
            }
            for i, (name, desc) in enumerate([
                ("Electronics", "Latest gadgets and electronic devices"),
                ("Clothing", "Fashionable clothing for all ages"),
                ("Home & Kitchen", "Home appliances and kitchenware"),
                ("Books", "Educational and entertainment books"),
                ("Sports", "Sports equipment and accessories"),
                ("Beauty", "Beauty and personal care products"),
                ("Toys", "Toys and games for all ages"),
                ("Automotive", "Car accessories and automotive parts"),
            ], 1)
        ]
        
        try:
            await self.db.categories.insert_many(categories)
            print(f"✅ Inserted {len(categories)} categories")
        except Exception as e:
            print(f"❌ Error inserting categories: {e}")

        # Create comprehensive products
        products = [
            {
                "_id": str(i),
                "name": name,
                "category": category,
                "subcategory": subcategory,
                "brand": brand,
                "price": price,
                "original_price": original_price,
                "description": description,
                "features": features,
                "specifications": specifications,
                "tags": tags,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            for i, (name, category, subcategory, brand, price, original_price, description, features, specifications, tags) in enumerate([
                ("MacBook Pro 16-inch", "Electronics", "Laptops", "Apple", 2399.99, 2499.99, 
                 "Powerful laptop for professionals", 
                 ["M2 Pro chip", "16-inch Liquid Retina XDR display", "32GB unified memory", "1TB SSD storage"],
                 {"processor": "Apple M2 Pro", "ram": "32GB", "storage": "1TB SSD", "display": "16.2-inch"},
                 ["laptop", "apple", "professional", "premium"]),
                
                ("iPhone 15 Pro", "Electronics", "Smartphones", "Apple", 999.99, 1099.99,
                 "Latest iPhone with advanced camera system",
                 ["A17 Pro chip", "Titanium design", "Pro camera system", "5G capable"],
                 {"storage": "128GB", "color": "Natural Titanium", "camera": "48MP"},
                 ["smartphone", "apple", "premium", "5g"]),
                
                ("Samsung Galaxy S24", "Electronics", "Smartphones", "Samsung", 849.99, 899.99,
                 "Advanced Android smartphone with AI features",
                 ["Snapdragon 8 Gen 3", "Dynamic AMOLED 2X", "200MP camera", "AI-powered features"],
                 {"storage": "256GB", "color": "Phantom Black", "camera": "200MP"},
                 ["android", "samsung", "5g", "camera"]),
                
                ("Sony WH-1000XM5", "Electronics", "Headphones", "Sony", 349.99, 399.99,
                 "Industry-leading noise canceling headphones",
                 ["Noise Canceling", "30-hour battery", "Touch controls", "Voice assistant"],
                 {"battery": "30 hours", "connectivity": "Bluetooth 5.2", "weight": "250g"},
                 ["headphones", "noise-canceling", "wireless", "premium"]),
                
                ("Nike Air Max 270", "Clothing", "Shoes", "Nike", 149.99, 159.99,
                 "Comfortable and stylish sneakers",
                 ["Air Max unit", "Breathable mesh", "Rubber outsole", "Cushioned midsole"],
                 {"sizes": ["US 7", "US 8", "US 9", "US 10", "US 11"], "colors": ["Black", "White", "Red"]},
                 ["shoes", "nike", "sneakers", "athletic"]),
                
                ("Levi's 511 Slim Jeans", "Clothing", "Pants", "Levi's", 79.99, 89.99,
                 "Classic slim fit jeans",
                 ["Slim fit", "Stretch denim", "Five-pocket style", "Machine washable"],
                 {"sizes": ["28x30", "30x30", "32x30", "34x30"], "colors": ["Dark Blue", "Black", "Light Blue"]},
                 ["jeans", "levis", "slim-fit", "denim"]),
                
                ("Instant Pot Pro", "Home & Kitchen", "Kitchen Appliances", "Instant Pot", 129.99, 149.99,
                 "8-in-1 pressure cooker and slow cooker",
                 ["8-in-1 functionality", "Easy-to-use controls", "Stainless steel pot", "Safety features"],
                 {"capacity": "6 quarts", "power": "1000W", "material": "Stainless Steel"},
                 ["kitchen", "cooker", "instant-pot", "appliance"]),
                
                ("Dyson V15 Detect", "Home & Kitchen", "Vacuum Cleaners", "Dyson", 749.99, 799.99,
                 "Powerful cordless vacuum with laser detection",
                 ["Laser dust detection", "High torque cleaner head", "60-minute runtime", "HEPA filtration"],
                 {"battery": "60 min", "bin_capacity": "0.77L", "weight": "3kg"},
                 ["vacuum", "dyson", "cordless", "cleaning"]),
                
                ("The Midnight Library", "Books", "Fiction", "Penguin", 17.99, 19.99,
                 "Bestselling novel by Matt Haig",
                 ["New York Times Bestseller", "Thought-provoking", "Emotional journey"],
                 {"pages": "304", "language": "English", "isbn": "978-0525559474"},
                 ["fiction", "novel", "bestseller", "library"]),
                
                ("Python Crash Course", "Books", "Education", "No Starch Press", 34.99, 39.99,
                 "Hands-on introduction to programming",
                 ["Beginner-friendly", "Practical projects", "Updated for Python 3"],
                 {"pages": "544", "language": "English", "isbn": "978-1593279288"},
                 ["programming", "python", "education", "coding"]),
                
                ("Yoga Mat Premium", "Sports", "Fitness", "Lululemon", 78.99, 89.99,
                 "High-quality non-slip yoga mat",
                 ["Non-slip surface", "5mm thickness", "Eco-friendly materials", "Carry strap"],
                 {"thickness": "5mm", "length": "72 inches", "weight": "2.5kg"},
                 ["yoga", "fitness", "exercise", "mat"]),
                
                ("Vitamin C Serum", "Beauty", "Skincare", "The Ordinary", 12.99, 14.99,
                 "Antioxidant protection for skin",
                 ["Brightens complexion", "Reduces wrinkles", "Lightweight formula", "Vegan"],
                 {"volume": "30ml", "skin_type": "All types", "ingredients": "Vitamin C, Hyaluronic Acid"},
                 ["skincare", "vitamin-c", "beauty", "serum"]),
                
                ("LEGO Star Wars Millennium Falcon", "Toys", "Building Sets", "LEGO", 159.99, 179.99,
                 "Iconic Star Wars spaceship building set",
                 ["1344 pieces", "Includes mini-figures", "Detailed interior", "Collector's item"],
                 {"pieces": "1344", "age_range": "9+", "theme": "Star Wars"},
                 ["lego", "star-wars", "toy", "building"]),
                
                ("Car Phone Mount", "Automotive", "Accessories", "iOttie", 24.99, 29.99,
                 "Easy one-touch smartphone car mount",
                 ["One-touch mechanism", "360-degree rotation", "Strong suction cup", "Universal compatibility"],
                 {"compatibility": "All smartphones", "mount_type": "Dashboard/Windshield"},
                 ["car", "accessory", "phone-mount", "iottoe"]),
                
                ("Wireless Charging Pad", "Electronics", "Accessories", "Anker", 19.99, 24.99,
                 "Fast wireless charging for compatible devices",
                 ["10W fast charging", "LED indicator", "Non-slip surface", "Compact design"],
                 {"power": "10W", "compatibility": "Qi-enabled devices", "cable_length": "1m"},
                 ["charger", "wireless", "anker", "accessory"]),
                
                ("Stainless Steel Water Bottle", "Home & Kitchen", "Drinkware", "Hydro Flask", 34.99, 39.99,
                 "Insulated water bottle keeps drinks cold for 24 hours",
                 ["Temperature retention", "Durable construction", "BPA-free", "Multiple colors"],
                 {"capacity": "32oz", "insulation": "Double-walled", "material": "Stainless Steel"},
                 ["water-bottle", "hydration", "eco-friendly", "insulated"]),
                
                ("Bluetooth Speaker", "Electronics", "Audio", "JBL", 89.99, 99.99,
                 "Portable waterproof Bluetooth speaker",
                 ["IPX7 waterproof", "12-hour battery", "JBL bass radiator", "PartyBoost feature"],
                 {"battery": "12 hours", "waterproof": "IPX7", "connectivity": "Bluetooth 5.1"},
                 ["speaker", "bluetooth", "portable", "audio"]),
                
                ("Gaming Mouse", "Electronics", "Computer Accessories", "Logitech", 49.99, 59.99,
                 "High-precision gaming mouse with RGB lighting",
                 ["25K DPI sensor", "LIGHTSYNC RGB", "8 programmable buttons", "Lightweight design"],
                 {"dpi": "25600", "buttons": "8", "weight": "85g", "connectivity": "USB"},
                 ["gaming", "mouse", "logitech", "rgb"]),
                
                ("Mechanical Keyboard", "Electronics", "Computer Accessories", "Corsair", 129.99, 149.99,
                 "RGB mechanical gaming keyboard",
                 ["Cherry MX switches", "Per-key RGB lighting", "Aircraft-grade aluminum frame", "Dedicated media controls"],
                 {"switches": "Cherry MX Red", "layout": "US QWERTY", "backlight": "RGB"},
                 ["keyboard", "mechanical", "gaming", "corsair"]),
                
                ("Smart Watch", "Electronics", "Wearables", "Samsung", 249.99, 299.99,
                 "Advanced health monitoring smartwatch",
                 ["Health tracking", "GPS", "Sleep monitoring", "Smartphone notifications"],
                 {"display": "1.4-inch", "battery": "2 days", "compatibility": "Android/iOS"},
                 ["smartwatch", "wearable", "fitness", "samsung"])
            ], 1)
        ]
        
        try:
            await self.db.products.insert_many(products)
            print(f"✅ Inserted {len(products)} products")
        except Exception as e:
            print(f"❌ Error inserting products: {e}")

        # Create comprehensive customers
        customers = [
            {
                "_id": str(i),
                "name": name,
                "email": email,
                "phone": phone,
                "address": address,
                "city": city,
                "state": state,
                "zip_code": zip_code,
                "country": country,
                "customer_since": customer_since,
                "loyalty_tier": loyalty_tier,
                "preferences": preferences,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            for i, (name, email, phone, address, city, state, zip_code, country, customer_since, loyalty_tier, preferences) in enumerate([
                ("Johnathan Smith", "john.smith@email.com", "+1-555-0101", "123 Main Street", "New York", "NY", "10001", "USA", 
                 datetime(2022, 1, 15), "Gold", {"categories": ["Electronics", "Books"], "brands": ["Apple", "Sony"]}),
                
                ("Emily Johnson", "emily.johnson@email.com", "+1-555-0102", "456 Oak Avenue", "Los Angeles", "CA", "90210", "USA",
                 datetime(2021, 8, 22), "Platinum", {"categories": ["Clothing", "Beauty"], "brands": ["Nike", "Levi's"]}),
                
                ("Michael Brown", "michael.brown@email.com", "+1-555-0103", "789 Pine Road", "Chicago", "IL", "60601", "USA",
                 datetime(2023, 3, 10), "Silver", {"categories": ["Electronics", "Sports"], "brands": ["Samsung", "JBL"]}),
                
                ("Sarah Davis", "sarah.davis@email.com", "+1-555-0104", "321 Elm Street", "Houston", "TX", "77001", "USA",
                 datetime(2020, 11, 5), "Platinum", {"categories": ["Home & Kitchen", "Beauty"], "brands": ["Dyson", "The Ordinary"]}),
                
                ("David Wilson", "david.wilson@email.com", "+1-555-0105", "654 Maple Drive", "Phoenix", "AZ", "85001", "USA",
                 datetime(2022, 6, 18), "Gold", {"categories": ["Automotive", "Electronics"], "brands": ["Logitech", "Corsair"]}),
                
                ("Jennifer Miller", "jennifer.miller@email.com", "+1-555-0106", "987 Cedar Lane", "Philadelphia", "PA", "19101", "USA",
                 datetime(2021, 2, 28), "Silver", {"categories": ["Toys", "Books"], "brands": ["LEGO", "Penguin"]}),
                
                ("Robert Taylor", "robert.taylor@email.com", "+1-555-0107", "147 Birch Court", "San Antonio", "TX", "78201", "USA",
                 datetime(2023, 1, 8), "Bronze", {"categories": ["Sports", "Electronics"], "brands": ["Hydro Flask", "Anker"]}),
                
                ("Lisa Anderson", "lisa.anderson@email.com", "+1-555-0108", "258 Walnut Street", "San Diego", "CA", "92101", "USA",
                 datetime(2020, 9, 14), "Platinum", {"categories": ["Clothing", "Home & Kitchen"], "brands": ["Lululemon", "Instant Pot"]}),
                
                ("Thomas Martinez", "thomas.martinez@email.com", "+1-555-0109", "369 Spruce Avenue", "Dallas", "TX", "75201", "USA",
                 datetime(2022, 11, 30), "Gold", {"categories": ["Automotive", "Sports"], "brands": ["iOttie", "JBL"]}),
                
                ("Amanda Garcia", "amanda.garcia@email.com", "+1-555-0110", "741 Oakwood Drive", "San Jose", "CA", "95101", "USA",
                 datetime(2021, 7, 12), "Silver", {"categories": ["Beauty", "Books"], "brands": ["The Ordinary", "No Starch Press"]})
            ], 1)
        ]
        
        try:
            await self.db.customers.insert_many(customers)
            print(f"✅ Inserted {len(customers)} customers")
        except Exception as e:
            print(f"❌ Error inserting customers: {e}")

        # Create inventory data
        inventory_items = []
        for product_id in range(1, 21):
            inventory_items.append({
                "_id": str(product_id),
                "product_id": str(product_id),
                "quantity": random.randint(10, 200),
                "low_stock_threshold": 20,
                "warehouse_location": random.choice(["NYC", "LA", "CHI", "DAL", "ATL"]),
                "last_restocked": datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                "created_at": datetime.utcnow()
            })
        
        try:
            await self.db.inventory.insert_many(inventory_items)
            print(f"✅ Inserted {len(inventory_items)} inventory items")
        except Exception as e:
            print(f"❌ Error inserting inventory: {e}")

        # Create product reviews
        reviews = []
        review_id = 1
        for product_id in range(1, 21):
            for customer_id in range(1, 11):
                if random.random() > 0.7:  # 30% chance of review
                    reviews.append({
                        "_id": str(review_id),
                        "product_id": str(product_id),
                        "customer_id": str(customer_id),
                        "rating": random.randint(3, 5),
                        "title": f"Great product #{review_id}",
                        "comment": f"This is my detailed review for product {product_id}. I found it to be excellent quality and would recommend it to others.",
                        "verified_purchase": random.choice([True, False]),
                        "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 180))
                    })
                    review_id += 1
        
        try:
            await self.db.reviews.insert_many(reviews)
            print(f"✅ Inserted {len(reviews)} product reviews")
        except Exception as e:
            print(f"❌ Error inserting reviews: {e}")

        # Create comprehensive orders with embedded items
        orders = []
        base_date = date(2025, 7, 1)
        for i in range(1, 51):  # 50 orders for more data
            days_offset = (i - 1) * 2
            order_date = (base_date + timedelta(days=days_offset)).isoformat()
            customer_id = str((i % 10) + 1)
            status = random.choice(["completed", "completed", "completed", "completed", "pending", "shipped", "delivered"])
            customer_id = str((i % 10) + 1)
            if order_date > "2025-10-31":
                order_date = "2025-10-31"
            # Create order with embedded items
            order = {
                "_id": str(i),
                "customer_id": customer_id,
                "order_date": order_date,
                "total_amount": 0,  # Will calculate
                "status": status,
                "shipping_address": f"{random.randint(100, 999)} {random.choice(['Main', 'Oak', 'Pine', 'Maple'])} St",
                "shipping_city": random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]),
                "shipping_state": random.choice(["NY", "CA", "IL", "TX", "AZ"]),
                "shipping_zip": f"{random.randint(10000, 99999)}",
                "payment_method": random.choice(["credit_card", "paypal", "apple_pay", "google_pay"]),
                "payment_status": "paid" if status in ["completed", "shipped", "delivered"] else "pending",
                "created_at": datetime.utcnow(),
                "items": []
            }
            
            # Add 1-5 items to each order
            num_items = random.randint(1, 5)
            order_total = 0
            
            for j in range(num_items):
                product_id = str(random.randint(1, 20))
                quantity = random.randint(1, 3)
                unit_price = (int(product_id) * 50) + random.randint(10, 99) + 0.99
                item_total = quantity * unit_price
                order_total += item_total
                
                order_item = {
                    "product_id": product_id,
                    "product_name": f"Product {product_id}",
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "item_total": item_total
                }
                order["items"].append(order_item)
            
            order["total_amount"] = round(order_total, 2)
            order["tax_amount"] = round(order_total * 0.08, 2)
            order["shipping_cost"] = 9.99 if order_total < 100 else 0
            order["final_amount"] = order["total_amount"] + order["tax_amount"] + order["shipping_cost"]
            
            orders.append(order)
        
        try:
            await self.db.orders.insert_many(orders)
            print(f"✅ Inserted {len(orders)} orders with embedded items")
            
            # Verify data insertion
            products_count = await self.db.products.count_documents({})
            customers_count = await self.db.customers.count_documents({})
            orders_count = await self.db.orders.count_documents({})
            categories_count = await self.db.categories.count_documents({})
            reviews_count = await self.db.reviews.count_documents({})
            inventory_count = await self.db.inventory.count_documents({})
            
            print(f"📊 Data verification - Products: {products_count}, Customers: {customers_count}, Orders: {orders_count}")
            print(f"📊 Additional data - Categories: {categories_count}, Reviews: {reviews_count}, Inventory: {inventory_count}")
            
        except Exception as e:
            print(f"❌ Error inserting orders: {e}")

        print("✅ MongoDB comprehensive sample data initialization completed")

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
            customers_count = await self.db.customers.count_documents({})
            categories_count = await self.db.categories.count_documents({})
            reviews_count = await self.db.reviews.count_documents({})
            inventory_count = await self.db.inventory.count_documents({})
            
            print(f"📊 Counts - Orders: {orders_count}, Products: {products_count}, Customers: {customers_count}")
            print(f"📊 Additional - Categories: {categories_count}, Reviews: {reviews_count}, Inventory: {inventory_count}")
            
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

    async def execute_dynamic_query(self, table: str, fields: List[str], filters: Dict[str, Any], 
                                  sort_by: str = None, sort_order: str = "desc", limit: int = 50,
                                  query_type: str = "general", operation: str = "get") -> List[Dict[str, Any]]:
        """Execute dynamic queries with enhanced capabilities including search"""
        
        # Handle product search queries
        if table == "products" and filters.get('search_term'):
            return await self.get_products_by_search(filters['search_term'])
        
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

    async def get_all_categories(self) -> List[Dict[str, Any]]:
        """Get all product categories"""
        try:
            cursor = self.db.categories.find().sort("name", 1)
            results = await cursor.to_list(length=None)
            print(f"✅ All categories: {len(results)} categories")
            return results
        except Exception as e:
            print(f"❌ Error in get_all_categories: {e}")
            return []

    async def get_product_reviews(self, product_id: str) -> List[Dict[str, Any]]:
        """Get reviews for a specific product"""
        try:
            pipeline = [
                {
                    "$match": {
                        "product_id": product_id
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
                        "rating": 1,
                        "title": 1,
                        "comment": 1,
                        "verified_purchase": 1,
                        "created_at": 1,
                        "customer_name": {"$arrayElemAt": ["$customer.name", 0]},
                        "_id": 0
                    }
                },
                {
                    "$sort": {"created_at": -1}
                }
            ]
            
            cursor = self.db.reviews.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            print(f"✅ Product {product_id} reviews: {len(results)} reviews")
            return results
        except Exception as e:
            print(f"❌ Error in get_product_reviews: {e}")
            return []

    async def get_products_by_search(self, search_term: str) -> List[Dict[str, Any]]:
        """Get products by search term in name"""
        try:
            # Case-insensitive search for products containing the search term
            query = {"name": {"$regex": search_term, "$options": "i"}}
            cursor = self.db.products.find(query)
            results = await cursor.to_list(length=None)
            print(f"✅ Products search for '{search_term}': {len(results)} results")
            return results
        except Exception as e:
            print(f"❌ Error in get_products_by_search: {e}")
            return []


    async def get_inventory_status(self) -> List[Dict[str, Any]]:
        """Get current inventory status with product details"""
        try:
            pipeline = [
                {
                    "$lookup": {
                        "from": "products",
                        "localField": "product_id",
                        "foreignField": "_id",
                        "as": "product"
                    }
                },
                {
                    "$unwind": "$product"
                },
                {
                    "$project": {
                        "product_id": 1,
                        "product_name": "$product.name",
                        "category": "$product.category",
                        "quantity": 1,
                        "low_stock_threshold": 1,
                        "warehouse_location": 1,
                        "last_restocked": 1,
                        "is_low_stock": {
                            "$lt": ["$quantity", "$low_stock_threshold"]
                        },
                        "_id": 0
                    }
                },
                {
                    "$sort": {"is_low_stock": -1, "quantity": 1}
                }
            ]
            
            cursor = self.db.inventory.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            print(f"✅ Inventory status: {len(results)} items")
            return results
        except Exception as e:
            print(f"❌ Error in get_inventory_status: {e}")
            return []