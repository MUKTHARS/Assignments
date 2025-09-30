import google.generativeai as genai
from app.config import settings
from typing import Dict, Any, List
import json
import re
import random
from datetime import datetime, date, timedelta

class LLMService:
    def __init__(self):
        self.model = None
        self.is_gemini_available = False
        
        try:
            # Configure with the correct API key
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            print("🔧 Initializing Gemini API...")
            
            # First, let's list available models to see what's accessible
            try:
                available_models = genai.list_models()
                model_names = [model.name for model in available_models]
                print(f"📋 Available models: {model_names}")
                
                # Try to find the correct model names from available ones
                working_models = []
                for model in available_models:
                    if 'generateContent' in model.supported_generation_methods:
                        working_models.append(model.name)
                        print(f"✅ Found working model: {model.name}")
                
                if working_models:
                    # Use the first available model that supports generateContent
                    model_name = working_models[0]
                    self.model = genai.GenerativeModel(model_name)
                    
                    # Test the model with a simple prompt
                    try:
                        test_response = self.model.generate_content("Hello, respond with 'OK' if working.")
                        if test_response.text:
                            self.is_gemini_available = True
                            print(f"🎉 Gemini model initialized successfully: {model_name}")
                        else:
                            print("❌ Model test failed - no response")
                    except Exception as test_error:
                        print(f"❌ Model test failed: {test_error}")
                
            except Exception as list_error:
                print(f"❌ Could not list models: {list_error}")
                # Fallback to common model names
                self._try_fallback_models()
                
        except Exception as e:
            print(f"❌ Gemini configuration failed: {e}")
            print("🔄 Using enhanced fallback parsing")
        
        # Enhanced query patterns for better matching
        self.query_patterns = self._initialize_query_patterns()

    def _try_fallback_models(self):
        """Try common model names as fallback"""
        fallback_models = [
            'gemini-flash-latest',
            'gemini-pro-latest', 
            'gemini-1.0-pro',
            'models/gemini-1.0-pro',
            'gemini-pro', 
            'models/gemini-pro',
            'gemini-1.0-pro-001',
            'models/gemini-1.0-pro-001'
        ]
        
        for model_name in fallback_models:
            try:
                print(f"🔄 Trying fallback model: {model_name}")
                self.model = genai.GenerativeModel(model_name)
                test_response = self.model.generate_content("Test")
                if test_response.text:
                    self.is_gemini_available = True
                    print(f"✅ Fallback model working: {model_name}")
                    break
            except Exception as e:
                print(f"❌ Fallback model failed {model_name}: {e}")
                continue

    def _initialize_query_patterns(self):
        """Initialize comprehensive query patterns with better user query handling"""
        return {
            # Revenue queries with date ranges
            r'.*this.week.*revenue.*': ("get_weekly_revenue", {"start_date": "this_week", "end_date": "this_week"}),
            r'.*last.week.*revenue.*': ("get_weekly_revenue", {"start_date": "last_week", "end_date": "last_week"}),
            r'.*this.month.*revenue.*': ("get_monthly_revenue", {"months": 1}),
            r'.*last.month.*revenue.*': ("get_monthly_revenue", {"months": 1, "last_month": True}),
            r'.*current.month.*revenue.*': ("get_monthly_revenue", {"months": 1}),
            r'.*all.time.*revenue.*': ("get_all_time_revenue", {}),
            r'.*total.*revenue.*': ("get_all_time_revenue", {}),
            r'.*overall.*revenue.*': ("get_all_time_revenue", {}),
            r'.*revenue.*this.week.*': ("get_weekly_revenue", {"start_date": "this_week", "end_date": "this_week"}),
            r'.*revenue.*last.week.*': ("get_weekly_revenue", {"start_date": "last_week", "end_date": "last_week"}),
            
            # User-specific revenue queries
            r'.*how.much.*revenue.*': ("get_all_time_revenue", {}),
            r'.*what.*total.*revenue.*': ("get_all_time_revenue", {}),
            r'.*what.*revenue.*': ("get_all_time_revenue", {}),
            
            # Product performance queries
            r'.*top.*(\d+).*product.*revenue.*': ("get_top_products", {"limit": None}),
            r'.*top.*(\d+).*product.*': ("get_top_products", {"limit": None}),
            r'.*best.*selling.*product.*': ("get_top_products", {"limit": 5}),
            r'.*most.popular.*product.*': ("get_top_products", {"limit": 5}),
            r'.*top.*product.*': ("get_top_products", {"limit": 10}),
            r'.*least.*sold.*product.*': ("get_least_sold_products", {"limit": 5}),
            r'.*worst.*selling.*product.*': ("get_least_sold_products", {"limit": 5}),
            
            # Customer queries - IMPROVED PATTERNS
            r'.*all.*customer.*': ("get_all_customers", {}),
            r'.*list.*customer.*': ("get_all_customers", {}),
            r'.*show.*customer.*': ("get_all_customers", {}),
            r'.*how.many.*customer.*': ("get_all_customers", {}),
            r'.*number.*customer.*': ("get_all_customers", {}),
            r'.*count.*customer.*': ("get_all_customers", {}),
            r'.*total.*customer.*': ("get_all_customers", {}),
            r'.*repeat.*customer.*': ("get_repeat_customers", {}),
            r'.*inactive.*customer.*': ("get_inactive_customers", {"days_threshold": 30}),
            
            # Order queries with dates - IMPROVED PATTERNS
            r'.*today.*sale.*': ("get_daily_sales", {"target_date": "today"}),
            r'.*today.*order.*': ("get_daily_sales", {"target_date": "today"}),
            r'.*sales.*today.*': ("get_daily_sales", {"target_date": "today"}),
            r'.*do.we.have.*sale.*today.*': ("get_daily_sales", {"target_date": "today"}),
            r'.*any.*sale.*today.*': ("get_daily_sales", {"target_date": "today"}),
            r'.*yesterday.*sale.*': ("get_daily_sales", {"target_date": "yesterday"}),
            r'.*yesterday.*order.*': ("get_daily_sales", {"target_date": "yesterday"}),
            r'.*recent.*order.*': ("get_recent_orders", {"limit": 10}),
            r'.*latest.*order.*': ("get_recent_orders", {"limit": 10}),
            
            # Customer specific queries
            r'.*order.*for.customer.*(\d+).*': ("get_customer_orders", {"customer_id": None}),
            r'.*customer.*(\d+).*order.*': ("get_customer_orders", {"customer_id": None}),
            r'.*show.*order.*customer.*(\d+).*': ("get_customer_orders", {"customer_id": None}),
            
            # Category queries
            r'.*sale.*by.*categor.*': ("get_sales_by_category", {"start_date": "last_month", "end_date": "today"}),
            r'.*category.*performance.*': ("get_sales_by_category", {"start_date": "last_month", "end_date": "today"}),
            r'.*revenue.*by.*categor.*': ("get_sales_by_category", {"start_date": "last_month", "end_date": "today"}),
            
            # Trend queries
            r'.*monthly.*trend.*': ("get_monthly_revenue_trend", {"months": 6}),
            r'.*revenue.*trend.*': ("get_monthly_revenue_trend", {"months": 6}),
            r'.*sales.*trend.*': ("get_monthly_revenue_trend", {"months": 6}),
            r'.*last.(\d+).month.*trend.*': ("get_monthly_revenue_trend", {"months": None}),
        }

    def _preprocess_query(self, query: str) -> str:
        """Preprocess and normalize user queries for better matching"""
        query_lower = query.lower().strip()
        
        # Common user query variations
        replacements = {
            r'do we have any': 'show',
            r'how many': 'count',
            r'what is': 'show',
            r'can you show': 'show',
            r'can you tell': 'show',
            r'i want to see': 'show',
            r'give me': 'show',
            r'display': 'show',
            r'list': 'show'
        }
        
        processed_query = query_lower
        for pattern, replacement in replacements.items():
            processed_query = re.sub(pattern, replacement, processed_query)
        
        # Remove common filler words
        filler_words = ['please', 'could you', 'would you', 'can you', 'the', 'a', 'an']
        for word in filler_words:
            processed_query = re.sub(r'\b' + word + r'\b', '', processed_query)
        
        # Normalize spaces
        processed_query = re.sub(r'\s+', ' ', processed_query).strip()
        
        if processed_query != query_lower:
            print(f"🔧 Query normalized: '{query_lower}' -> '{processed_query}'")
        
        return processed_query


    def parse_natural_language(self, query: str) -> Dict[str, Any]:
        """Parse natural language query with proper Gemini API usage"""
        print(f"🔍 Processing query: '{query}'")
        
        # Preprocess the query first
        processed_query = self._preprocess_query(query)
        query_lower = processed_query.lower().strip()
        
        # Always try Gemini first if available
        if self.is_gemini_available:
            try:
                gemini_result = self._try_gemini_parsing(query)
                if gemini_result and gemini_result.get("confidence", 0) > 0.6:
                    print(f"✅ Gemini parsing successful: {gemini_result['intent']}")
                    return gemini_result
                else:
                    print("⚠️ Gemini parsing failed or low confidence, using fallback")
            except Exception as e:
                print(f"❌ Gemini parsing failed: {e}")
        
        # Enhanced pattern matching with parameter extraction
        return self._enhanced_pattern_parsing(query_lower, query)

    def _try_gemini_parsing(self, query: str) -> Dict[str, Any]:
        """Try to parse using Gemini API with comprehensive prompts"""
        try:
            prompt = f"""
            Analyze this shopping analytics query and map it to the most specific function.
            
            Available functions and their purposes:
            - get_weekly_revenue(start_date, end_date): Calculate revenue for a specific week
            - get_monthly_revenue_trend(months): Get monthly revenue trend for past N months  
            - get_all_time_revenue(): Get total revenue across all time
            - get_daily_sales(target_date): Get sales for a specific day
            - get_top_products(limit): Get best selling products by revenue
            - get_least_sold_products(limit): Get worst selling products by quantity
            - get_all_customers(): List all customers
            - get_all_products(): List all products
            - get_customer_orders(customer_id): Get orders for specific customer
            - get_sales_by_category(start_date, end_date): Get sales breakdown by category
            - get_repeat_customers(): Get customers with multiple orders
            - get_inactive_customers(days_threshold): Get inactive customers
            - get_costliest_product(): Get most expensive product
            - get_cheapest_product(): Get least expensive product
            - get_product_price_range(): Get price statistics
            - get_average_product_price(): Get average product price
            - get_recent_orders(limit): Get recent orders

            IMPORTANT: For date-related queries:
            - "this week" means current week (Monday to Sunday)
            - "last week" means previous week
            - "this month" means current month
            - "last month" means previous month
            - "today" means current date
            - "yesterday" means previous date

            Query: "{query}"

            Extract parameters like:
            - customer_id: extract numbers after "customer" (e.g., "customer 1" -> "1")
            - limit: extract numbers after "top" or "first" (e.g., "top 5" -> 5)
            - dates: map to "this_week", "last_week", "today", "yesterday", etc.
            - months: extract numbers for trend analysis

            Respond with ONLY valid JSON in this exact format:
            {{
                "intent": "function_name",
                "parameters": {{"param1": value1, "param2": value2}},
                "confidence": 0.95
            }}

            If unsure, use get_all_time_revenue as default.
            """
            
            print("🤖 Sending request to Gemini...")
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            print(f"🔍 Gemini raw response: {response_text}")
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                # Validate the result
                if self._validate_gemini_result(result, query):
                    return result
                else:
                    print("⚠️ Gemini result validation failed")
                    
        except Exception as e:
            print(f"Gemini API error: {e}")
            
        return None

    def _validate_gemini_result(self, result: Dict[str, Any], query: str) -> bool:
        """Validate Gemini parsing result"""
        if not isinstance(result, dict):
            return False
            
        required_keys = ['intent', 'parameters', 'confidence']
        if not all(key in result for key in required_keys):
            return False
            
        if not isinstance(result['parameters'], dict):
            return False
            
        # Validate intent exists in available functions
        valid_intents = [
            'get_weekly_revenue', 'get_monthly_revenue_trend', 'get_all_time_revenue',
            'get_daily_sales', 'get_top_products', 'get_least_sold_products',
            'get_all_customers', 'get_all_products', 'get_customer_orders',
            'get_sales_by_category', 'get_repeat_customers', 'get_inactive_customers',
            'get_costliest_product', 'get_cheapest_product', 'get_product_price_range',
            'get_average_product_price', 'get_recent_orders', 'get_monthly_revenue'
        ]
        
        if result['intent'] not in valid_intents:
            print(f"⚠️ Invalid intent from Gemini: {result['intent']}")
            return False
            
        # Extract and validate parameters from query
        result['parameters'] = self._extract_parameters_from_query(query, result['intent'], result['parameters'])
        
        return True

    def _extract_parameters_from_query(self, query: str, intent: str, current_params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and validate parameters from query text"""
        query_lower = query.lower()
        params = current_params.copy()
        
        # Extract customer ID
        if intent == "get_customer_orders":
            customer_match = re.search(r'customer\s+(\d+)', query_lower)
            if customer_match and not params.get('customer_id'):
                params['customer_id'] = customer_match.group(1)
        
        # Extract limit
        if intent in ["get_top_products", "get_least_sold_products", "get_recent_orders"]:
            limit_match = re.search(r'top\s+(\d+)', query_lower) or re.search(r'first\s+(\d+)', query_lower) or re.search(r'(\d+).*product', query_lower)
            if limit_match and not params.get('limit'):
                params['limit'] = int(limit_match.group(1))
        
        # Extract months for trends
        if intent == "get_monthly_revenue_trend":
            months_match = re.search(r'last\s+(\d+)\s+month', query_lower) or re.search(r'past\s+(\d+)\s+month', query_lower) or re.search(r'(\d+).*month.*trend', query_lower)
            if months_match and not params.get('months'):
                params['months'] = int(months_match.group(1))
        
        # Handle date parameters
        params = self._process_date_parameters(query_lower, intent, params)
        
        return params

    def _process_date_parameters(self, query_lower: str, intent: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Process and set date parameters based on query text"""
        # Handle weekly revenue
        if intent == "get_weekly_revenue":
            if "this week" in query_lower and not params.get('start_date'):
                params['start_date'] = "this_week"
                params['end_date'] = "this_week"
            elif "last week" in query_lower and not params.get('start_date'):
                params['start_date'] = "last_week"
                params['end_date'] = "last_week"
        
        # Handle daily sales
        elif intent == "get_daily_sales":
            if "today" in query_lower and not params.get('target_date'):
                params['target_date'] = "today"
            elif "yesterday" in query_lower and not params.get('target_date'):
                params['target_date'] = "yesterday"
        
        # Handle monthly trends
        elif intent == "get_monthly_revenue_trend":
            if "this month" in query_lower and not params.get('months'):
                params['months'] = 1
            elif "last month" in query_lower and not params.get('months'):
                params['months'] = 1
                params['last_month'] = True
        
        return params

    def _enhanced_pattern_parsing(self, query_lower: str, original_query: str) -> Dict[str, Any]:
        """Enhanced pattern-based parsing with better parameter extraction"""
        
        # Extract specific parameters
        customer_id = self._extract_parameter(r'customer\s+(\d+)', query_lower)
        months = self._extract_parameter(r'last\s+(\d+)\s+month', query_lower) or self._extract_parameter(r'past\s+(\d+)\s+month', query_lower)
        limit = self._extract_parameter(r'top\s+(\d+)', query_lower) or self._extract_parameter(r'(\d+).*product', query_lower)
        
        # Try pattern matching for other queries
        for pattern, (intent, base_params) in self.query_patterns.items():
            if re.search(pattern, query_lower, re.IGNORECASE):
                print(f"✅ Pattern matched: {intent}")
                
                # Update parameters with extracted values
                final_params = base_params.copy()
                
                if customer_id and intent == "get_customer_orders":
                    final_params["customer_id"] = customer_id
                
                if months and intent == "get_monthly_revenue_trend":
                    final_params["months"] = int(months)
                
                if limit and intent in ["get_top_products", "get_least_sold_products"]:
                    final_params["limit"] = int(limit)
                
                # Handle specific date patterns
                if "this week" in query_lower and intent == "get_weekly_revenue":
                    final_params["start_date"] = "this_week"
                    final_params["end_date"] = "this_week"
                elif "last week" in query_lower and intent == "get_weekly_revenue":
                    final_params["start_date"] = "last_week"
                    final_params["end_date"] = "last_week"
                elif "this month" in query_lower and intent == "get_monthly_revenue_trend":
                    final_params["months"] = 1
                
                return {
                    "intent": intent,
                    "parameters": final_params,
                    "confidence": 0.85
                }
        
        # Enhanced keyword-based fallback
        return self._enhanced_keyword_fallback(query_lower)

    def _extract_parameter(self, pattern: str, query: str) -> str:
        """Extract parameter using regex pattern"""
        match = re.search(pattern, query)
        return match.group(1) if match else None

    def _enhanced_keyword_fallback(self, query_lower: str) -> Dict[str, Any]:
        """Enhanced keyword-based fallback parsing with better user query handling"""
        keywords = {
            'revenue': ['revenue', 'sales', 'income', 'money', 'earning', 'how much', 'what is'],
            'customer': ['customer', 'client', 'user', 'how many', 'number of', 'count'],
            'product': ['product', 'item', 'merchandise'],
            'order': ['order', 'sale', 'purchase', 'transaction'],
            'week': ['week', 'weekly'],
            'month': ['month', 'monthly'],
            'today': ['today', 'daily', 'current day', 'do we have', 'any sales'],
            'top': ['top', 'best', 'most', 'highest'],
            'category': ['category', 'type', 'group']
        }
        
        # Count keyword matches with weights
        scores = {category: 0 for category in keywords}
        for category, words in keywords.items():
            for word in words:
                if word in query_lower:
                    scores[category] += 1
        
        # Enhanced intent determination with better logic
        if scores['today'] > 0 and (scores['order'] > 0 or scores['revenue'] > 0):
            return {"intent": "get_daily_sales", "parameters": {"target_date": "today"}, "confidence": 0.8}
        elif scores['customer'] > 1 and any(word in query_lower for word in ['how many', 'number', 'count', 'total']):
            return {"intent": "get_all_customers", "parameters": {}, "confidence": 0.9}
        elif scores['revenue'] > 0 and scores['week'] > 0:
            return {"intent": "get_weekly_revenue", "parameters": {"start_date": "this_week", "end_date": "this_week"}, "confidence": 0.8}
        elif scores['revenue'] > 0 and scores['month'] > 0:
            return {"intent": "get_monthly_revenue", "parameters": {"months": 1}, "confidence": 0.8}
        elif scores['revenue'] > 0:
            return {"intent": "get_all_time_revenue", "parameters": {}, "confidence": 0.8}
        elif scores['customer'] > 0 and scores['order'] > 0:
            return {"intent": "get_customer_orders", "parameters": {"customer_id": "1"}, "confidence": 0.7}
        elif scores['customer'] > 0:
            return {"intent": "get_all_customers", "parameters": {}, "confidence": 0.8}
        elif scores['product'] > 0 and scores['top'] > 0:
            return {"intent": "get_top_products", "parameters": {"limit": 5}, "confidence": 0.8}
        elif scores['product'] > 0:
            return {"intent": "get_all_products", "parameters": {}, "confidence": 0.7}
        elif scores['today'] > 0:
            return {"intent": "get_daily_sales", "parameters": {"target_date": "today"}, "confidence": 0.8}
        elif scores['category'] > 0:
            return {"intent": "get_sales_by_category", "parameters": {"start_date": "last_month", "end_date": "today"}, "confidence": 0.7}
        
        # Default safe fallback - try to be more specific
        if "today" in query_lower:
            return {"intent": "get_daily_sales", "parameters": {"target_date": "today"}, "confidence": 0.6}
        elif "customer" in query_lower:
            return {"intent": "get_all_customers", "parameters": {}, "confidence": 0.6}
        elif "product" in query_lower:
            return {"intent": "get_all_products", "parameters": {}, "confidence": 0.6}
        
        return {"intent": "get_all_time_revenue", "parameters": {}, "confidence": 0.5}


    async def generate_natural_response(self, data: Any, original_query: str) -> str:
        """Generate natural language response using Gemini when available"""
        # Use Gemini if available for better responses
        if self.is_gemini_available:
            try:
                prompt = f"""
                The user asked: "{original_query}"
                
                Data from database: {json.dumps(data, indent=2) if data else "No data found"}
                
                Provide a clear, concise, and helpful response summarizing this data in natural language.
                Focus on directly answering the specific question asked.
                If there's no data, explain that politely.
                Use appropriate formatting for numbers (commas for thousands, currency symbols).
                Keep the response conversational but professional.
                Be specific about what the data shows.
                """
                
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                print(f"Gemini response generation failed: {e}")
        
        # Enhanced fallback response generation
        return self._enhanced_fallback_response(data, original_query)

    def _enhanced_fallback_response(self, data: Any, query: str) -> str:
        """Enhanced fallback response generation"""
        if data is None:
            return f"I couldn't find any data for your query: '{query}'"
        
        query_lower = query.lower()
        
        # Handle different data types and structures
        if isinstance(data, list):
            count = len(data)
            if count == 0:
                return f"No results found for: {query}"
            
            # Provide meaningful summary based on data structure
            if count > 0 and isinstance(data[0], dict):
                # Product data
                if 'name' in data[0] and 'price' in data[0]:
                    if count == 1:
                        item = data[0]
                        return f"The {item.get('name', 'product')} is priced at ${item.get('price', 0):.2f}"
                    else:
                        sample = ", ".join([f"{item.get('name', 'Unknown')} (${item.get('price', 0):.2f})" for item in data[:3]])
                        return f"Found {count} products. Examples: {sample}" + (f" and {count-3} more." if count > 3 else "")
                
                # Customer data
                elif 'name' in data[0] and 'email' in data[0]:
                    names = [item.get('name', 'Unknown') for item in data[:3]]
                    if count > 3:
                        return f"Found {count} customers. Including: {', '.join(names)}... and {count-3} more"
                    else:
                        return f"Found {count} customers: {', '.join(names)}"
                
                # Order data with revenue
                elif 'total_amount' in data[0]:
                    total = sum(item.get('total_amount', 0) for item in data)
                    if "customer" in query_lower:
                        return f"Found {count} orders for this customer totaling ${total:,.2f}"
                    else:
                        return f"Found {count} orders totaling ${total:,.2f}"
                
                # Category sales data
                elif 'category' in data[0] and 'total_revenue' in data[0]:
                    top_category = data[0] if data else {}
                    return f"Sales by category: {top_category.get('category', 'Unknown')} had the highest revenue at ${top_category.get('total_revenue', 0):,.2f}"
                
                # Top products data
                elif 'name' in data[0] and 'total_revenue' in data[0]:
                    if count == 1:
                        product = data[0]
                        return f"Top product: {product.get('name', 'Unknown')} with ${product.get('total_revenue', 0):,.2f} in revenue"
                    else:
                        top_product = data[0] if data else {}
                        return f"Top {count} products: {top_product.get('name', 'Unknown')} leads with ${top_product.get('total_revenue', 0):,.2f} in revenue"
            
            return f"Found {count} records matching your query."
        
        # Single numeric value (revenue)
        if isinstance(data, (int, float)):
            if any(word in query_lower for word in ['revenue', 'sales', 'amount']):
                period = ""
                if "this week" in query_lower:
                    period = " this week"
                elif "last week" in query_lower:
                    period = " last week" 
                elif "this month" in query_lower:
                    period = " this month"
                elif "last month" in query_lower:
                    period = " last month"
                
                return f"Total revenue{period}: ${data:,.2f}"
            return f"Result: {data}"
        
        # Dictionary response
        if isinstance(data, dict):
            key_info = []
            for key, value in list(data.items())[:4]:
                if isinstance(value, (int, float)):
                    if 'price' in key.lower() or 'revenue' in key.lower() or 'amount' in key.lower():
                        key_info.append(f"{key}: ${value:,.2f}")
                    else:
                        key_info.append(f"{key}: {value:,.0f}" if isinstance(value, (int, float)) and value > 1000 else f"{key}: {value}")
                else:
                    key_info.append(f"{key}: {value}")
            return f"Results: {', '.join(key_info)}"
        
        return f"Here's the data for your query: {str(data)}"