import google.generativeai as genai
from app.config import settings
from typing import Dict, Any, List
import json
import re

class LLMService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
        
        # Define available analytics functions
        self.available_functions = {
            "get_weekly_revenue": {
                "description": "Get total revenue for a specific week",
                "parameters": ["start_date", "end_date"]
            },
            "get_daily_sales": {
                "description": "Get sales data for a specific day",
                "parameters": ["target_date"]
            },
            "get_top_products": {
                "description": "Get top selling products by revenue",
                "parameters": ["limit"]
            },
            "get_customer_orders": {
                "description": "Get order history for a specific customer",
                "parameters": ["customer_id"]
            },
            "get_sales_by_category": {
                "description": "Get sales breakdown by product category",
                "parameters": ["start_date", "end_date"]
            },
            "get_monthly_revenue_trend": {
                "description": "Get monthly revenue trend for the past months",
                "parameters": ["months"]
            }
        }

    def parse_natural_language(self, query: str) -> Dict[str, Any]:
        """Parse natural language query and extract intent and parameters"""
        
        prompt = f"""
        Analyze the following user query about sales analytics and extract the intent and parameters.
        
        Available functions:
        {json.dumps(self.available_functions, indent=2)}
        
        User Query: "{query}"
        
        Respond in JSON format with:
        {{
            "intent": "function_name",
            "parameters": {{
                "param1": "value1",
                "param2": "value2"
            }},
            "confidence": 0.95
        }}
        
        If no clear intent is found, set intent to "unknown".
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result
            else:
                return {"intent": "unknown", "parameters": {}, "confidence": 0.0}
                
        except Exception as e:
            print(f"Error parsing natural language: {e}")
            return {"intent": "unknown", "parameters": {}, "confidence": 0.0}

    async def generate_natural_response(self, data: Any, original_query: str) -> str:
        """Generate natural language response from data"""
        
        prompt = f"""
        The user asked: "{original_query}"
        
        Here is the data retrieved from the database:
        {json.dumps(data, indent=2) if data else "No data found"}
        
        Please provide a clear, concise natural language response summarizing this data.
        Focus on the key insights and present the information in an easy-to-understand way.
        If there are numbers, format them properly (e.g., currency, percentages).
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error generating natural response: {e}")
            return f"Here's the data for your query '{original_query}': {json.dumps(data, indent=2) if data else 'No data found'}"