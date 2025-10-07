from fastapi import APIRouter, HTTPException
from app.services.analytics_service import AnalyticsService
from app.api.schemas import QueryRequest, QueryResponse, DatabaseConfig
from app.config import settings
import os
import traceback

# Create router with correct prefix
router = APIRouter(prefix="/api/v1", tags=["analytics"])

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
    try:
        current_db_type = analytics_service.current_db_type or "mongodb"
        initialized = analytics_service.db is not None
        return {
            "status": "healthy", 
            "database_type": current_db_type,
            "initialized": initialized
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@router.post("/reinitialize")
async def reinitialize_database():
    """Reinitialize database connection and sample data"""
    try:
        await analytics_service.reinitialize_database()
        return {"status": "success", "message": "Database reinitialized"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/switch-database")
async def switch_database(config: DatabaseConfig):
    """Switch database type dynamically"""
    try:
        print(f"🔄 Switching to database: {config.database_type}")
        print(f"🔗 Connection URL: {config.connection_url[:50]}...")
        
        # Validate database type
        if config.database_type.lower() not in ["postgres", "mongodb"]:
            raise HTTPException(status_code=400, detail="Database type must be 'postgres' or 'mongodb'")
        
        # Validate connection URL
        if not config.connection_url:
            raise HTTPException(status_code=400, detail="Connection URL is required")
        
        # Update environment variables temporarily for this connection
        if config.database_type.lower() == "postgres":
            os.environ["POSTGRES_URL"] = config.connection_url
            # Also update settings temporarily
            settings.POSTGRES_URL = config.connection_url
        else:
            os.environ["MONGODB_URL"] = config.connection_url
            settings.MONGODB_URL = config.connection_url
        
        # Reinitialize the database
        await analytics_service.reinitialize_database(config.database_type.lower())
        
        return {
            "status": "success", 
            "message": f"Switched to {config.database_type}",
            "database_type": config.database_type
        }
    except HTTPException:
        raise
    except Exception as e:
        error_detail = f"Failed to switch database: {str(e)}"
        print(f"❌ Database switch error: {error_detail}")
        print(f"🔍 Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_detail)

@router.post("/test-connection")
async def test_database_connection(config: DatabaseConfig):
    """Test database connection without switching"""
    try:
        print(f"🧪 Testing connection to: {config.database_type}")
        print(f"🔗 URL: {config.connection_url[:50]}...")
        
        # Validate inputs
        if config.database_type.lower() not in ["postgres", "mongodb"]:
            return {"status": "error", "message": "Invalid database type"}
        
        if not config.connection_url:
            return {"status": "error", "message": "Connection URL required"}
        
        # Test the connection
        if config.database_type.lower() == "postgres":
            from sqlalchemy import create_engine, text
            try:
                engine = create_engine(config.connection_url)
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT version()"))
                    version = result.scalar()
                return {"status": "success", "message": f"PostgreSQL connected: {version}"}
            except Exception as e:
                return {"status": "error", "message": f"PostgreSQL connection failed: {str(e)}"}
        else:
            from motor.motor_asyncio import AsyncIOMotorClient
            try:
                client = AsyncIOMotorClient(config.connection_url)
                # Test connection by listing databases
                databases = await client.list_database_names()
                return {"status": "success", "message": f"MongoDB connected, found {len(databases)} databases"}
            except Exception as e:
                return {"status": "error", "message": f"MongoDB connection failed: {str(e)}"}
                
    except Exception as e:
        return {"status": "error", "message": f"Test failed: {str(e)}"}