from app.database.factory import DatabaseFactory
from app.services.llm_service import LLMService
from datetime import datetime, date, timedelta
from typing import Dict, Any, List
import json

class AnalyticsService:
    def __init__(self):
        self.llm_service = LLMService()
        self.db = None

    async def initialize_database(self):
        """Initialize database connection"""
        if not self.db:
            print("🔄 Initializing database connection...")
            self.db = await DatabaseFactory.create_database()
            print("🔄 Creating sample data...")
            await DatabaseFactory.initialize_sample_data(self.db)
            print("✅ Database initialization completed")
        else:
            print("✅ Database already initialized")    

    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process natural language query and return results"""
        
        if not self.db:
            await self.initialize_database()
        
        # Parse the natural language query
        parsed_intent = self.llm_service.parse_natural_language(query)
        
        if parsed_intent["intent"] == "unknown":
            return {
                "success": False,
                "error": "I couldn't understand your query. Please try rephrasing it.",
                "data": None,
                "response": "I couldn't understand your query. Please try rephrasing it."
            }
        
        try:
            # Execute the appropriate function based on intent
            data = await self._execute_analytics_function(
                parsed_intent["intent"], 
                parsed_intent["parameters"]
            )
            
            # Serialize data for JSON response
            serialized_data = self._serialize_data(data)
            
            # Generate natural language response
            natural_response = await self.llm_service.generate_natural_response(
                serialized_data, query
            )
            
            return {
                "success": True,
                "intent": parsed_intent["intent"],
                "parameters": parsed_intent["parameters"],
                "data": serialized_data,
                "response": natural_response
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"Query processing error: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "data": None,
                "response": f"Sorry, I encountered an error while processing your query: {error_msg}"
            }

    async def _execute_analytics_function(self, intent: str, parameters: Dict[str, Any]) -> Any:
        """Execute the appropriate analytics function"""
        
        # Handle date parameters
        processed_params = self._process_parameters(parameters)
        
        if intent == "execute_dynamic_query":
            # Extract dynamic query parameters
            return await self.db.execute_dynamic_query(
                table=processed_params.get("table", "customers"),
                fields=processed_params.get("fields", ["*"]),
                filters=processed_params.get("filters", {}),
                sort_by=processed_params.get("sort_by"),
                sort_order=processed_params.get("sort_order", "desc"),
                limit=processed_params.get("limit", 50),
                query_type=processed_params.get("query_type", "general"),
                operation=processed_params.get("operation", "get")
            )
            
        elif intent == "get_daily_sales":
            return await self.db.get_daily_sales(
                processed_params["target_date"]
            )
            
        elif intent == "get_top_products":
            return await self.db.get_top_products(
                processed_params.get("limit", 10)
            )
            
        elif intent == "get_customer_orders":
            return await self.db.get_customer_orders(
                processed_params["customer_id"]
            )
            
        elif intent == "get_sales_by_category":
            return await self.db.get_sales_by_category(
                processed_params["start_date"],
                processed_params["end_date"]
            )
            
        elif intent == "get_monthly_revenue_trend":
            return await self.db.get_monthly_revenue_trend(
                processed_params.get("months", 6)
            )
        
        elif intent == "get_all_customers":
            return await self.db.get_all_customers()
            
        elif intent == "get_all_products":
            return await self.db.get_all_products()
            
        elif intent == "get_recent_orders":
            return await self.db.get_recent_orders(
                processed_params.get("limit", 10)
            )
            
        elif intent == "execute_custom_query":
            # For completely dynamic queries
            return await self.db.execute_dynamic_query(
                processed_params.get("table", "customers"),
                processed_params.get("fields", ["*"]),
                processed_params.get("filters", {})
            )

        elif intent == "get_least_sold_products":
            return await self.db.get_least_sold_products(
                processed_params.get("limit", 5)
            )
            
        elif intent == "get_repeat_customers":
            return await self.db.get_repeat_customers()
            
        elif intent == "get_all_time_revenue":
            return await self.db.get_all_time_revenue()
            
        elif intent == "get_inactive_customers":
            return await self.db.get_inactive_customers(
                processed_params.get("days_threshold", 30)
            )
            
        elif intent == "get_peak_revenue_month":
            return await self.db.get_peak_revenue_month(
                processed_params.get("year")
            )
            
        elif intent == "get_customer_product_preferences":
            return await self.db.get_customer_product_preferences()
            
        elif intent == "get_costliest_product":
            return await self.db.get_costliest_product()
    
        elif intent == "get_cheapest_product":
            return await self.db.get_cheapest_product()
    
        elif intent == "get_product_price_range":
            return await self.db.get_product_price_range()
    
        elif intent == "get_average_product_price":
            return await self.db.get_average_product_price()
        
        else:
            raise ValueError(f"Unknown intent: {intent}")

    def _process_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate parameters"""
        from datetime import datetime, date, timedelta
        
        processed = parameters.copy()
        
        # Handle date calculations
        today = date.today()
        
        if "start_date" in parameters:
            if parameters["start_date"] == "this_week":
                start_of_week = today - timedelta(days=today.weekday())
                processed["start_date"] = start_of_week
                if "end_date" not in processed or processed["end_date"] == "this_week":
                    processed["end_date"] = start_of_week + timedelta(days=6)
            
            elif parameters["start_date"] == "last_week":
                start_of_last_week = today - timedelta(days=today.weekday() + 7)
                processed["start_date"] = start_of_last_week
                if "end_date" not in processed or processed["end_date"] == "last_week":
                    processed["end_date"] = start_of_last_week + timedelta(days=6)
            
            elif parameters["start_date"] == "last_month":
                first_day_current_month = today.replace(day=1)
                last_month = first_day_current_month - timedelta(days=1)
                first_day_last_month = last_month.replace(day=1)
                processed["start_date"] = first_day_last_month
                if "end_date" not in processed or processed["end_date"] == "today":
                    processed["end_date"] = today
        
        if "end_date" in parameters and parameters["end_date"] == "today":
            processed["end_date"] = today
        
        if "target_date" in parameters:
            if parameters["target_date"] == "today":
                processed["target_date"] = today
            elif parameters["target_date"] == "yesterday":
                processed["target_date"] = today - timedelta(days=1)
        
        # Ensure all date parameters are actual date objects
        for key in ['start_date', 'end_date', 'target_date']:
            if key in processed and isinstance(processed[key], str):
                # Try to parse string dates
                try:
                    processed[key] = datetime.strptime(processed[key], '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    # If parsing fails, use today as fallback
                    processed[key] = today
        
        return processed

    def _serialize_data(self, data: Any) -> Any:
        """Convert non-serializable objects to strings for JSON response"""
        import json
        from datetime import datetime, date
        
        def default_serializer(obj):
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            elif hasattr(obj, '__dict__'):
                return obj.__dict__
            else:
                return str(obj)
        
        try:
            # Try to serialize the data
            if data is None:
                return None
                
            # For simple types, return as is
            if isinstance(data, (str, int, float, bool)):
                return data
                
            # For lists and dicts, recursively serialize
            if isinstance(data, list):
                return [self._serialize_data(item) for item in data]
            elif isinstance(data, dict):
                return {key: self._serialize_data(value) for key, value in data.items()}
            else:
                # For complex objects, use the default serializer
                return json.loads(json.dumps(data, default=default_serializer))
                
        except Exception as e:
            print(f"Serialization error: {e}")
            return str(data)