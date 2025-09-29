import re
import uuid
from datetime import datetime, date
from typing import Any, Dict, List, Optional
from decimal import Decimal

def format_currency(amount: float, currency: str = "USD") -> str:
    """
    Format currency amount with proper symbol and decimal places
    
    Args:
        amount: The amount to format
        currency: Currency code (USD, EUR, etc.)
    
    Returns:
        Formatted currency string
    """
    currency_symbols = {
        "USD": "$",
        "EUR": "€", 
        "GBP": "£",
        "JPY": "¥",
        "INR": "₹"
    }
    
    symbol = currency_symbols.get(currency, currency)
    
    if currency == "JPY":
        return f"{symbol}{amount:,.0f}"
    else:
        return f"{symbol}{amount:,.2f}"

def format_date(target_date: date, format_str: str = "%Y-%m-%d") -> str:
    """
    Format date to string
    
    Args:
        target_date: Date to format
        format_str: Format string
    
    Returns:
        Formatted date string
    """
    return target_date.strftime(format_str)

def generate_unique_id() -> str:
    """
    Generate a unique ID string
    
    Returns:
        Unique ID string
    """
    return str(uuid.uuid4())

def validate_email(email: str) -> bool:
    """
    Validate email format
    
    Args:
        email: Email address to validate
    
    Returns:
        True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert value to float
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
    
    Returns:
        Float value
    """
    try:
        if value is None:
            return default
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert value to integer
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
    
    Returns:
        Integer value
    """
    try:
        if value is None:
            return default
        return int(value)
    except (ValueError, TypeError):
        return default

def dict_to_sql_params(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert dictionary to SQL parameters format
    
    Args:
        data: Dictionary of data
    
    Returns:
        Dictionary with parameter keys
    """
    return {f"param_{k}": v for k, v in data.items()}

def calculate_percentage(part: float, whole: float) -> float:
    """
    Calculate percentage
    
    Args:
        part: Part value
        whole: Whole value
    
    Returns:
        Percentage value
    """
    if whole == 0:
        return 0.0
    return (part / whole) * 100

def format_large_number(number: float) -> str:
    """
    Format large numbers with K, M, B suffixes
    
    Args:
        number: Number to format
    
    Returns:
        Formatted number string
    """
    if number >= 1_000_000_000:
        return f"{number/1_000_000_000:.1f}B"
    elif number >= 1_000_000:
        return f"{number/1_000_000:.1f}M"
    elif number >= 1_000:
        return f"{number/1_000:.1f}K"
    else:
        return f"{number:.0f}"

def sanitize_query_string(query: str) -> str:
    """
    Sanitize query string for security
    
    Args:
        query: Query string to sanitize
    
    Returns:
        Sanitized query string
    """
    # Remove potentially dangerous SQL keywords (basic protection)
    dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE']
    sanitized = query
    for keyword in dangerous_keywords:
        sanitized = sanitized.replace(keyword, '')
    return sanitized.strip()