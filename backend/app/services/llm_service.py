import google.generativeai as genai
from app.config import settings
from typing import Dict, Any, List
import json
import re
import random
from datetime import datetime, date

class LLMService:
    def __init__(self):
        self.model = None
        
        try:
            # Use the correct API configuration
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # Try different model configurations
            model_configs = [
                'gemini-1.5-flash',
                'gemini-1.5-pro',
                'gemini-pro',
                'models/gemini-pro'
            ]
            
            for model_name in model_configs:
                try:
                    self.model = genai.GenerativeModel(model_name)
                    print(f"✅ Gemini model initialized: {model_name}")
                    break
                except Exception as e:
                    print(f"❌ Failed with {model_name}: {e}")
                    continue
            
            if not self.model:
                print("🔄 Using enhanced fallback parsing (no Gemini API)")
                
        except Exception as e:
            print(f"❌ Gemini initialization failed: {e}")
            print("🔄 Using enhanced fallback parsing")
        
        # Enhanced query patterns for better matching
        self.query_patterns = self._initialize_query_patterns()

    def _initialize_query_patterns(self):
        """Initialize comprehensive query patterns with better product queries"""
        return {
            # Product price and cost queries
            r'.*costliest.*product.*': ("get_costliest_product", {}),
            r'.*most.expensive.*product.*': ("get_costliest_product", {}),
            r'.*highest.price.*product.*': ("get_costliest_product", {}),
            r'.*cheapest.*product.*': ("get_cheapest_product", {}),
            r'.*lowest.price.*product.*': ("get_cheapest_product", {}),
            r'.*least.expensive.*product.*': ("get_cheapest_product", {}),
            r'.*product.*price.*range.*': ("get_product_price_range", {}),
            r'.*average.*product.*price.*': ("get_average_product_price", {}),
            
            # Product availability and stock queries
            r'.*out.of.stock.*product.*': ("get_out_of_stock_products", {}),
            r'.*available.*product.*': ("get_all_products", {}),
            r'.*list.*all.*product.*': ("get_all_products", {}),
            r'.*show.*all.*product.*': ("get_all_products", {}),
            
            # Revenue queries
            r'.*all.time.*revenue.*': ("get_all_time_revenue", {}),
            r'.*total.*revenue.*': ("get_all_time_revenue", {}),
            r'.*peak.*month.*revenue.*': ("get_peak_revenue_month", {"year": None}),
            r'.*this.week.*revenue.*': ("get_weekly_revenue", {"start_date": "this_week", "end_date": "this_week"}),
            
            # Customer queries  
            r'.*who.*all.*customer.*': ("get_all_customers", {}),
            r'.*list.*customer.*': ("get_all_customers", {}),
            r'.*repeat.*customer.*': ("get_repeat_customers", {}),
            r'.*inactive.*customer.*': ("get_inactive_customers", {"days_threshold": 30}),
            
            # Product performance queries
            r'.*least.*sold.*product.*': ("get_least_sold_products", {"limit": 5}),
            r'.*worst.*selling.*product.*': ("get_least_sold_products", {"limit": 5}),
            r'.*top.*product.*': ("get_top_products", {"limit": 5}),
            r'.*best.*selling.*product.*': ("get_top_products", {"limit": 5}),
            r'.*most.popular.*product.*': ("get_top_products", {"limit": 5}),
            
            # Order queries
            r'.*recent.*order.*': ("get_recent_orders", {"limit": 10}),
            r'.*today.*sale.*': ("get_daily_sales", {"target_date": "today"}),
            r'.*yesterday.*sale.*': ("get_daily_sales", {"target_date": "yesterday"}),
            
            # Category queries
            r'.*sale.*by.*categor.*': ("get_sales_by_category", {"start_date": "last_month", "end_date": "today"}),
            r'.*category.*performance.*': ("get_sales_by_category", {"start_date": "last_month", "end_date": "today"}),
            
            # Trend queries
            r'.*monthly.*trend.*': ("get_monthly_revenue_trend", {"months": 6}),
            r'.*revenue.*trend.*': ("get_monthly_revenue_trend", {"months": 6}),
            
            # Customer specific queries
            r'.*order.*for.customer.*(\d+).*': ("get_customer_orders", {"customer_id": None}),
            r'.*customer.*(\d+).*order.*': ("get_customer_orders", {"customer_id": None}),
        }

    def parse_natural_language(self, query: str) -> Dict[str, Any]:
        """Parse natural language query with enhanced matching"""
        print(f"🔍 Processing query: {query}")
        query_lower = query.lower().strip()
        
        # First, try to use Gemini if available
        if self.model:
            try:
                gemini_result = self._try_gemini_parsing(query)
                if gemini_result and gemini_result.get("confidence", 0) > 0.7:
                    print("✅ Using Gemini parsing")
                    return gemini_result
            except Exception as e:
                print(f"❌ Gemini parsing failed: {e}")
        
        # Enhanced pattern matching with parameter extraction
        return self._enhanced_pattern_parsing(query_lower, query)

    def _try_gemini_parsing(self, query: str) -> Dict[str, Any]:
        """Try to parse using Gemini API with enhanced prompts for dynamic routing"""
        try:
            prompt = f"""
            Analyze this shopping analytics query and map it to the most specific function.
            
            Available functions:
            - get_all_customers (list all customers)
            - get_all_products (list all products) 
            - get_all_time_revenue (total revenue)
            - get_weekly_revenue (weekly sales)
            - get_daily_sales (daily orders)
            - get_top_products (best selling products by revenue)
            - get_least_sold_products (worst selling products by quantity)
            - execute_dynamic_query (for product price queries - use this for costliest/cheapest products)
            - get_customer_orders (orders by specific customer)
            - get_sales_by_category (sales by category)
            - get_monthly_revenue_trend (revenue trends)
            - get_repeat_customers (customers with multiple orders)
            - get_inactive_customers (inactive customers)
            - get_peak_revenue_month (best revenue month)
            
            IMPORTANT: For questions about product prices (costliest, cheapest, most expensive), 
            use execute_dynamic_query with appropriate parameters.
            
            Query: "{query}"
            
            Respond with JSON: {{"intent": "function_name", "parameters": {{}}, "confidence": 0.9}}
            Extract any parameters like customer IDs, dates, or limits.
            """
            
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                # Post-process to handle specific cases with dynamic queries
                query_lower = query.lower()
                if any(term in query_lower for term in ['costliest', 'most expensive', 'highest price']):
                    result["intent"] = "execute_dynamic_query"
                    result["parameters"] = {
                        "table": "products",
                        "fields": ["name", "category", "price"],
                        "filters": {"operation": "costliest"},
                        "query_type": "product_price",
                        "operation": "get_costliest_product",
                        "limit": 1
                    }
                    result["confidence"] = 0.95
                
                return result
                
        except Exception as e:
            print(f"Gemini API error: {e}")
            
        return None
        
    def _enhanced_pattern_parsing(self, query_lower: str, original_query: str) -> Dict[str, Any]:
        """Enhanced pattern-based parsing with parameter extraction"""
        
        # Extract specific parameters first
        customer_id = self._extract_parameter(r'customer\s+(\d+)', query_lower)
        months = self._extract_parameter(r'last\s+(\d+)\s+month', query_lower)
        limit = self._extract_parameter(r'top\s+(\d+)', query_lower) or self._extract_parameter(r'(\d+).*product', query_lower)
        
        # Enhanced product price queries - route through dynamic query
        if any(term in query_lower for term in ['costliest', 'most expensive', 'highest price']):
            return {
                "intent": "execute_dynamic_query",
                "parameters": {
                    "table": "products",
                    "fields": ["name", "category", "price"],
                    "filters": {"operation": "costliest"},
                    "query_type": "product_price",
                    "operation": "get_costliest_product",
                    "limit": 1
                },
                "confidence": 0.95
            }
        
        if any(term in query_lower for term in ['cheapest', 'least expensive', 'lowest price']):
            return {
                "intent": "execute_dynamic_query", 
                "parameters": {
                    "table": "products", 
                    "fields": ["name", "category", "price"],
                    "filters": {"operation": "cheapest"},
                    "query_type": "product_price",
                    "operation": "get_cheapest_product",
                    "limit": 1
                },
                "confidence": 0.95
            }
        
        if any(term in query_lower for term in ['price range', 'price statistics']):
            return {
                "intent": "execute_dynamic_query",
                "parameters": {
                    "table": "products",
                    "fields": ["min_price", "max_price", "avg_price", "product_count"],
                    "filters": {"operation": "price_range"},
                    "query_type": "product_price", 
                    "operation": "get_product_price_range"
                },
                "confidence": 0.9
            }
        
        if any(term in query_lower for term in ['average price', 'mean price']):
            return {
                "intent": "execute_dynamic_query",
                "parameters": {
                    "table": "products", 
                    "fields": ["avg_price"],
                    "filters": {"operation": "average_price"},
                    "query_type": "product_price",
                    "operation": "get_average_product_price"
                },
                "confidence": 0.9
            }
        
        # Try pattern matching for other queries
        for pattern, (intent, params) in self.query_patterns.items():
            if re.search(pattern, query_lower, re.IGNORECASE):
                print(f"✅ Pattern matched: {intent}")
                
                # Update parameters with extracted values
                final_params = params.copy()
                
                if customer_id and intent == "get_customer_orders":
                    final_params["customer_id"] = customer_id
                
                if months and intent == "get_monthly_revenue_trend":
                    final_params["months"] = int(months)
                
                if limit and intent in ["get_top_products", "get_least_sold_products"]:
                    final_params["limit"] = int(limit)
                
                # Handle customer ID extraction for pattern
                if intent == "get_customer_orders" and not final_params.get("customer_id"):
                    # Try to extract from the pattern match
                    customer_match = re.search(r'customer.*?(\d+)', query_lower)
                    if customer_match:
                        final_params["customer_id"] = customer_match.group(1)
                
                return {
                    "intent": intent,
                    "parameters": final_params,
                    "confidence": 0.9
                }
        
        # Enhanced keyword-based fallback
        return self._enhanced_keyword_fallback(query_lower)

    def _extract_parameter(self, pattern: str, query: str) -> str:
        """Extract parameter using regex pattern"""
        match = re.search(pattern, query)
        return match.group(1) if match else None

    def _enhanced_keyword_fallback(self, query_lower: str) -> Dict[str, Any]:
        """Enhanced keyword-based fallback parsing"""
        keywords = {
            'customer': ['customer', 'client', 'user'],
            'product': ['product', 'item', 'merchandise'],
            'order': ['order', 'sale', 'purchase'],
            'revenue': ['revenue', 'sales', 'income', 'money'],
            'price': ['price', 'cost', 'expensive', 'cheap'],
            'week': ['week', 'weekly'],
            'today': ['today', 'daily'],
            'month': ['month', 'monthly'],
            'top': ['top', 'best', 'most', 'highest'],
            'bottom': ['bottom', 'worst', 'least', 'lowest']
        }
        
        # Count keyword matches with weights
        scores = {category: 0 for category in keywords}
        for category, words in keywords.items():
            for word in words:
                if word in query_lower:
                    scores[category] += 1
        
        # Enhanced intent determination
        if scores['price'] > 0 and scores['top'] > 0:
            return {"intent": "get_costliest_product", "parameters": {}, "confidence": 0.8}
        elif scores['price'] > 0 and scores['bottom'] > 0:
            return {"intent": "get_cheapest_product", "parameters": {}, "confidence": 0.8}
        elif scores['customer'] > 0 and scores['top'] > 0:
            return {"intent": "get_repeat_customers", "parameters": {}, "confidence": 0.7}
        elif scores['customer'] > 0:
            return {"intent": "get_all_customers", "parameters": {}, "confidence": 0.7}
        elif scores['product'] > 0 and scores['bottom'] > 0:
            return {"intent": "get_least_sold_products", "parameters": {"limit": 5}, "confidence": 0.7}
        elif scores['product'] > 0 and scores['top'] > 0:
            return {"intent": "get_top_products", "parameters": {"limit": 5}, "confidence": 0.7}
        elif scores['product'] > 0:
            return {"intent": "get_all_products", "parameters": {}, "confidence": 0.7}
        elif scores['revenue'] > 0:
            return {"intent": "get_all_time_revenue", "parameters": {}, "confidence": 0.7}
        elif scores['today'] > 0:
            return {"intent": "get_daily_sales", "parameters": {"target_date": "today"}, "confidence": 0.7}
        elif scores['week'] > 0:
            return {"intent": "get_weekly_revenue", "parameters": {"start_date": "this_week", "end_date": "this_week"}, "confidence": 0.7}
        
        # Default safe fallback - show customers instead of products
        return {"intent": "get_all_customers", "parameters": {}, "confidence": 0.5}

    async def generate_natural_response(self, data: Any, original_query: str) -> str:
        """Generate natural language response with enhanced product handling"""
        # Use Gemini if available, otherwise enhanced fallback
        if self.model:
            try:
                prompt = f"""
                The user asked: "{original_query}"
                
                Data: {json.dumps(data, indent=2) if data else "No data found"}
                
                Provide a clear, concise response summarizing this data in natural language.
                Focus on answering the specific question asked.
                If it's about product prices, highlight the costliest/cheapest product specifically.
                """
                
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                print(f"Gemini response generation failed: {e}")
        
        # Enhanced fallback response generation
        return self._enhanced_fallback_response(data, original_query)

    async def verify_data(self):
        """Verify that data exists and is accessible"""
        try:
            products_count = await self.db.products.count_documents({})
            customers_count = await self.db.customers.count_documents({})
            orders_count = await self.db.orders.count_documents({})
            
            print(f"📊 Data verification:")
            print(f"   Products: {products_count}")
            print(f"   Customers: {customers_count}") 
            print(f"   Orders: {orders_count}")
            
            # Check if orders have items
            orders_with_items = await self.db.orders.count_documents({
                "items": {"$exists": True, "$ne": []}
            })
            print(f"   Orders with items: {orders_with_items}")
            
            return True
        except Exception as e:
            print(f"❌ Data verification failed: {e}")
            return False

    def _enhanced_fallback_response(self, data: Any, query: str) -> str:
        """Enhanced fallback response generation with product-specific handling"""
        if data is None:
            return f"No data found for: {query}"
        
        query_lower = query.lower()
        
        # Handle product price queries specifically
        if any(term in query_lower for term in ['costliest', 'most expensive', 'highest price']):
            if isinstance(data, list) and len(data) > 0:
                # Find the product with highest price
                costliest = max(data, key=lambda x: x.get('price', 0))
                return f"The costliest product is '{costliest.get('name', 'Unknown')}' priced at ${costliest.get('price', 0):.2f}"
        
        elif any(term in query_lower for term in ['cheapest', 'least expensive', 'lowest price']):
            if isinstance(data, list) and len(data) > 0:
                # Find the product with lowest price
                cheapest = min(data, key=lambda x: x.get('price', 0))
                return f"The cheapest product is '{cheapest.get('name', 'Unknown')}' priced at ${cheapest.get('price', 0):.2f}"
        
        # Generic response handling
        if isinstance(data, list):
            count = len(data)
            if count == 0:
                return f"No results found for: {query}"
            
            # Provide meaningful summary based on data structure
            if count > 0 and isinstance(data[0], dict):
                if 'name' in data[0] and 'price' in data[0]:
                    # Product data
                    if count <= 5:
                        products_info = [f"{item.get('name', 'Unknown')} (${item.get('price', 0):.2f})" for item in data]
                        return f"Found {count} products: {', '.join(products_info)}"
                    else:
                        sample_products = [f"{item.get('name', 'Unknown')} (${item.get('price', 0):.2f})" for item in data[:3]]
                        return f"Found {count} products. Examples: {', '.join(sample_products)}... and {count-3} more."
                elif 'name' in data[0]:
                    names = [item.get('name', 'Unknown') for item in data[:3]]
                    if count > 3:
                        return f"Found {count} items. Examples: {', '.join(names)}... and {count-3} more."
                    else:
                        return f"Found {count} items: {', '.join(names)}"
                elif 'total_amount' in data[0]:
                    total = sum(item.get('total_amount', 0) for item in data)
                    return f"Found {count} orders totaling ${total:,.2f}"
            
            return f"Found {count} records matching your query."
        
        if isinstance(data, (int, float)):
            if any(word in query_lower for word in ['revenue', 'sales', 'amount']):
                return f"Total revenue: ${data:,.2f}"
            return f"Result: {data}"
        
        if isinstance(data, dict):
            key_info = []
            for key, value in list(data.items())[:3]:
                if isinstance(value, (int, float)):
                    key_info.append(f"{key}: {value:,.2f}" if key in ['revenue', 'amount', 'price'] else f"{key}: {value}")
                else:
                    key_info.append(f"{key}: {value}")
            return f"Results: {', '.join(key_info)}"
        
        return f"Here's the data for your query: {str(data)}"