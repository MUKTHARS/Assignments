import google.generativeai as genai
from app.config import settings
from typing import Dict, Any, List
import json
import re

class LLMService:
    def __init__(self):
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            # List available models to see what's actually available
            available_models = genai.list_models()
            print(f"Available Gemini models: {[model.name for model in available_models]}")
            
            # Try to use the first available model or gemini-pro
            model_name = 'gemini-pro'
            for model in available_models:
                if 'gemini-pro' in model.name:
                    model_name = model.name
                    break
                    
            self.model = genai.GenerativeModel(model_name)
            print(f"✅ Using Gemini model: {model_name}")
            
        except Exception as e:
            print(f"❌ Gemini model initialization error: {e}")
            print("🔄 Using fallback rule-based parsing")
            self.model = None
        
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
        
        # If Gemini is not available, use simple rule-based parsing
        if not self.model:
            return self._fallback_parse(query)
            
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
            return self._fallback_parse(query)

    def _fallback_parse(self, query: str) -> Dict[str, Any]:
        """Fallback rule-based parsing when Gemini fails"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['revenue', 'income', 'sales']) and 'week' in query_lower:
            return {
                "intent": "get_weekly_revenue",
                "parameters": {"start_date": "this_week", "end_date": "this_week"},
                "confidence": 0.8
            }
        elif 'today' in query_lower and 'sales' in query_lower:
            return {
                "intent": "get_daily_sales", 
                "parameters": {"target_date": "today"},
                "confidence": 0.8
            }
        elif 'top' in query_lower and 'product' in query_lower:
            limit = 5 if '5' in query else 10
            return {
                "intent": "get_top_products",
                "parameters": {"limit": limit},
                "confidence": 0.8
            }
        elif 'category' in query_lower and 'sales' in query_lower:
            return {
                "intent": "get_sales_by_category",
                "parameters": {"start_date": "last_month", "end_date": "today"},
                "confidence": 0.7
            }
        elif 'trend' in query_lower or 'monthly' in query_lower:
            months = 6
            if '3' in query:
                months = 3
            elif '12' in query:
                months = 12
            return {
                "intent": "get_monthly_revenue_trend", 
                "parameters": {"months": months},
                "confidence": 0.7
            }
        elif 'customer' in query_lower and 'order' in query_lower:
            # Extract customer ID if mentioned
            import re
            customer_match = re.search(r'customer\s+(\d+)', query_lower)
            customer_id = customer_match.group(1) if customer_match else "1"
            return {
                "intent": "get_customer_orders",
                "parameters": {"customer_id": customer_id},
                "confidence": 0.7
            }
        else:
            return {"intent": "unknown", "parameters": {}, "confidence": 0.0}
        """Fallback rule-based parsing when Gemini fails"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['revenue', 'income', 'sales']) and 'week' in query_lower:
            return {
                "intent": "get_weekly_revenue",
                "parameters": {"start_date": "this_week", "end_date": "this_week"},
                "confidence": 0.8
            }
        elif 'today' in query_lower and 'sales' in query_lower:
            return {
                "intent": "get_daily_sales", 
                "parameters": {"target_date": "today"},
                "confidence": 0.8
            }
        elif 'top' in query_lower and 'product' in query_lower:
            limit = 5 if '5' in query else 10
            return {
                "intent": "get_top_products",
                "parameters": {"limit": limit},
                "confidence": 0.8
            }
        elif 'category' in query_lower and 'sales' in query_lower:
            return {
                "intent": "get_sales_by_category",
                "parameters": {"start_date": "last_month", "end_date": "today"},
                "confidence": 0.7
            }
        elif 'trend' in query_lower or 'monthly' in query_lower:
            return {
                "intent": "get_monthly_revenue_trend", 
                "parameters": {"months": 6},
                "confidence": 0.7
            }
        elif 'customer' in query_lower and 'order' in query_lower:
            # Extract customer ID if mentioned
            import re
            customer_match = re.search(r'customer\s+(\d+)', query_lower)
            customer_id = customer_match.group(1) if customer_match else "1"
            return {
                "intent": "get_customer_orders",
                "parameters": {"customer_id": customer_id},
                "confidence": 0.7
            }
        else:
            return {"intent": "unknown", "parameters": {}, "confidence": 0.0}

    async def generate_natural_response(self, data: Any, original_query: str) -> str:
        """Generate natural language response from data"""
        
        if not self.model:
            return self._fallback_response(data, original_query)
            
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
            return self._fallback_response(data, original_query)

    def _fallback_response(self, data: Any, original_query: str) -> str:
        """Fallback response generation"""
        if not data:
            return f"I couldn't find any data for your query: '{original_query}'"
        
        if isinstance(data, (int, float)):
            return f"The result for '{original_query}' is: ${data:,.2f}"
        
        if isinstance(data, list) and len(data) > 0:
            return f"Found {len(data)} records for your query: '{original_query}'"
            
        return f"Here's the data for '{original_query}': {str(data)}"