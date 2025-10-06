import asyncpg
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, Float, DateTime, Date, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
import json
import random

from .base import DatabaseInterface

class PostgresDB(DatabaseInterface):
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.engine = None
        self.SessionLocal = None
        self.metadata = MetaData()
        
        # Define comprehensive tables
        self.categories = Table(
            'categories', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String),
            Column('description', String),
            Column('created_at', DateTime, default=datetime.utcnow)
        )
        
        self.products = Table(
            'products', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String),
            Column('category', String),
            Column('subcategory', String),
            Column('brand', String),
            Column('price', Float),
            Column('original_price', Float),
            Column('description', String),
            Column('features', JSON),
            Column('specifications', JSON),
            Column('tags', JSON),
            Column('created_at', DateTime, default=datetime.utcnow),
            Column('updated_at', DateTime, default=datetime.utcnow)
        )
        
        self.customers = Table(
            'customers', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String),
            Column('email', String),
            Column('phone', String),
            Column('address', String),
            Column('city', String),
            Column('state', String),
            Column('zip_code', String),
            Column('country', String),
            Column('customer_since', DateTime),
            Column('loyalty_tier', String),
            Column('preferences', JSON),
            Column('created_at', DateTime, default=datetime.utcnow),
            Column('updated_at', DateTime, default=datetime.utcnow)
        )
        
        self.orders = Table(
            'orders', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('customer_id', Integer),
            Column('order_date', Date),
            Column('total_amount', Float),
            Column('tax_amount', Float),
            Column('shipping_cost', Float),
            Column('final_amount', Float),
            Column('status', String),
            Column('shipping_address', String),
            Column('shipping_city', String),
            Column('shipping_state', String),
            Column('shipping_zip', String),
            Column('payment_method', String),
            Column('payment_status', String),
            Column('created_at', DateTime, default=datetime.utcnow)
        )
        
        self.order_items = Table(
            'order_items', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('order_id', Integer),
            Column('product_id', Integer),
            Column('product_name', String),
            Column('quantity', Integer),
            Column('unit_price', Float),
            Column('item_total', Float),
            Column('created_at', DateTime, default=datetime.utcnow)
        )
        
        self.inventory = Table(
            'inventory', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('product_id', Integer),
            Column('quantity', Integer),
            Column('low_stock_threshold', Integer),
            Column('warehouse_location', String),
            Column('last_restocked', DateTime),
            Column('created_at', DateTime, default=datetime.utcnow)
        )
        
        self.reviews = Table(
            'reviews', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('product_id', Integer),
            Column('customer_id', Integer),
            Column('rating', Integer),
            Column('title', String),
            Column('comment', String),
            Column('verified_purchase', Boolean),
            Column('created_at', DateTime, default=datetime.utcnow)
        )

    async def connect(self):
        try:
            self.engine = create_engine(self.connection_string)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            self.metadata.create_all(bind=self.engine)
            print("✅ PostgreSQL connected successfully")
        except Exception as e:
            print(f"❌ Error connecting to PostgreSQL: {e}")
            raise

    async def disconnect(self):
        if self.engine:
            self.engine.dispose()

    async def create_tables(self):
        """Create all tables if they don't exist"""
        try:
            self.metadata.create_all(bind=self.engine)
            print("✅ PostgreSQL tables created successfully")
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            raise

    async def initialize_sample_data(self):
        """Initialize comprehensive sample data for testing"""
        with self.engine.begin() as conn:
            # Check if data already exists
            result = conn.execute(text("SELECT COUNT(*) FROM products"))
            count = result.scalar()
            
            if count > 0:
                print("ℹ️ Data already exists, skipping initialization")
                return  # Data already exists
            
            print("🔄 Initializing comprehensive PostgreSQL sample data...")
            
            # Insert categories
            categories_data = [
                {"name": "Electronics", "description": "Latest gadgets and electronic devices"},
                {"name": "Clothing", "description": "Fashionable clothing for all ages"},
                {"name": "Home & Kitchen", "description": "Home appliances and kitchenware"},
                {"name": "Books", "description": "Educational and entertainment books"},
                {"name": "Sports", "description": "Sports equipment and accessories"},
                {"name": "Beauty", "description": "Beauty and personal care products"},
                {"name": "Toys", "description": "Toys and games for all ages"},
                {"name": "Automotive", "description": "Car accessories and automotive parts"},
            ]
            
            for category in categories_data:
                conn.execute(
                    text("INSERT INTO categories (name, description) VALUES (:name, :description)"),
                    category
                )
            
            # Insert comprehensive products
            products_data = [
                ("MacBook Pro 16-inch", "Electronics", "Laptops", "Apple", 2399.99, 2499.99, 
                 "Powerful laptop for professionals", 
                 '["M2 Pro chip", "16-inch Liquid Retina XDR display", "32GB unified memory", "1TB SSD storage"]',
                 '{"processor": "Apple M2 Pro", "ram": "32GB", "storage": "1TB SSD", "display": "16.2-inch"}',
                 '["laptop", "apple", "professional", "premium"]'),
                
                ("iPhone 15 Pro", "Electronics", "Smartphones", "Apple", 999.99, 1099.99,
                 "Latest iPhone with advanced camera system",
                 '["A17 Pro chip", "Titanium design", "Pro camera system", "5G capable"]',
                 '{"storage": "128GB", "color": "Natural Titanium", "camera": "48MP"}',
                 '["smartphone", "apple", "premium", "5g"]'),
                
                ("Samsung Galaxy S24", "Electronics", "Smartphones", "Samsung", 849.99, 899.99,
                 "Advanced Android smartphone with AI features",
                 '["Snapdragon 8 Gen 3", "Dynamic AMOLED 2X", "200MP camera", "AI-powered features"]',
                 '{"storage": "256GB", "color": "Phantom Black", "camera": "200MP"}',
                 '["android", "samsung", "5g", "camera"]'),
                
                ("Sony WH-1000XM5", "Electronics", "Headphones", "Sony", 349.99, 399.99,
                 "Industry-leading noise canceling headphones",
                 '["Noise Canceling", "30-hour battery", "Touch controls", "Voice assistant"]',
                 '{"battery": "30 hours", "connectivity": "Bluetooth 5.2", "weight": "250g"}',
                 '["headphones", "noise-canceling", "wireless", "premium"]'),
                
                ("Nike Air Max 270", "Clothing", "Shoes", "Nike", 149.99, 159.99,
                 "Comfortable and stylish sneakers",
                 '["Air Max unit", "Breathable mesh", "Rubber outsole", "Cushioned midsole"]',
                 '{"sizes": ["US 7", "US 8", "US 9", "US 10", "US 11"], "colors": ["Black", "White", "Red"]}',
                 '["shoes", "nike", "sneakers", "athletic"]'),
                
                ("Levi's 511 Slim Jeans", "Clothing", "Pants", "Levi's", 79.99, 89.99,
                 "Classic slim fit jeans",
                 '["Slim fit", "Stretch denim", "Five-pocket style", "Machine washable"]',
                 '{"sizes": ["28x30", "30x30", "32x30", "34x30"], "colors": ["Dark Blue", "Black", "Light Blue"]}',
                 '["jeans", "levis", "slim-fit", "denim"]'),
                
                ("Instant Pot Pro", "Home & Kitchen", "Kitchen Appliances", "Instant Pot", 129.99, 149.99,
                 "8-in-1 pressure cooker and slow cooker",
                 '["8-in-1 functionality", "Easy-to-use controls", "Stainless steel pot", "Safety features"]',
                 '{"capacity": "6 quarts", "power": "1000W", "material": "Stainless Steel"}',
                 '["kitchen", "cooker", "instant-pot", "appliance"]'),
                
                ("Dyson V15 Detect", "Home & Kitchen", "Vacuum Cleaners", "Dyson", 749.99, 799.99,
                 "Powerful cordless vacuum with laser detection",
                 '["Laser dust detection", "High torque cleaner head", "60-minute runtime", "HEPA filtration"]',
                 '{"battery": "60 min", "bin_capacity": "0.77L", "weight": "3kg"}',
                 '["vacuum", "dyson", "cordless", "cleaning"]'),
                
                ("The Midnight Library", "Books", "Fiction", "Penguin", 17.99, 19.99,
                 "Bestselling novel by Matt Haig",
                 '["New York Times Bestseller", "Thought-provoking", "Emotional journey"]',
                 '{"pages": "304", "language": "English", "isbn": "978-0525559474"}',
                 '["fiction", "novel", "bestseller", "library"]'),
                
                ("Python Crash Course", "Books", "Education", "No Starch Press", 34.99, 39.99,
                 "Hands-on introduction to programming",
                 '["Beginner-friendly", "Practical projects", "Updated for Python 3"]',
                 '{"pages": "544", "language": "English", "isbn": "978-1593279288"}',
                 '["programming", "python", "education", "coding"]'),
                
                ("Yoga Mat Premium", "Sports", "Fitness", "Lululemon", 78.99, 89.99,
                 "High-quality non-slip yoga mat",
                 '["Non-slip surface", "5mm thickness", "Eco-friendly materials", "Carry strap"]',
                 '{"thickness": "5mm", "length": "72 inches", "weight": "2.5kg"}',
                 '["yoga", "fitness", "exercise", "mat"]'),
                
                ("Vitamin C Serum", "Beauty", "Skincare", "The Ordinary", 12.99, 14.99,
                 "Antioxidant protection for skin",
                 '["Brightens complexion", "Reduces wrinkles", "Lightweight formula", "Vegan"]',
                 '{"volume": "30ml", "skin_type": "All types", "ingredients": "Vitamin C, Hyaluronic Acid"}',
                 '["skincare", "vitamin-c", "beauty", "serum"]'),
                
                ("LEGO Star Wars Millennium Falcon", "Toys", "Building Sets", "LEGO", 159.99, 179.99,
                 "Iconic Star Wars spaceship building set",
                 '["1344 pieces", "Includes mini-figures", "Detailed interior", "Collector\'s item"]',
                 '{"pieces": "1344", "age_range": "9+", "theme": "Star Wars"}',
                 '["lego", "star-wars", "toy", "building"]'),
                
                ("Car Phone Mount", "Automotive", "Accessories", "iOttie", 24.99, 29.99,
                 "Easy one-touch smartphone car mount",
                 '["One-touch mechanism", "360-degree rotation", "Strong suction cup", "Universal compatibility"]',
                 '{"compatibility": "All smartphones", "mount_type": "Dashboard/Windshield"}',
                 '["car", "accessory", "phone-mount", "iottoe"]'),
                
                ("Wireless Charging Pad", "Electronics", "Accessories", "Anker", 19.99, 24.99,
                 "Fast wireless charging for compatible devices",
                 '["10W fast charging", "LED indicator", "Non-slip surface", "Compact design"]',
                 '{"power": "10W", "compatibility": "Qi-enabled devices", "cable_length": "1m"}',
                 '["charger", "wireless", "anker", "accessory"]'),
                
                ("Stainless Steel Water Bottle", "Home & Kitchen", "Drinkware", "Hydro Flask", 34.99, 39.99,
                 "Insulated water bottle keeps drinks cold for 24 hours",
                 '["Temperature retention", "Durable construction", "BPA-free", "Multiple colors"]',
                 '{"capacity": "32oz", "insulation": "Double-walled", "material": "Stainless Steel"}',
                 '["water-bottle", "hydration", "eco-friendly", "insulated"]'),
                
                ("Bluetooth Speaker", "Electronics", "Audio", "JBL", 89.99, 99.99,
                 "Portable waterproof Bluetooth speaker",
                 '["IPX7 waterproof", "12-hour battery", "JBL bass radiator", "PartyBoost feature"]',
                 '{"battery": "12 hours", "waterproof": "IPX7", "connectivity": "Bluetooth 5.1"}',
                 '["speaker", "bluetooth", "portable", "audio"]'),
                
                ("Gaming Mouse", "Electronics", "Computer Accessories", "Logitech", 49.99, 59.99,
                 "High-precision gaming mouse with RGB lighting",
                 '["25K DPI sensor", "LIGHTSYNC RGB", "8 programmable buttons", "Lightweight design"]',
                 '{"dpi": "25600", "buttons": "8", "weight": "85g", "connectivity": "USB"}',
                 '["gaming", "mouse", "logitech", "rgb"]'),
                
                ("Mechanical Keyboard", "Electronics", "Computer Accessories", "Corsair", 129.99, 149.99,
                 "RGB mechanical gaming keyboard",
                 '["Cherry MX switches", "Per-key RGB lighting", "Aircraft-grade aluminum frame", "Dedicated media controls"]',
                 '{"switches": "Cherry MX Red", "layout": "US QWERTY", "backlight": "RGB"}',
                 '["keyboard", "mechanical", "gaming", "corsair"]'),
                
                ("Smart Watch", "Electronics", "Wearables", "Samsung", 249.99, 299.99,
                 "Advanced health monitoring smartwatch",
                 '["Health tracking", "GPS", "Sleep monitoring", "Smartphone notifications"]',
                 '{"display": "1.4-inch", "battery": "2 days", "compatibility": "Android/iOS"}',
                 '["smartwatch", "wearable", "fitness", "samsung"]')
            ]
            
            for product in products_data:
                conn.execute(
                    text("""
                        INSERT INTO products (name, category, subcategory, brand, price, original_price, 
                        description, features, specifications, tags) 
                        VALUES (:name, :category, :subcategory, :brand, :price, :original_price, 
                        :description, :features, :specifications, :tags)
                    """),
                    {
                        "name": product[0], "category": product[1], "subcategory": product[2], 
                        "brand": product[3], "price": product[4], "original_price": product[5],
                        "description": product[6], "features": product[7], "specifications": product[8],
                        "tags": product[9]
                    }
                )
            
            # Insert comprehensive customers
            customers_data = [
                ("Johnathan Smith", "john.smith@email.com", "+1-555-0101", "123 Main Street", "New York", "NY", "10001", "USA", 
                 datetime(2022, 1, 15), "Gold", '{"categories": ["Electronics", "Books"], "brands": ["Apple", "Sony"]}'),
                
                ("Emily Johnson", "emily.johnson@email.com", "+1-555-0102", "456 Oak Avenue", "Los Angeles", "CA", "90210", "USA",
                 datetime(2021, 8, 22), "Platinum", '{"categories": ["Clothing", "Beauty"], "brands": ["Nike", "Levi\'s"]}'),
                
                ("Michael Brown", "michael.brown@email.com", "+1-555-0103", "789 Pine Road", "Chicago", "IL", "60601", "USA",
                 datetime(2023, 3, 10), "Silver", '{"categories": ["Electronics", "Sports"], "brands": ["Samsung", "JBL"]}'),
                
                ("Sarah Davis", "sarah.davis@email.com", "+1-555-0104", "321 Elm Street", "Houston", "TX", "77001", "USA",
                 datetime(2020, 11, 5), "Platinum", '{"categories": ["Home & Kitchen", "Beauty"], "brands": ["Dyson", "The Ordinary"]}'),
                
                ("David Wilson", "david.wilson@email.com", "+1-555-0105", "654 Maple Drive", "Phoenix", "AZ", "85001", "USA",
                 datetime(2022, 6, 18), "Gold", '{"categories": ["Automotive", "Electronics"], "brands": ["Logitech", "Corsair"]}'),
                
                ("Jennifer Miller", "jennifer.miller@email.com", "+1-555-0106", "987 Cedar Lane", "Philadelphia", "PA", "19101", "USA",
                 datetime(2021, 2, 28), "Silver", '{"categories": ["Toys", "Books"], "brands": ["LEGO", "Penguin"]}'),
                
                ("Robert Taylor", "robert.taylor@email.com", "+1-555-0107", "147 Birch Court", "San Antonio", "TX", "78201", "USA",
                 datetime(2023, 1, 8), "Bronze", '{"categories": ["Sports", "Electronics"], "brands": ["Hydro Flask", "Anker"]}'),
                
                ("Lisa Anderson", "lisa.anderson@email.com", "+1-555-0108", "258 Walnut Street", "San Diego", "CA", "92101", "USA",
                 datetime(2020, 9, 14), "Platinum", '{"categories": ["Clothing", "Home & Kitchen"], "brands": ["Lululemon", "Instant Pot"]}'),
                
                ("Thomas Martinez", "thomas.martinez@email.com", "+1-555-0109", "369 Spruce Avenue", "Dallas", "TX", "75201", "USA",
                 datetime(2022, 11, 30), "Gold", '{"categories": ["Automotive", "Sports"], "brands": ["iOttie", "JBL"]}'),
                
                ("Amanda Garcia", "amanda.garcia@email.com", "+1-555-0110", "741 Oakwood Drive", "San Jose", "CA", "95101", "USA",
                 datetime(2021, 7, 12), "Silver", '{"categories": ["Beauty", "Books"], "brands": ["The Ordinary", "No Starch Press"]}')
            ]
            
            for customer in customers_data:
                conn.execute(
                    text("""
                        INSERT INTO customers (name, email, phone, address, city, state, zip_code, country, 
                        customer_since, loyalty_tier, preferences) 
                        VALUES (:name, :email, :phone, :address, :city, :state, :zip_code, :country, 
                        :customer_since, :loyalty_tier, :preferences)
                    """),
                    {
                        "name": customer[0], "email": customer[1], "phone": customer[2], 
                        "address": customer[3], "city": customer[4], "state": customer[5],
                        "zip_code": customer[6], "country": customer[7], "customer_since": customer[8],
                        "loyalty_tier": customer[9], "preferences": customer[10]
                    }
                )
            
            # Insert inventory data
            for product_id in range(1, 21):
                conn.execute(
                    text("""
                        INSERT INTO inventory (product_id, quantity, low_stock_threshold, warehouse_location, last_restocked)
                        VALUES (:product_id, :quantity, :low_stock_threshold, :warehouse_location, :last_restocked)
                    """),
                    {
                        "product_id": product_id,
                        "quantity": random.randint(10, 200),
                        "low_stock_threshold": 20,
                        "warehouse_location": random.choice(["NYC", "LA", "CHI", "DAL", "ATL"]),
                        "last_restocked": datetime.utcnow() - timedelta(days=random.randint(1, 30))
                    }
                )
            
            # Insert product reviews
            review_id = 1
            for product_id in range(1, 21):
                for customer_id in range(1, 11):
                    if random.random() > 0.7:  # 30% chance of review
                        conn.execute(
                            text("""
                                INSERT INTO reviews (product_id, customer_id, rating, title, comment, verified_purchase, created_at)
                                VALUES (:product_id, :customer_id, :rating, :title, :comment, :verified_purchase, :created_at)
                            """),
                            {
                                "product_id": product_id,
                                "customer_id": customer_id,
                                "rating": random.randint(3, 5),
                                "title": f"Great product #{review_id}",
                                "comment": f"This is my detailed review for product {product_id}. I found it to be excellent quality and would recommend it to others.",
                                "verified_purchase": random.choice([True, False]),
                                "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 180))
                            }
                        )
                        review_id += 1
            
            # Insert comprehensive orders and order items
            for i in range(1, 51):  # 50 orders for more data
                order_date = (base_date + timedelta(days=days_offset)).isoformat
                base_date = date(2025, 7, 1)  # Start from July 2025
                days_offset = (i - 1) * 2  #
                customer_id = (i % 10) + 1
                status = random.choice(["completed", "completed", "completed", "completed", "pending", "shipped", "delivered"])
                order_date = (base_date + timedelta(days=days_offset)).isoformat()
                # Calculate order totals
                num_items = random.randint(1, 5)
                order_total = 0
                if order_date > "2025-10-31":
                    order_date = "2025-10-31"
                # First insert the order to get the ID
                order_result = conn.execute(
                    text("""
                        INSERT INTO orders (customer_id, order_date, total_amount, tax_amount, shipping_cost, final_amount, 
                        status, shipping_address, shipping_city, shipping_state, shipping_zip, payment_method, payment_status) 
                        VALUES (:customer_id, :order_date, :total_amount, :tax_amount, :shipping_cost, :final_amount,
                        :status, :shipping_address, :shipping_city, :shipping_state, :shipping_zip, :payment_method, :payment_status)
                        RETURNING id
                    """),
                    {
                        "customer_id": customer_id,
                        "order_date": order_date,
                        "total_amount": 0,  # Will update
                        "tax_amount": 0,    # Will update
                        "shipping_cost": 0, # Will update
                        "final_amount": 0,  # Will update
                        "status": status,
                        "shipping_address": f"{random.randint(100, 999)} {random.choice(['Main', 'Oak', 'Pine', 'Maple'])} St",
                        "shipping_city": random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]),
                        "shipping_state": random.choice(["NY", "CA", "IL", "TX", "AZ"]),
                        "shipping_zip": f"{random.randint(10000, 99999)}",
                        "payment_method": random.choice(["credit_card", "paypal", "apple_pay", "google_pay"]),
                        "payment_status": "paid" if status in ["completed", "shipped", "delivered"] else "pending"
                    }
                )
                
                order_id = order_result.scalar()
                
                # Add order items and calculate totals
                for j in range(num_items):
                    product_id = random.randint(1, 20)
                    quantity = random.randint(1, 3)
                    unit_price = (product_id * 50) + random.randint(10, 99) + 0.99
                    item_total = quantity * unit_price
                    order_total += item_total
                    
                    # Get product name
                    product_result = conn.execute(
                        text("SELECT name FROM products WHERE id = :product_id"),
                        {"product_id": product_id}
                    )
                    product_name = product_result.scalar()
                    
                    conn.execute(
                        text("""
                            INSERT INTO order_items (order_id, product_id, product_name, quantity, unit_price, item_total)
                            VALUES (:order_id, :product_id, :product_name, :quantity, :unit_price, :item_total)
                        """),
                        {
                            "order_id": order_id,
                            "product_id": product_id,
                            "product_name": product_name,
                            "quantity": quantity,
                            "unit_price": unit_price,
                            "item_total": item_total
                        }
                    )
                
                # Update order with calculated totals
                tax_amount = round(order_total * 0.08, 2)
                shipping_cost = 9.99 if order_total < 100 else 0
                final_amount = order_total + tax_amount + shipping_cost
                
                conn.execute(
                    text("""
                        UPDATE orders 
                        SET total_amount = :total_amount, tax_amount = :tax_amount, 
                            shipping_cost = :shipping_cost, final_amount = :final_amount
                        WHERE id = :order_id
                    """),
                    {
                        "total_amount": round(order_total, 2),
                        "tax_amount": tax_amount,
                        "shipping_cost": shipping_cost,
                        "final_amount": round(final_amount, 2),
                        "order_id": order_id
                    }
                )
            
            print("✅ PostgreSQL comprehensive sample data initialization completed")
            
            # Verify data insertion
            counts = conn.execute(text("""
                SELECT 
                    (SELECT COUNT(*) FROM products) as products,
                    (SELECT COUNT(*) FROM customers) as customers,
                    (SELECT COUNT(*) FROM orders) as orders,
                    (SELECT COUNT(*) FROM categories) as categories,
                    (SELECT COUNT(*) FROM reviews) as reviews,
                    (SELECT COUNT(*) FROM inventory) as inventory
            """)).fetchone()
            
            print(f"📊 Data verification - Products: {counts[0]}, Customers: {counts[1]}, Orders: {counts[2]}")
            print(f"📊 Additional data - Categories: {counts[3]}, Reviews: {counts[4]}, Inventory: {counts[5]}")

    async def get_weekly_revenue(self, start_date: date, end_date: date) -> float:
        with self.engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT COALESCE(SUM(total_amount), 0) as total_revenue
                    FROM orders 
                    WHERE order_date BETWEEN :start_date AND :end_date
                    AND status = 'completed'
                """),
                {"start_date": start_date, "end_date": end_date}
            )
            row = result.fetchone()
            return float(row[0]) if row else 0.0

    async def get_daily_sales(self, target_date: date) -> List[Dict[str, Any]]:
        with self.engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT 
                        o.id as order_id,
                        c.name as customer_name,
                        o.total_amount,
                        o.status,
                        COUNT(oi.id) as item_count
                    FROM orders o
                    LEFT JOIN customers c ON o.customer_id = c.id
                    LEFT JOIN order_items oi ON o.id = oi.order_id
                    WHERE o.order_date = :target_date
                    GROUP BY o.id, c.name, o.total_amount, o.status
                """),
                {"target_date": target_date}
            )
            return [dict(row._mapping) for row in result]

    async def get_top_products(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self.engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT 
                        p.name,
                        p.category,
                        SUM(oi.quantity) as total_sold,
                        SUM(oi.quantity * oi.unit_price) as total_revenue
                    FROM products p
                    JOIN order_items oi ON p.id = oi.product_id
                    JOIN orders o ON oi.order_id = o.id
                    WHERE o.status = 'completed'
                    GROUP BY p.id, p.name, p.category
                    ORDER BY total_revenue DESC
                    LIMIT :limit
                """),
                {"limit": limit}
            )
            return [dict(row._mapping) for row in result]

    async def get_customer_orders(self, customer_id: str) -> List[Dict[str, Any]]:
        with self.engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT 
                        o.id as order_id,
                        o.order_date,
                        o.total_amount,
                        o.status,
                        COUNT(oi.id) as item_count
                    FROM orders o
                    LEFT JOIN order_items oi ON o.id = oi.order_id
                    WHERE o.customer_id = :customer_id
                    GROUP BY o.id, o.order_date, o.total_amount, o.status
                    ORDER BY o.order_date DESC
                """),
                {"customer_id": int(customer_id)}
            )
            return [dict(row._mapping) for row in result]

    async def get_sales_by_category(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        with self.engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT 
                        p.category,
                        COUNT(DISTINCT o.id) as order_count,
                        SUM(oi.quantity) as total_quantity,
                        SUM(oi.quantity * oi.unit_price) as total_revenue
                    FROM products p
                    JOIN order_items oi ON p.id = oi.product_id
                    JOIN orders o ON oi.order_id = o.id
                    WHERE o.order_date BETWEEN :start_date AND :end_date
                    AND o.status = 'completed'
                    GROUP BY p.category
                    ORDER BY total_revenue DESC
                """),
                {"start_date": start_date, "end_date": end_date}
            )
            return [dict(row._mapping) for row in result]

    async def get_monthly_revenue_trend(self, months: int = 6) -> List[Dict[str, Any]]:
        end_date = date.today()
        start_date = end_date - timedelta(days=30*months)
        
        with self.engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT 
                        DATE_TRUNC('month', order_date) as month,
                        SUM(total_amount) as monthly_revenue,
                        COUNT(*) as order_count
                    FROM orders
                    WHERE order_date BETWEEN :start_date AND :end_date
                    AND status = 'completed'
                    GROUP BY DATE_TRUNC('month', order_date)
                    ORDER BY month
                """),
                {"start_date": start_date, "end_date": end_date}
            )
            return [dict(row._mapping) for row in result]

    async def execute_custom_query(self, query: str) -> List[Dict[str, Any]]:
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                columns = result.keys()
                return [dict(zip(columns, row)) for row in result]
        except Exception as e:
            raise Exception(f"Query execution error: {str(e)}")

    async def get_all_customers(self) -> List[Dict[str, Any]]:
        with self.engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM customers ORDER BY id")
            )
            return [dict(row._mapping) for row in result]

    async def get_all_products(self) -> List[Dict[str, Any]]:
        with self.engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM products ORDER BY id")
            )
            return [dict(row._mapping) for row in result]

    async def get_recent_orders(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self.engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT o.*, c.name as customer_name 
                    FROM orders o 
                    LEFT JOIN customers c ON o.customer_id = c.id 
                    WHERE o.status = 'completed'
                    ORDER BY o.order_date DESC 
                    LIMIT :limit
                """),
                {"limit": limit}
            )
            return [dict(row._mapping) for row in result]

    async def execute_dynamic_query(self, table: str, fields: List[str], filters: Dict[str, Any], 
                                  sort_by: str = None, sort_order: str = "desc", limit: int = 50,
                                  query_type: str = "general", operation: str = "get") -> List[Dict[str, Any]]:
        """Execute dynamic queries with enhanced capabilities including search"""
        
        # Handle product search queries
        if table == "products" and filters.get('search_term'):
            return await self.get_products_by_search(filters['search_term'])
        try:
            # Handle product price queries dynamically
            if query_type == "product_price":
                return await self._handle_product_price_queries(operation, filters, limit)
            
            # Handle aggregation queries differently
            if any('(' in field for field in fields) or query_type == "aggregation":
                return await self._handle_aggregation_query(table, fields, filters, sort_by, sort_order, limit)
            
            # Handle analytics queries with grouping
            if query_type == "analytics" and any(keyword in str(fields) for keyword in ['SUM', 'COUNT', 'AVG', 'MAX', 'MIN']):
                return await self._handle_analytics_query(table, fields, filters, sort_by, sort_order, limit)
            
            # Regular SELECT query
            return await self._handle_select_query(table, fields, filters, sort_by, sort_order, limit)
            
        except Exception as e:
            print(f"Dynamic query failed: {e}")
            # Ultimate fallback - simple select
            return await self._execute_simple_fallback(table, limit)

    async def _handle_product_price_queries(self, operation: str, filters: Dict[str, Any], limit: int = 1) -> List[Dict[str, Any]]:
        """Handle product price queries dynamically"""
        
        if operation == "get_costliest_product":
            query = """
                SELECT name, category, price 
                FROM products 
                ORDER BY price DESC 
                LIMIT 1
            """
        elif operation == "get_cheapest_product":
            query = """
                SELECT name, category, price 
                FROM products 
                ORDER BY price ASC 
                LIMIT 1
            """
        elif operation == "get_product_price_range":
            query = """
                SELECT 
                    MIN(price) as min_price,
                    MAX(price) as max_price,
                    AVG(price) as avg_price,
                    COUNT(*) as product_count
                FROM products
            """
        elif operation == "get_average_product_price":
            query = "SELECT AVG(price) as avg_price FROM products"
        else:
            # Fallback to get all products
            query = "SELECT * FROM products ORDER BY price DESC LIMIT :limit"
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query), {"limit": limit} if "LIMIT" in query else {})
            
            if operation in ["get_product_price_range", "get_average_product_price"]:
                row = result.fetchone()
                return [dict(row._mapping)] if row else [{}]
            else:
                return [dict(row._mapping) for row in result]
                
    async def _handle_aggregation_query(self, table: str, fields: List[str], filters: Dict[str, Any],
                                      sort_by: str = None, sort_order: str = "desc", limit: int = 50) -> List[Dict[str, Any]]:
        """Handle aggregation queries with proper GROUP BY"""
        field_list = ", ".join(fields)
        
        # Build WHERE clause
        where_conditions = []
        params = {}
        param_count = 0
        
        for key, value in filters.items():
            where_conditions.append(f"{key} = :param_{param_count}")
            params[f"param_{param_count}"] = value
            param_count += 1
        
        where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # For aggregation, we need to identify non-aggregated fields for GROUP BY
        non_agg_fields = []
        for field in fields:
            if not any(op in field.upper() for op in ['SUM(', 'COUNT(', 'AVG(', 'MAX(', 'MIN(', 'DATE_TRUNC(']):
                # Extract field name without alias
                field_name = field.split(' as ')[0].strip() if ' as ' in field else field.strip()
                non_agg_fields.append(field_name)
        
        group_by_clause = " GROUP BY " + ", ".join(non_agg_fields) if non_agg_fields else ""
        
        # Build ORDER BY clause
        order_clause = ""
        if sort_by:
            # Handle ordering by aggregated fields
            if any(op in sort_by.upper() for op in ['SUM(', 'COUNT(', 'AVG(', 'MAX(', 'MIN(']):
                order_clause = f" ORDER BY {sort_by} {sort_order.upper()}"
            else:
                order_clause = f" ORDER BY {sort_by} {sort_order.upper()}"
        
        # Build LIMIT clause
        limit_clause = f" LIMIT {limit}" if limit else ""
        
        # Construct final query
        query = f"SELECT {field_list} FROM {table}{where_clause}{group_by_clause}{order_clause}{limit_clause}"
        
        print(f"Executing aggregation query: {query}")
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query), params)
            return [dict(row._mapping) for row in result]

    async def _handle_analytics_query(self, table: str, fields: List[str], filters: Dict[str, Any],
                                    sort_by: str = None, sort_order: str = "desc", limit: int = 50) -> List[Dict[str, Any]]:
        """Handle analytics queries with proper grouping"""
        # For analytics queries, use predefined methods when possible
        if "month" in str(fields) and "revenue" in str(fields):
            # Use existing monthly trend method
            return await self.get_monthly_revenue_trend(12)
        elif "category" in str(fields) and "revenue" in str(fields):
            # Use sales by category method
            return await self.get_sales_by_category(date.today().replace(day=1), date.today())
        
        # Fallback to aggregation query
        return await self._handle_aggregation_query(table, fields, filters, sort_by, sort_order, limit)

    async def _handle_select_query(self, table: str, fields: List[str], filters: Dict[str, Any],
                                 sort_by: str = None, sort_order: str = "desc", limit: int = 50) -> List[Dict[str, Any]]:
        """Handle regular SELECT queries"""
        field_list = ", ".join(fields) if fields != ["*"] else "*"
        
        # Build WHERE clause
        where_conditions = []
        params = {}
        param_count = 0
        
        for key, value in filters.items():
            if isinstance(value, str) and value.startswith(('>', '<', '>=', '<=')):
                operator = value[0] if value[1] != '=' else value[:2]
                actual_value = value[1:] if value[1] != '=' else value[2:]
                where_conditions.append(f"{key} {operator} :param_{param_count}")
                params[f"param_{param_count}"] = actual_value
            elif isinstance(value, str) and "days" in value:
                days = int(''.join(filter(str.isdigit, value)))
                where_conditions.append(f"{key} < CURRENT_DATE - INTERVAL '{days} days'")
            elif value == ">1":  # Special case for order_count > 1
                where_conditions.append(f"{key} > 1")
            else:
                where_conditions.append(f"{key} = :param_{param_count}")
                params[f"param_{param_count}"] = value
            param_count += 1
        
        # Build ORDER BY clause
        order_clause = ""
        if sort_by:
            order_clause = f" ORDER BY {sort_by} {sort_order.upper()}"
        
        # Build LIMIT clause
        limit_clause = f" LIMIT {limit}" if limit else ""
        
        # Construct final query
        query = f"SELECT {field_list} FROM {table}"
        
        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)
        
        query += order_clause + limit_clause
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query), params)
            return [dict(row._mapping) for row in result]

    async def _execute_simple_fallback(self, table: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Ultimate fallback - simple SELECT with limit"""
        query = f"SELECT * FROM {table} LIMIT {limit}"
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query))
            return [dict(row._mapping) for row in result]

    async def get_least_sold_products(self, limit: int = 5) -> List[Dict[str, Any]]:
        with self.engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT 
                        p.name,
                        p.category,
                        COALESCE(SUM(oi.quantity), 0) as total_sold,
                        COALESCE(SUM(oi.quantity * oi.unit_price), 0) as total_revenue
                    FROM products p
                    LEFT JOIN order_items oi ON p.id = oi.product_id
                    LEFT JOIN orders o ON oi.order_id = o.id AND o.status = 'completed'
                    GROUP BY p.id, p.name, p.category
                    ORDER BY total_sold ASC, total_revenue ASC
                    LIMIT :limit
                """),
                {"limit": limit}
            )
            return [dict(row._mapping) for row in result]

    async def get_repeat_customers(self) -> List[Dict[str, Any]]:
        with self.engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT 
                        c.id,
                        c.name,
                        c.email,
                        COUNT(o.id) as order_count,
                        SUM(o.total_amount) as total_spent
                    FROM customers c
                    JOIN orders o ON c.id = o.customer_id
                    WHERE o.status = 'completed'
                    GROUP BY c.id, c.name, c.email
                    HAVING COUNT(o.id) > 1
                    ORDER BY order_count DESC, total_spent DESC
                """)
            )
            return [dict(row._mapping) for row in result]

    async def get_all_time_revenue(self) -> float:
        with self.engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT COALESCE(SUM(total_amount), 0) as total_revenue
                    FROM orders 
                    WHERE status = 'completed'
                """)
            )
            row = result.fetchone()
            return float(row[0]) if row else 0.0

    async def get_inactive_customers(self, days_threshold: int = 30) -> List[Dict[str, Any]]:
        with self.engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT 
                        c.id,
                        c.name,
                        c.email,
                        MAX(o.order_date) as last_order_date,
                        EXTRACT(DAY FROM (CURRENT_DATE - MAX(o.order_date))) as days_since_last_order
                    FROM customers c
                    LEFT JOIN orders o ON c.id = o.customer_id
                    GROUP BY c.id, c.name, c.email
                    HAVING MAX(o.order_date) IS NULL 
                        OR EXTRACT(DAY FROM (CURRENT_DATE - MAX(o.order_date))) > :days_threshold
                    ORDER BY days_since_last_order DESC
                """),
                {"days_threshold": days_threshold}
            )
            return [dict(row._mapping) for row in result]

    async def get_peak_revenue_month(self, year: int = None) -> Dict[str, Any]:
        if year is None:
            year = date.today().year
            
        with self.engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT 
                        DATE_TRUNC('month', order_date) as month,
                        SUM(total_amount) as monthly_revenue,
                        COUNT(*) as order_count
                    FROM orders
                    WHERE status = 'completed'
                    AND EXTRACT(YEAR FROM order_date) = :year
                    GROUP BY DATE_TRUNC('month', order_date)
                    ORDER BY monthly_revenue DESC
                    LIMIT 1
                """),
                {"year": year}
            )
            row = result.fetchone()
            return dict(row._mapping) if row else {}

    async def get_customer_product_preferences(self) -> List[Dict[str, Any]]:
        with self.engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT 
                        c.id as customer_id,
                        c.name as customer_name,
                        p.id as product_id, 
                        p.name as product_name,
                        p.category,
                        SUM(oi.quantity) as total_quantity,
                        COUNT(DISTINCT o.id) as times_ordered
                    FROM customers c
                    JOIN orders o ON c.id = o.customer_id
                    JOIN order_items oi ON o.id = oi.order_id
                    JOIN products p ON oi.product_id = p.id
                    WHERE o.status = 'completed'
                    GROUP BY c.id, c.name, p.id, p.name, p.category
                    ORDER BY c.name, total_quantity DESC
                """)
            )
            return [dict(row._mapping) for row in result]          

    async def get_costliest_product(self) -> List[Dict[str, Any]]:
        with self.engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT name, category, price 
                    FROM products 
                    ORDER BY price DESC 
                    LIMIT 1
                """)
            )
            return [dict(row._mapping) for row in result]

    async def get_cheapest_product(self) -> List[Dict[str, Any]]:
        with self.engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT name, category, price 
                    FROM products 
                    ORDER BY price ASC 
                    LIMIT 1
                """)
            )
            return [dict(row._mapping) for row in result]

    async def get_product_price_range(self) -> Dict[str, Any]:
        with self.engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT 
                        MIN(price) as min_price,
                        MAX(price) as max_price,
                        AVG(price) as avg_price,
                        COUNT(*) as product_count
                    FROM products
                """)
            )
            row = result.fetchone()
            return dict(row._mapping) if row else {}

    async def get_average_product_price(self) -> float:
        with self.engine.connect() as conn:
            result = conn.execute(
                text("SELECT AVG(price) as avg_price FROM products")
            )
            row = result.fetchone()
            return float(row[0]) if row else 0.0

    async def get_all_categories(self) -> List[Dict[str, Any]]:
        """Get all product categories"""
        with self.engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM categories ORDER BY name")
            )
            return [dict(row._mapping) for row in result]

    async def get_product_reviews(self, product_id: str) -> List[Dict[str, Any]]:
        """Get reviews for a specific product"""
        with self.engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT 
                        r.rating,
                        r.title,
                        r.comment,
                        r.verified_purchase,
                        r.created_at,
                        c.name as customer_name
                    FROM reviews r
                    JOIN customers c ON r.customer_id = c.id
                    WHERE r.product_id = :product_id
                    ORDER BY r.created_at DESC
                """),
                {"product_id": int(product_id)}
            )
            return [dict(row._mapping) for row in result]

    async def get_inventory_status(self) -> List[Dict[str, Any]]:
        """Get current inventory status with product details"""
        with self.engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT 
                        i.product_id,
                        p.name as product_name,
                        p.category,
                        i.quantity,
                        i.low_stock_threshold,
                        i.warehouse_location,
                        i.last_restocked,
                        (i.quantity < i.low_stock_threshold) as is_low_stock
                    FROM inventory i
                    JOIN products p ON i.product_id = p.id
                    ORDER BY is_low_stock DESC, i.quantity ASC
                """)
            )
            return [dict(row._mapping) for row in result]

    async def get_products_by_search(self, search_term: str) -> List[Dict[str, Any]]:
        """Get products by search term in name"""
        with self.engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM products WHERE LOWER(name) LIKE LOWER(:search_term)"),
                {"search_term": f"%{search_term}%"}
            )
            results = [dict(row._mapping) for row in result]
            print(f"✅ Products search for '{search_term}': {len(results)} results")
            return results


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
            
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT COALESCE(SUM(total_amount), 0) as monthly_revenue
                        FROM orders 
                        WHERE order_date BETWEEN :start_date AND :end_date
                        AND status = 'completed'
                    """),
                    {"start_date": start_date, "end_date": end_date}
                )
                row = result.fetchone()
                revenue = float(row[0]) if row else 0.0
                month_name = start_date.strftime('%B %Y')
                print(f"✅ Monthly revenue for {month_name}: ${revenue:,.2f}")
                return revenue
        except Exception as e:
            print(f"❌ Error in get_monthly_revenue: {e}")
            return 0.0


            