from fastapi import APIRouter, HTTPException
from app.services.analytics_service import AnalyticsService
from app.api.schemas import QueryRequest, QueryResponse, DatabaseConfig
from app.config import settings
import os

router = APIRouter()
analytics_service = AnalyticsService()

@router.post("/query", response_model=QueryResponse)
async def process_natural_language_query(request: QueryRequest):
    """Process natural language queries about sales data"""
    try:
        result = await analytics_service.process_query(request.query)
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "database_type": settings.DATABASE_TYPE,
        "initialized": analytics_service.db is not None
    }

@router.post("/reinitialize")
async def reinitialize_database():
    """Reinitialize database connection and sample data"""
    try:
        await analytics_service.initialize_database()
        return {"status": "success", "message": "Database reinitialized"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))