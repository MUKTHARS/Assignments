from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router as api_router
from app.config import settings

app = FastAPI(
    title="Shopping Analytics API",
    description="LLM-powered shopping store analytics with dynamic database support",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        from app.services.analytics_service import AnalyticsService
        analytics_service = AnalyticsService()
        await analytics_service.initialize_database()
        print("✅ Application started successfully")
    except Exception as e:
        print(f"❌ Error during startup: {e}")

@app.get("/")
async def root():
    return {
        "message": "Shopping Analytics API", 
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "health": "/api/v1/health",
            "query": "/api/v1/query", 
            "switch-database": "/api/v1/switch-database",
            "test-connection": "/api/v1/test-connection"
        }
    }

# Add health redirect to fix 404
# @app.get("/health")
# async def health_redirect():
#     """Redirect to the actual health endpoint"""
#     from fastapi.responses import RedirectResponse
#     return RedirectResponse(url="/api/v1/health")