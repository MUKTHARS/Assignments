from pydantic import BaseModel
from typing import Any, Optional, Dict

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    response: str
    intent: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class DatabaseConfig(BaseModel):
    database_type: str
    connection_url: str