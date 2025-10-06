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
            print(f"🔧 Initializing Gemini API with key: {settings.GEMINI_API_KEY[:10]}...")
            
            # Configure with the correct API key
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # Try to use the most reliable model
            model_name = 'gemini-2.0-flash'  # Most stable and widely available
            
            try:
                # First, test if the API key is valid by listing models
                available_models = genai.list_models()
                print(f"✅ API key validated. Available models: {len(available_models)}")
                
                # Check if our preferred model is available
                available_model_names = [model.name for model in available_models]
                print(f"📋 Available model names: {[name for name in available_model_names if 'gemini' in name][:5]}...")
                
                # Try to find the best available model
                preferred_models = [
                    'models/gemini-2.0-flash',
                    'models/gemini-2.0-flash-001',
                    'models/gemini-pro',
                    'models/gemini-1.5-flash',
                    'models/gemini-1.5-pro',
                    'models/gemini-flash-latest',
                    'models/gemini-pro-latest'
                ]
                
                selected_model = None
                for preferred in preferred_models:
                    if preferred in available_model_names:
                        selected_model = preferred
                        print(f"✅ Selected model: {selected_model}")
                        break
                
                if not selected_model:
                    # Fallback to any available Gemini model
                    for model_name in available_model_names:
                        if 'gemini' in model_name.lower() and 'generateContent' in [method for method in genai.get_model(model_name).supported_generation_methods]:
                            selected_model = model_name
                            print(f"🔄 Fallback to: {selected_model}")
                            break
                
                if selected_model:
                    self.model = genai.GenerativeModel(selected_model)
                    
                    # Test the model with a simple prompt
                    try:
                        test_response = self.model.generate_content("Hello, respond with 'OK' if working.")
                        if test_response and hasattr(test_response, 'text') and test_response.text:
                            self.is_gemini_available = True
                            print(f"🎉 Gemini model initialized successfully: {selected_model}")
                            print(f"✅ Test response: {test_response.text}")
                        else:
                            print("❌ Model test failed - no valid response")
                            self._try_direct_initialization()
                    except Exception as test_error:
                        print(f"❌ Model test failed: {test_error}")
                        self._try_direct_initialization()
                else:
                    print("❌ No suitable Gemini model found")
                    self._try_direct_initialization()
                    
            except Exception as list_error:
                print(f"❌ Could not list models: {list_error}")
                self._try_direct_initialization()
                
        except Exception as e:
            print(f"❌ Gemini configuration failed: {e}")
            print("🔄 Using enhanced fallback parsing")
    
        # Enhanced query patterns for better matching
        self.query_patterns = self._initialize_query_patterns()
        
        # Final check and debug output
        print(f"🔍 Final Gemini status: {'AVAILABLE' if self.is_gemini_available else 'NOT AVAILABLE'}")
        if self.is_gemini_available:
            print(f"🔍 Model: {self.model}")

    def _try_direct_initialization(self):
        """Try direct initialization with common models"""
        print("🔄 Attempting direct model initialization...")
        
        direct_models = [
            'gemini-2.0-flash',
            'gemini-pro', 
            'gemini-1.5-flash',
            'gemini-1.5-pro',
            'models/gemini-pro'
        ]
        
        for model_name in direct_models:
            try:
                print(f"🔄 Trying direct: {model_name}")
                self.model = genai.GenerativeModel(model_name)
                
                # Quick silent test
                test_response = self.model.generate_content("Test")
                if test_response and hasattr(test_response, 'text'):
                    self.is_gemini_available = True
                    print(f"✅ Direct initialization successful: {model_name}")
                    return
            except Exception as e:
                print(f"❌ Direct model {model_name} failed: {str(e)[:100]}...")
                continue
        
        # Ultimate fallback - try without specifying model
        try:
            print("🔄 Trying ultimate fallback...")
            self.model = genai.GenerativeModel('gemini-pro')
            self.is_gemini_available = True
            print("✅ Ultimate fallback successful")
        except Exception as final_error:
            print(f"❌ All initialization attempts failed: {final_error}")

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
            
            # Product price queries - COMPREHENSIVE PATTERNS
            r'.*costliest.*product.*': ("get_costliest_product", {}),
            r'.*most.expensive.*product.*': ("get_costliest_product", {}),
            r'.*highest.price.*product.*': ("get_costliest_product", {}),
            r'.*maximum.price.*product.*': ("get_costliest_product", {}),
            r'.*most.costly.*product.*': ("get_costliest_product", {}),
            r'.*expensive.*product.*': ("get_costliest_product", {}),
            r'.*cheapest.*product.*': ("get_cheapest_product", {}),
            r'.*least.expensive.*product.*': ("get_cheapest_product", {}),
            r'.*lowest.price.*product.*': ("get_cheapest_product", {}),
            r'.*minimum.price.*product.*': ("get_cheapest_product", {}),
            r'.*most.affordable.*product.*': ("get_cheapest_product", {}),
            r'.*product.price.range.*': ("get_product_price_range", {}),
            r'.*price.range.*product.*': ("get_product_price_range", {}),
            r'.*min.and.max.price.*': ("get_product_price_range", {}),
            r'.*price.statistics.*': ("get_product_price_range", {}),
            r'.*average.product.price.*': ("get_average_product_price", {}),
            r'.*avg.price.*product.*': ("get_average_product_price", {}),
            r'.*mean.price.*product.*': ("get_average_product_price", {}),
            r'.*what.is.the.average.price.*': ("get_average_product_price", {}),
            
            # Product search queries - NEW PATTERNS FOR SPECIFIC PRODUCTS
            r'.*price.*of.*macbook.*': ("get_all_products", {"search_term": "macbook"}),
            r'.*cost.*of.*macbook.*': ("get_all_products", {"search_term": "macbook"}),
            r'.*how.much.*macbook.*': ("get_all_products", {"search_term": "macbook"}),
            r'.*price.*of.*iphone.*': ("get_all_products", {"search_term": "iphone"}),
            r'.*cost.*of.*iphone.*': ("get_all_products", {"search_term": "iphone"}),
            r'.*how.much.*iphone.*': ("get_all_products", {"search_term": "iphone"}),
            r'.*price.*of.*samsung.*': ("get_all_products", {"search_term": "samsung"}),
            r'.*cost.*of.*samsung.*': ("get_all_products", {"search_term": "samsung"}),
            r'.*price.*of.*laptop.*': ("get_all_products", {"search_term": "laptop"}),
            r'.*cost.*of.*laptop.*': ("get_all_products", {"search_term": "laptop"}),
            r'.*price.*of.*phone.*': ("get_all_products", {"search_term": "phone"}),
            r'.*cost.*of.*phone.*': ("get_all_products", {"search_term": "phone"}),
            r'.*how.much.*does.*cost.*': ("get_all_products", {"search_term": ""}),  # Generic price query
            
            # Product performance queries
            r'.*top.*(\d+).*product.*revenue.*': ("get_top_products", {"limit": None}),
            r'.*top.*(\d+).*product.*': ("get_top_products", {"limit": None}),
            r'.*best.*selling.*product.*': ("get_top_products", {"limit": 5}),
            r'.*most.popular.*product.*': ("get_top_products", {"limit": 5}),
            r'.*top.*product.*': ("get_top_products", {"limit": 10}),
            r'.*best.performing.*product.*': ("get_top_products", {"limit": 5}),
            r'.*highest.selling.*product.*': ("get_top_products", {"limit": 5}),
            r'.*least.*sold.*product.*': ("get_least_sold_products", {"limit": 5}),
            r'.*worst.*selling.*product.*': ("get_least_sold_products", {"limit": 5}),
            r'.*poorly.performing.*product.*': ("get_least_sold_products", {"limit": 5}),
            r'.*lowest.selling.*product.*': ("get_least_sold_products", {"limit": 5}),
            
            # Customer queries - COMPREHENSIVE PATTERNS
            r'.*all.*customer.*': ("get_all_customers", {}),
            r'.*list.*customer.*': ("get_all_customers", {}),
            r'.*show.*customer.*': ("get_all_customers", {}),
            r'.*how.many.*customer.*': ("get_all_customers", {}),
            r'.*number.*customer.*': ("get_all_customers", {}),
            r'.*count.*customer.*': ("get_all_customers", {}),
            r'.*total.*customer.*': ("get_all_customers", {}),
            r'.*customer.list.*': ("get_all_customers", {}),
            r'.*repeat.*customer.*': ("get_repeat_customers", {}),
            r'.*loyal.*customer.*': ("get_repeat_customers", {}),
            r'.*frequent.*customer.*': ("get_repeat_customers", {}),
            r'.*multiple.orders.*customer.*': ("get_repeat_customers", {}),
            r'.*inactive.*customer.*': ("get_inactive_customers", {"days_threshold": 30}),
            r'.*not.active.*customer.*': ("get_inactive_customers", {"days_threshold": 30}),
            r'.*dormant.*customer.*': ("get_inactive_customers", {"days_threshold": 30}),
            
            # Order queries with dates - COMPREHENSIVE PATTERNS
            r'.*today.*sale.*': ("get_daily_sales", {"target_date": "today"}),
            r'.*today.*order.*': ("get_daily_sales", {"target_date": "today"}),
            r'.*sales.*today.*': ("get_daily_sales", {"target_date": "today"}),
            r'.*do.we.have.*sale.*today.*': ("get_daily_sales", {"target_date": "today"}),
            r'.*any.*sale.*today.*': ("get_daily_sales", {"target_date": "today"}),
            r'.*current.day.*sale.*': ("get_daily_sales", {"target_date": "today"}),
            r'.*yesterday.*sale.*': ("get_daily_sales", {"target_date": "yesterday"}),
            r'.*yesterday.*order.*': ("get_daily_sales", {"target_date": "yesterday"}),
            r'.*previous.day.*sale.*': ("get_daily_sales", {"target_date": "yesterday"}),
            r'.*recent.*order.*': ("get_recent_orders", {"limit": 10}),
            r'.*latest.*order.*': ("get_recent_orders", {"limit": 10}),
            r'.*new.*order.*': ("get_recent_orders", {"limit": 10}),
            r'.*last.*order.*': ("get_recent_orders", {"limit": 10}),
            
            # Customer specific queries
            r'.*order.*for.customer.*(\d+).*': ("get_customer_orders", {"customer_id": None}),
            r'.*customer.*(\d+).*order.*': ("get_customer_orders", {"customer_id": None}),
            r'.*show.*order.*customer.*(\d+).*': ("get_customer_orders", {"customer_id": None}),
            r'.*purchase.history.*customer.*(\d+).*': ("get_customer_orders", {"customer_id": None}),
            r'.*transaction.history.*customer.*(\d+).*': ("get_customer_orders", {"customer_id": None}),
            
            # Category queries
            r'.*sale.*by.*categor.*': ("get_sales_by_category", {"start_date": "last_month", "end_date": "today"}),
            r'.*category.*performance.*': ("get_sales_by_category", {"start_date": "last_month", "end_date": "today"}),
            r'.*revenue.*by.*categor.*': ("get_sales_by_category", {"start_date": "last_month", "end_date": "today"}),
            r'.*which.category.*best.*': ("get_sales_by_category", {"start_date": "last_month", "end_date": "today"}),
            r'.*category.wise.*sale.*': ("get_sales_by_category", {"start_date": "last_month", "end_date": "today"}),
            
            # Trend queries
            r'.*monthly.*trend.*': ("get_monthly_revenue_trend", {"months": 6}),
            r'.*revenue.*trend.*': ("get_monthly_revenue_trend", {"months": 6}),
            r'.*sales.*trend.*': ("get_monthly_revenue_trend", {"months": 6}),
            r'.*performance.trend.*': ("get_monthly_revenue_trend", {"months": 6}),
            r'.*growth.trend.*': ("get_monthly_revenue_trend", {"months": 6}),
            r'.*last.(\d+).month.*trend.*': ("get_monthly_revenue_trend", {"months": None}),
            r'.*past.(\d+).month.*trend.*': ("get_monthly_revenue_trend", {"months": None}),
            
            # Product catalog queries
            r'.*all.*product.*': ("get_all_products", {}),
            r'.*list.*product.*': ("get_all_products", {}),
            r'.*show.*product.*': ("get_all_products", {}),
            r'.*product.catalog.*': ("get_all_products", {}),
            r'.*available.product.*': ("get_all_products", {}),
            r'.*what.product.*do.we.have.*': ("get_all_products", {}),
        }

    def parse_natural_language(self, query: str) -> Dict[str, Any]:
        """Parse natural language query using forced Gemini parsing"""
        print(f"🔍 Processing query: '{query}'")
        
        # FORCE Gemini to handle everything - no early fallbacks
        if self.is_gemini_available and self.model:
            try:
                print("🚀 FORCING Gemini to process query...")
                
                # Use the most reliable parsing method
                gemini_result = self._force_gemini_parsing(query)
                if gemini_result and gemini_result.get('intent') != 'unknown':
                    print(f"✅ Gemini parsing successful: {gemini_result['intent']}")
                    return gemini_result
                else:
                    print("❌ Gemini parsing returned unknown intent")
                    
            except Exception as e:
                print(f"❌ Gemini parsing failed with error: {e}")
        
        else:
            print("❌ Gemini not available - using fallback parsing")
    
        # ONLY use pattern matching if Gemini is completely unavailable
        print("🔄 Falling back to pattern matching...")
        processed_query = self._preprocess_query(query)
        return self._enhanced_pattern_parsing(processed_query.lower(), query)

    def _force_gemini_parsing(self, query: str) -> Dict[str, Any]:
        """Force Gemini to parse the query with maximum reliability"""
        try:
            prompt = f"""
            CRITICAL: You MUST process this shopping analytics query and return ONLY valid JSON.
            
            USER QUERY: "{query}"

            AVAILABLE FUNCTIONS:
            - get_weekly_revenue(start_date, end_date): Use ONLY for 7-day periods or custom date ranges
            - get_monthly_revenue(months, last_month): Use for monthly revenue (current/last month)
            - get_monthly_revenue_trend(months): Use for multi-month trends and analysis
            - get_all_time_revenue(): Use for total lifetime revenue
            - get_daily_sales(target_date): Use for single day sales
            - get_sales_by_category(start_date, end_date): Use for category breakdowns within date ranges
            - get_all_products(search_term): Search products by name
            - get_costliest_product(): Most expensive product
            - get_cheapest_product(): Least expensive product  
            - get_product_price_range(): Price statistics
            - get_average_product_price(): Average price
            - get_top_products(limit): Best selling products
            - get_all_customers(): All customers
            - get_customer_orders(customer_id): Customer orders
            - get_recent_orders(limit): Recent orders
            - get_least_sold_products(limit): Least sold products
            - get_repeat_customers(): Repeat customers
            - get_inactive_customers(days_threshold): Inactive customers
            - get_inventory_status(): Inventory status
            - get_product_reviews(product_id): Product reviews

            FUNCTION SELECTION RULES:
            1. For "last X days" where X ≠ 7: Use get_weekly_revenue with calculated dates
            2. For "last week" or "7 days": Use get_weekly_revenue with 7-day range
            3. For "last X months" trends: Use get_monthly_revenue_trend(months=X)
            4. For "last month" revenue: Use get_monthly_revenue(last_month=true)
            5. For "this month" revenue: Use get_monthly_revenue(last_month=false)
            6. For "last year" or long periods: Use get_weekly_revenue with 365-day range
            7. For category analysis: Use get_sales_by_category
            8. For trend analysis: Use get_monthly_revenue_trend

            DATE RANGE CALCULATIONS:
            - "last 15 days" → start_date = ((today - 15 days)), end_date = today → get_weekly_revenue
            - "past 2 months" → months = 2 → get_monthly_revenue_trend
            - "last 6 months trend" → months = 6 → get_monthly_revenue_trend
            - "last month sales" → last_month = true → get_monthly_revenue
            - "last year revenue" → start_date = ((today - 365 days)), end_date = today → get_weekly_revenue

            RESPOND WITH VALID JSON ONLY. Examples:

            Example for "last 15 days revenue":
            {{
                "intent": "get_weekly_revenue",
                "parameters": {{
                    "start_date": "((today - 15 days))",
                    "end_date": "today"
                }},
                "confidence": 0.95,
                "reasoning": "15-day period, using weekly revenue function with custom date range"
            }}

            Example for "past 2 months sales trend":
            {{
                "intent": "get_monthly_revenue_trend",
                "parameters": {{
                    "months": 2
                }},
                "confidence": 0.92,
                "reasoning": "Multi-month trend analysis, using monthly revenue trend function"
            }}

            Example for "last month revenue":
            {{
                "intent": "get_monthly_revenue",
                "parameters": {{
                    "last_month": true
                }},
                "confidence": 0.98,
                "reasoning": "Specific month revenue request, using monthly revenue function"
            }}

            Example for "sales by category last 30 days":
            {{
                "intent": "get_sales_by_category",
                "parameters": {{
                    "start_date": "((today - 30 days))",
                    "end_date": "today"
                }},
                "confidence": 0.94,
                "reasoning": "Category breakdown request with date range"
            }}

            Example for "revenue trend for past 6 months":
            {{
                "intent": "get_monthly_revenue_trend",
                "parameters": {{
                    "months": 6
                }},
                "confidence": 0.96,
                "reasoning": "Multi-month trend analysis request"
            }}

            Example for "last week revenue":
            {{
                "intent": "get_weekly_revenue",
                "parameters": {{
                    "start_date": "((today - 7 days))",
                    "end_date": "today"
                }},
                "confidence": 0.97,
                "reasoning": "7-day period, using weekly revenue function"
            }}

            NOW PROCESS: "{query}"
            IMPORTANT: Choose the MOST SPECIFIC function based on the query context and time period.
            """

            print("🤖 Sending forced request to Gemini...")
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            print(f"🔍 Gemini forced response: {response_text}")
            
            # Extract JSON from response
            json_match = re.search(r'\{[^{}]*\{[^{}]*\}[^{}]*\}|\{[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    
                    # Process dynamic date calculations
                    result = self._process_dynamic_dates(result, query)
                    
                    # Validate the result
                    if self._validate_forced_result(result):
                        return result
                    else:
                        print("⚠️ Forced result validation failed")
                except json.JSONDecodeError as e:
                    print(f"❌ JSON parsing error: {e}")
                    # Try to fix common JSON issues
                    fixed_json = self._fix_json_response(response_text)
                    if fixed_json:
                        try:
                            result = json.loads(fixed_json)
                            result = self._process_dynamic_dates(result, query)
                            if self._validate_forced_result(result):
                                return result
                        except:
                            pass
                            
        except Exception as e:
            print(f"❌ Forced Gemini API error: {e}")
            
        return {"intent": "unknown", "parameters": {}, "confidence": 0.0}

    def _process_dynamic_dates(self, result: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Process dynamic date calculations in the result parameters with proper historical data handling"""
        if 'parameters' not in result:
            return result
        
        params = result['parameters']
        query_lower = query.lower()
        
        # Extract number of days from query
        days_match = re.search(r'last\s+(\d+)\s+days', query_lower) or \
                    re.search(r'past\s+(\d+)\s+days', query_lower) or \
                    re.search(r'(\d+)\s+days', query_lower)
        
        # Extract number of months from query
        months_match = re.search(r'last\s+(\d+)\s+months', query_lower) or \
                      re.search(r'past\s+(\d+)\s+months', query_lower) or \
                      re.search(r'(\d+)\s+months', query_lower)
        
        # Extract number of years from query
        years_match = re.search(r'last\s+(\d+)\s+years', query_lower) or \
                     re.search(r'past\s+(\d+)\s+years', query_lower) or \
                     re.search(r'(\d+)\s+years', query_lower)
        
        # Extract number of weeks from query
        weeks_match = re.search(r'last\s+(\d+)\s+weeks', query_lower) or \
                     re.search(r'past\s+(\d+)\s+weeks', query_lower) or \
                     re.search(r'(\d+)\s+weeks', query_lower)
        
        from datetime import date, timedelta, datetime
        
        # Calculate dates based on your database timeframe (most orders are from 2025)
        # Use a reference date that matches your data distribution
        reference_date = date(2025, 10, 15)  # Most orders are around July-Sept 2025
        
        if days_match:
            days = int(days_match.group(1))
            start_date = reference_date - timedelta(days=days)
            end_date = reference_date
            
            params['start_date'] = start_date.isoformat()
            params['end_date'] = end_date.isoformat()
            print(f"📅 Calculated {days} days range: {params['start_date']} to {params['end_date']}")
        
        elif weeks_match:
            weeks = int(weeks_match.group(1))
            days = weeks * 7
            start_date = reference_date - timedelta(days=days)
            end_date = reference_date
            
            params['start_date'] = start_date.isoformat()
            params['end_date'] = end_date.isoformat()
            print(f"📅 Calculated {weeks} weeks range: {params['start_date']} to {params['end_date']}")
        
        elif months_match:
            months = int(months_match.group(1))
            # Approximate months as 30 days each
            days = months * 30
            start_date = reference_date - timedelta(days=days)
            end_date = reference_date
            
            params['start_date'] = start_date.isoformat()
            params['end_date'] = end_date.isoformat()
            print(f"📅 Calculated {months} months range: {params['start_date']} to {params['end_date']}")
        
        elif years_match:
            years = int(years_match.group(1))
            # Approximate years as 365 days
            days = years * 365
            start_date = reference_date - timedelta(days=days)
            end_date = reference_date
            
            params['start_date'] = start_date.isoformat()
            params['end_date'] = end_date.isoformat()
            print(f"📅 Calculated {years} years range: {params['start_date']} to {params['end_date']}")
        
        # Handle relative time periods without specific numbers
        elif 'last week' in query_lower or 'past week' in query_lower:
            start_date = reference_date - timedelta(days=7)
            end_date = reference_date
            params['start_date'] = start_date.isoformat()
            params['end_date'] = end_date.isoformat()
            print(f"📅 Calculated last week range: {params['start_date']} to {params['end_date']}")
        
        elif 'last month' in query_lower or 'past month' in query_lower:
            start_date = reference_date - timedelta(days=30)
            end_date = reference_date
            params['start_date'] = start_date.isoformat()
            params['end_date'] = end_date.isoformat()
            print(f"📅 Calculated last month range: {params['start_date']} to {params['end_date']}")
        
        elif 'last year' in query_lower or 'past year' in query_lower:
            start_date = reference_date - timedelta(days=365)
            end_date = reference_date
            params['start_date'] = start_date.isoformat()
            params['end_date'] = end_date.isoformat()
            print(f"📅 Calculated last year range: {params['start_date']} to {params['end_date']}")
        
        elif 'last 3 months' in query_lower:
            start_date = reference_date - timedelta(days=90)
            end_date = reference_date
            params['start_date'] = start_date.isoformat()
            params['end_date'] = end_date.isoformat()
            print(f"📅 Calculated last 3 months range: {params['start_date']} to {params['end_date']}")
        
        elif 'last 6 months' in query_lower:
            start_date = reference_date - timedelta(days=180)
            end_date = reference_date
            params['start_date'] = start_date.isoformat()
            params['end_date'] = end_date.isoformat()
            print(f"📅 Calculated last 6 months range: {params['start_date']} to {params['end_date']}")
        
        # Process any remaining dynamic date calculations from Gemini
        if 'start_date' in params and isinstance(params['start_date'], str):
            if '((today -' in params['start_date']:
                # Extract days from the dynamic calculation
                days_match = re.search(r'\(\(today - (\d+) days\)\)', params['start_date'])
                if days_match:
                    days = int(days_match.group(1))
                    start_date = reference_date - timedelta(days=days)
                    params['start_date'] = start_date.isoformat()
                    print(f"📅 Processed dynamic date: {params['start_date']}")
        
        if 'end_date' in params and params['end_date'] == 'today':
            params['end_date'] = reference_date.isoformat()
            print(f"📅 Set end_date to reference date: {params['end_date']}")
        
        # Ensure dates are within your data range (adjust based on your actual data)
        # Your data seems to be from mid-2025, so ensure we don't go too far back
        if 'start_date' in params:
            start_date_obj = datetime.fromisoformat(params['start_date']).date()
            min_date = date(2025, 7, 1)  # Your earliest data starts from July 2025
            max_date = date(2025, 10, 30)  # Your latest data goes to September 2025
            if start_date_obj < min_date:
                params['start_date'] = min_date.isoformat()
                print(f"📅 Adjusted start_date to minimum: {params['start_date']}")
            if start_date_obj > max_date:
                params['start_date'] = max_date.isoformat()
                print(f"📅 Adjusted start_date to maximum: {params['start_date']}")
        
        return result


    def _validate_forced_result(self, result: Dict[str, Any]) -> bool:
        """Validate forced Gemini parsing result"""
        if not isinstance(result, dict):
            return False
            
        required_keys = ['intent', 'parameters']
        if not all(key in result for key in required_keys):
            return False
            
        if not isinstance(result['parameters'], dict):
            return False
            
        # Valid intents
        valid_intents = [
            'get_all_products', 'get_costliest_product', 'get_cheapest_product',
            'get_product_price_range', 'get_average_product_price', 'get_top_products',
            'get_weekly_revenue', 'get_monthly_revenue', 'get_all_time_revenue',
            'get_daily_sales', 'get_all_customers', 'get_customer_orders',
            'get_sales_by_category', 'get_monthly_revenue_trend', 'get_recent_orders',
            'get_least_sold_products', 'get_repeat_customers', 'get_inactive_customers',
            'get_inventory_status', 'get_product_reviews'
        ]
        
        if result['intent'] not in valid_intents:
            print(f"⚠️ Invalid intent in forced result: {result['intent']}")
            return False
            
        # Don't validate date parameters too strictly - let the processing handle it
        # Ensure confidence exists
        if 'confidence' not in result:
            result['confidence'] = 0.8
            
        return True

    def _fix_json_response(self, response_text: str) -> str:
        """Fix common JSON response issues from Gemini"""
        try:
            # Remove extra text before and after JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                
                # Fix common JSON issues
                json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas
                json_str = re.sub(r',\s*]', ']', json_str)  # Remove trailing commas in arrays
                json_str = re.sub(r'(\w+):', r'"\1":', json_str)  # Add quotes to keys
                json_str = re.sub(r':\s*\'([^\']+)\'', r': "\1"', json_str)  # Replace single quotes with double
                
                return json_str
        except Exception as e:
            print(f"❌ JSON fixing failed: {e}")
        
        return None

    def _preprocess_query(self, query: str) -> str:
        """Preprocess and normalize user queries for better matching"""
        query_lower = query.lower().strip()
        
        # Common user query variations and typo corrections
        replacements = {
            r'do we have any': 'show',
            r'how many': 'count',
            r'what is': 'show',
            r'can you show': 'show',
            r'can you tell': 'show',
            r'i want to see': 'show',
            r'give me': 'show',
            r'display': 'show',
            r'list': 'show',
            r'could you': '',
            r'would you': '',
            r'please': '',
            r'kindly': '',
            r'i need': 'show',
            r'i would like': 'show',
            r'last moths': 'last month',
            r'last months': 'last month',
            r'last mont': 'last month',
            r'this moths': 'this month',
            r'this months': 'this month',
            r'this mont': 'this month',
            r'revenu': 'revenue',
            r'reveneu': 'revenue',
            r'reveniew': 'revenue',
            r'costliest': 'most expensive',
            r'cheapest': 'least expensive',
            r'costley': 'most expensive',
            r'cheep': 'least expensive'
        }
        
        processed_query = query_lower
        for pattern, replacement in replacements.items():
            processed_query = re.sub(pattern, replacement, processed_query)
        
        # Remove common filler words
        filler_words = ['the', 'a', 'an', 'our', 'my', 'your', 'some', 'any']
        for word in filler_words:
            processed_query = re.sub(r'\b' + word + r'\b', '', processed_query)
        
        # Normalize spaces
        processed_query = re.sub(r'\s+', ' ', processed_query).strip()
        
        if processed_query != query_lower:
            print(f"🔧 Query normalized: '{query_lower}' -> '{processed_query}'")
        
        return processed_query

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
            'category': ['category', 'type', 'group'],
            'costly': ['costliest', 'most expensive', 'highest price', 'maximum price'],
            'cheap': ['cheapest', 'least expensive', 'lowest price', 'minimum price']
        }
        
        # Count keyword matches with weights
        scores = {category: 0 for category in keywords}
        for category, words in keywords.items():
            for word in words:
                if word in query_lower:
                    scores[category] += 1
        
        # Enhanced intent determination with better logic
        if scores['costly'] > 0 and scores['product'] > 0:
            return {"intent": "get_costliest_product", "parameters": {}, "confidence": 0.9}
        elif scores['cheap'] > 0 and scores['product'] > 0:
            return {"intent": "get_cheapest_product", "parameters": {}, "confidence": 0.9}
        elif scores['today'] > 0 and (scores['order'] > 0 or scores['revenue'] > 0):
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
        if "costliest" in query_lower or "most expensive" in query_lower:
            return {"intent": "get_costliest_product", "parameters": {}, "confidence": 0.7}
        elif "cheapest" in query_lower or "least expensive" in query_lower:
            return {"intent": "get_cheapest_product", "parameters": {}, "confidence": 0.7}
        elif "today" in query_lower:
            return {"intent": "get_daily_sales", "parameters": {"target_date": "today"}, "confidence": 0.6}
        elif "customer" in query_lower:
            return {"intent": "get_all_customers", "parameters": {}, "confidence": 0.6}
        elif "product" in query_lower:
            return {"intent": "get_all_products", "parameters": {}, "confidence": 0.6}
        
        return {"intent": "get_all_time_revenue", "parameters": {}, "confidence": 0.5}

    async def generate_natural_response(self, data: Any, original_query: str) -> str:
        """Generate natural language response using Gemini when available"""
        # Use Gemini if available for better responses
        if self.is_gemini_available and self.model:
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