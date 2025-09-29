from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from app.utils.helpers import sanitize_query_string

class QueryBuilder:
    """Builds database queries based on analytics requirements"""
    
    @staticmethod
    def build_weekly_revenue_query(start_date: date, end_date: date, db_type: str) -> Dict[str, Any]:
        """
        Build query for weekly revenue calculation
        
        Args:
            start_date: Start date of the week
            end_date: End date of the week
            db_type: Database type ('postgres' or 'mongodb')
        
        Returns:
            Query dictionary with 'query' and 'params' keys
        """
        if db_type == "postgres":
            query = """
                SELECT COALESCE(SUM(total_amount), 0) as total_revenue
                FROM orders 
                WHERE order_date BETWEEN :start_date AND :end_date
                AND status = 'completed'
            """
            params = {"start_date": start_date, "end_date": end_date}
            return {"query": query, "params": params}
        
        elif db_type == "mongodb":
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
            return {"query": pipeline, "params": {}}
        
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    @staticmethod
    def build_daily_sales_query(target_date: date, db_type: str) -> Dict[str, Any]:
        """
        Build query for daily sales data
        
        Args:
            target_date: Target date
            db_type: Database type
        
        Returns:
            Query dictionary
        """
        if db_type == "postgres":
            query = """
                SELECT 
                    o.id as order_id,
                    c.name as customer_name,
                    o.total_amount,
                    o.status,
                    COUNT(oi.id) as item_count,
                    o.order_date
                FROM orders o
                LEFT JOIN customers c ON o.customer_id = c.id
                LEFT JOIN order_items oi ON o.id = oi.order_id
                WHERE o.order_date = :target_date
                GROUP BY o.id, c.name, o.total_amount, o.status, o.order_date
                ORDER BY o.id
            """
            params = {"target_date": target_date}
            return {"query": query, "params": params}
        
        elif db_type == "mongodb":
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
                        "item_count": {"$size": "$items"},
                        "order_date": 1
                    }
                },
                {
                    "$sort": {"order_id": 1}
                }
            ]
            return {"query": pipeline, "params": {}}
        
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    @staticmethod
    def build_top_products_query(limit: int, db_type: str) -> Dict[str, Any]:
        """
        Build query for top products by revenue
        
        Args:
            limit: Number of products to return
            db_type: Database type
        
        Returns:
            Query dictionary
        """
        if db_type == "postgres":
            query = """
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
            """
            params = {"limit": limit}
            return {"query": query, "params": params}
        
        elif db_type == "mongodb":
            pipeline = [
                {
                    "$match": {
                        "status": "completed"
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
            return {"query": pipeline, "params": {}}
        
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    @staticmethod
    def build_customer_orders_query(customer_id: str, db_type: str) -> Dict[str, Any]:
        """
        Build query for customer order history
        
        Args:
            customer_id: Customer ID
            db_type: Database type
        
        Returns:
            Query dictionary
        """
        if db_type == "postgres":
            query = """
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
            """
            params = {"customer_id": int(customer_id)}
            return {"query": query, "params": params}
        
        elif db_type == "mongodb":
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
            return {"query": pipeline, "params": {}}
        
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    @staticmethod
    def build_sales_by_category_query(start_date: date, end_date: date, db_type: str) -> Dict[str, Any]:
        """
        Build query for sales breakdown by category
        
        Args:
            start_date: Start date
            end_date: End date
            db_type: Database type
        
        Returns:
            Query dictionary
        """
        if db_type == "postgres":
            query = """
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
            """
            params = {"start_date": start_date, "end_date": end_date}
            return {"query": query, "params": params}
        
        elif db_type == "mongodb":
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
            return {"query": pipeline, "params": {}}
        
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    @staticmethod
    def build_monthly_revenue_trend_query(months: int, db_type: str) -> Dict[str, Any]:
        """
        Build query for monthly revenue trend
        
        Args:
            months: Number of months to analyze
            db_type: Database type
        
        Returns:
            Query dictionary
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=30*months)
        
        if db_type == "postgres":
            query = """
                SELECT 
                    DATE_TRUNC('month', order_date) as month,
                    SUM(total_amount) as monthly_revenue,
                    COUNT(*) as order_count
                FROM orders
                WHERE order_date BETWEEN :start_date AND :end_date
                AND status = 'completed'
                GROUP BY DATE_TRUNC('month', order_date)
                ORDER BY month
            """
            params = {"start_date": start_date, "end_date": end_date}
            return {"query": query, "params": params}
        
        elif db_type == "mongodb":
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
            return {"query": pipeline, "params": {}}
        
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    @staticmethod
    def build_custom_query(query: str, db_type: str) -> Dict[str, Any]:
        """
        Build custom query based on user input
        
        Args:
            query: Custom query string
            db_type: Database type
        
        Returns:
            Query dictionary
        """
        sanitized_query = sanitize_query_string(query)
        
        if db_type == "postgres":
            return {"query": sanitized_query, "params": {}}
        
        elif db_type == "mongodb":
            # For MongoDB, try to parse as aggregation pipeline
            try:
                import json
                pipeline = json.loads(sanitized_query)
                return {"query": pipeline, "params": {}}
            except:
                # If not valid JSON, treat as collection name
                return {"query": sanitized_query, "params": {}}
        
        else:
            raise ValueError(f"Unsupported database type: {db_type}")