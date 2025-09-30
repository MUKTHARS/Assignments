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

    async def create_tables(self):
        """Create all tables if they don't exist"""
        try:
            self.metadata.create_all(bind=self.engine)
            print("✅ PostgreSQL tables created successfully")
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            raise

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
                    ORDER BY o.order_date DESC 
                    LIMIT :limit
                """),
                {"limit": limit}
            )
            return [dict(row._mapping) for row in result]

    async def execute_dynamic_query(self, table: str, fields: List[str], filters: Dict[str, Any], 
                                  sort_by: str = None, sort_order: str = "desc", limit: int = 50,
                                  query_type: str = "general", operation: str = "get") -> List[Dict[str, Any]]:
        """Execute dynamic queries with advanced capabilities including product price queries"""
        
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