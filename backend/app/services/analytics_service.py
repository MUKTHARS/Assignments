from app.database.factory import DatabaseFactory
from app.services.llm_service import LLMService
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from typing import Dict, Any, List
import json
import traceback

class AnalyticsService:
    def __init__(self):
        self.llm_service = LLMService()
        self.db = None
        self.current_db_type = "mongodb"

    async def initialize_database(self, database_type: str = None):
        """Initialize database connection with optional type override"""
        # Use MongoDB as default if no type specified
        if database_type:
            self.current_db_type = database_type
        else:
            self.current_db_type = "mongodb"
        
        print(f"🔄 Initializing database connection... Type: {self.current_db_type}")
        
        # Close existing connection if any
        if self.db:
            try:
                await self.db.disconnect()
                print("✅ Closed previous database connection")
            except Exception as e:
                print(f"⚠️ Error closing previous connection: {e}")
        
        try:
            # Create new database connection
            self.db = await DatabaseFactory.create_database(self.current_db_type)
            print("🔄 Creating sample data...")
            await DatabaseFactory.initialize_sample_data(self.db)
            
            print("✅ Database initialization completed")
            
        except Exception as e:
            print(f"❌ Database initialization failed: {str(e)}")
            print(f"🔍 Full traceback: {traceback.format_exc()}")
            # Reset to MongoDB as fallback
            print("🔄 Falling back to MongoDB...")
            self.current_db_type = "mongodb"
            # Update environment to use MongoDB URL
            from app.config import settings
            if settings.MONGODB_URL:
                self.db = await DatabaseFactory.create_database("mongodb")
                await DatabaseFactory.initialize_sample_data(self.db)
            else:
                raise Exception("MongoDB fallback also failed - no MongoDB URL configured")


    async def reinitialize_database(self, database_type: str = None):
        """Reinitialize database with new type"""
        await self.initialize_database(database_type)

    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process natural language query and return results"""
        
        if not self.db:
            await self.initialize_database()
        
        # Manual handling for default dashboard questions
        manual_result = await self._handle_manual_queries(query)
        if manual_result:
            return manual_result
        
        # Parse the natural language query using LLM for user requests
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
            
    async def _handle_manual_queries(self, query: str) -> Optional[Dict[str, Any]]:
        """Handle manual queries for default dashboard questions with proper date ranges"""
        query_lower = query.lower().strip()
        
        # Map default questions to specific intents with proper date calculations
        from datetime import date, timedelta
        
        # Use your data timeframe reference date
        reference_date = date(2025, 10, 15)
        
        manual_mappings = {
            "what is the total revenue for this week?": ("get_weekly_revenue", {
                "start_date": (reference_date - timedelta(days=reference_date.weekday())).isoformat(),
                "end_date": (reference_date + timedelta(days=6 - reference_date.weekday())).isoformat()
            }),
            "show me today's sales": ("get_daily_sales", {
                "target_date": reference_date.isoformat()
            }),
            "what are the top 5 products by revenue?": ("get_top_products", {"limit": 5}),
            "show me orders for customer 1": ("get_customer_orders", {"customer_id": "1"})
        }
        
        if query_lower in manual_mappings:
            intent, params = manual_mappings[query_lower]
            print(f"🔧 Using manual mapping for: {query}")
            
            try:
                data = await self._execute_analytics_function(intent, params)
                serialized_data = self._serialize_data(data)
                natural_response = await self.llm_service.generate_natural_response(serialized_data, query)
                
                return {
                    "success": True,
                    "intent": intent,
                    "parameters": params,
                    "data": serialized_data,
                    "response": natural_response
                }
            except Exception as e:
                print(f"Manual query error: {e}")
        
        return None

    async def _execute_analytics_function(self, intent: str, parameters: Dict[str, Any]) -> Any:
        """Execute the appropriate analytics function"""
        print(f"🔍 Executing intent: {intent} with parameters: {parameters}")
        # Handle date parameters
        processed_params = self._process_parameters(parameters)
        print(f"🔍 Processed parameters: {processed_params}")
        
        # if intent == "execute_dynamic_query":
        #     # Extract dynamic query parameters
        #     return await self.db.execute_dynamic_query(
        #         table=processed_params.get("table", "customers"),
        #         fields=processed_params.get("fields", ["*"]),
        #         filters=processed_params.get("filters", {}),
        #         sort_by=processed_params.get("sort_by"),
        #         sort_order=processed_params.get("sort_order", "desc"),
        #         limit=processed_params.get("limit", 50),
        #         query_type=processed_params.get("query_type", "general"),
        #         operation=processed_params.get("operation", "get")
        #     )

        if intent == "get_monthly_revenue":
            return await self.db.get_monthly_revenue(
                processed_params.get("months", 1),
                processed_params.get("last_month", False)
            )
                
        elif intent == "get_weekly_revenue":
            return await self.db.get_weekly_revenue(
                processed_params["start_date"],
                processed_params["end_date"]
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
        
        # Handle date calculations - use your database timeframe (July-Oct 2025)
        reference_date = date(2025, 9, 15)  # Middle of your data range
        
        # Handle specific date strings first
        for key in ['start_date', 'end_date', 'target_date']:
            if key in processed and isinstance(processed[key], str):
                if processed[key] == 'today':
                    processed[key] = reference_date
                elif processed[key] == 'yesterday':
                    processed[key] = reference_date - timedelta(days=1)
                elif processed[key] == 'this_week':
                    # Calculate this week relative to reference date
                    start_of_week = reference_date - timedelta(days=reference_date.weekday())
                    processed[key] = start_of_week
                    # If both start_date and end_date are 'this_week', calculate end_date too
                    if key == 'start_date' and processed.get('end_date') == 'this_week':
                        processed['end_date'] = start_of_week + timedelta(days=6)
                elif processed[key] == 'last_week':
                    start_of_last_week = reference_date - timedelta(days=reference_date.weekday() + 7)
                    processed[key] = start_of_last_week
                    if key == 'start_date' and processed.get('end_date') == 'last_week':
                        processed['end_date'] = start_of_last_week + timedelta(days=6)
                else:
                    # Try to parse as ISO date string
                    try:
                        processed[key] = datetime.strptime(processed[key], '%Y-%m-%d').date()
                    except (ValueError, TypeError):
                        # If parsing fails, use reference date
                        processed[key] = reference_date
        
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



            