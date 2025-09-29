import asyncpg
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, Float, DateTime, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
import json

from .base import DatabaseInterface

class PostgresDB(DatabaseInterface):
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.engine = None
        self.SessionLocal = None
        self.metadata = MetaData()
        
        # Define tables
        self.products = Table(
            'products', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String),
            Column('category', String),
            Column('price', Float),
            Column('created_at', DateTime, default=datetime.utcnow)
        )
        
        self.customers = Table(
            'customers', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String),
            Column('email', String),
            Column('created_at', DateTime, default=datetime.utcnow)
        )
        
        self.orders = Table(
            'orders', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('customer_id', Integer),
            Column('order_date', Date),
            Column('total_amount', Float),
            Column('status', String),
            Column('created_at', DateTime, default=datetime.utcnow)
        )
        
        self.order_items = Table(
            'order_items', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('order_id', Integer),
            Column('product_id', Integer),
            Column('quantity', Integer),
            Column('unit_price', Float),
            Column('created_at', DateTime, default=datetime.utcnow)
        )

    async def connect(self):
        try:
            self.engine = create_engine(self.connection_string)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            self.metadata.create_all(bind=self.engine)
            print("PostgreSQL connected successfully")
        except Exception as e:
            print(f"Error connecting to PostgreSQL: {e}")
            raise

    async def disconnect(self):
        if self.engine:
            self.engine.dispose()

    async def get_weekly_revenue(self, start_date: date, end_date: date) -> float:
        with self.engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT COALESCE(SUM(total_amount), 0) as total_revenue
                    FROM orders 
                    WHERE order_date BETWEEN :start_date AND :end_date
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

    async def initialize_sample_data(self):
        """Initialize sample data for testing"""
        with self.engine.begin() as conn:
            # Check if data already exists
            result = conn.execute(text("SELECT COUNT(*) FROM products"))
            count = result.scalar()
            
            if count > 0:
                return  # Data already exists
            
            # Insert sample products
            products_data = [
                {"name": "Laptop", "category": "Electronics", "price": 999.99},
                {"name": "Smartphone", "category": "Electronics", "price": 699.99},
                {"name": "Headphones", "category": "Electronics", "price": 149.99},
                {"name": "T-Shirt", "category": "Clothing", "price": 29.99},
                {"name": "Jeans", "category": "Clothing", "price": 59.99},
                {"name": "Book", "category": "Education", "price": 19.99},
                {"name": "Coffee Mug", "category": "Home", "price": 12.99},
            ]
            
            for product in products_data:
                conn.execute(
                    text("INSERT INTO products (name, category, price) VALUES (:name, :category, :price)"),
                    product
                )
            
            # Insert sample customers
            customers_data = [
                {"name": "John Doe", "email": "john@example.com"},
                {"name": "Jane Smith", "email": "jane@example.com"},
                {"name": "Bob Johnson", "email": "bob@example.com"},
            ]
            
            for customer in customers_data:
                conn.execute(
                    text("INSERT INTO customers (name, email) VALUES (:name, :email)"),
                    customer
                )
            
            # Insert sample orders and order items
            from datetime import date, timedelta
            
            for i in range(20):
                order_date = date.today() - timedelta(days=i*2)
                customer_id = (i % 3) + 1
                total_amount = (i + 1) * 50
                
                order_result = conn.execute(
                    text("""
                        INSERT INTO orders (customer_id, order_date, total_amount, status) 
                        VALUES (:customer_id, :order_date, :total_amount, :status)
                        RETURNING id
                    """),
                    {
                        "customer_id": customer_id,
                        "order_date": order_date,
                        "total_amount": total_amount,
                        "status": "completed"
                    }
                )
                
                order_id = order_result.scalar()
                
                # Add order items
                for j in range(1, 4):
                    product_id = ((i + j) % 7) + 1
                    conn.execute(
                        text("""
                            INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                            VALUES (:order_id, :product_id, :quantity, :unit_price)
                        """),
                        {
                            "order_id": order_id,
                            "product_id": product_id,
                            "quantity": j,
                            "unit_price": (product_id * 10) + 9.99
                        }
                    )