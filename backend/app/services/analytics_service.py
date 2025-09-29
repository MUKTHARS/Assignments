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
            self.db = await DatabaseFactory.create_database()
            await DatabaseFactory.initialize_sample_data(self.db)

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
            
            # Generate natural language response
            natural_response = await self.llm_service.generate_natural_response(
                data, query
            )
            
            return {
                "success": True,
                "intent": parsed_intent["intent"],
                "parameters": parsed_intent["parameters"],
                "data": data,
                "response": natural_response
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": None,
                "response": f"Sorry, I encountered an error while processing your query: {str(e)}"
            }

    async def _execute_analytics_function(self, intent: str, parameters: Dict[str, Any]) -> Any:
        """Execute the appropriate analytics function"""
        
        # Handle date parameters
        processed_params = self._process_parameters(parameters)
        
        if intent == "get_weekly_revenue":
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
        
        else:
            raise ValueError(f"Unknown intent: {intent}")

    def _process_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate parameters"""
        processed = parameters.copy()
        
        # Handle date calculations
        if "start_date" in parameters and parameters["start_date"] == "this_week":
            today = date.today()
            start_of_week = today - timedelta(days=today.weekday())
            processed["start_date"] = start_of_week
            processed["end_date"] = start_of_week + timedelta(days=6)
        
        elif "start_date" in parameters and parameters["start_date"] == "last_week":
            today = date.today()
            start_of_last_week = today - timedelta(days=today.weekday() + 7)
            processed["start_date"] = start_of_last_week
            processed["end_date"] = start_of_last_week + timedelta(days=6)
        
        elif "target_date" in parameters and parameters["target_date"] == "today":
            processed["target_date"] = date.today()
        
        elif "target_date" in parameters and parameters["target_date"] == "yesterday":
            processed["target_date"] = date.today() - timedelta(days=1)
        
        return processed