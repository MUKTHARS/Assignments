from .postgres import PostgresDB
from .mongodb import MongoDB
from .base import DatabaseInterface
from app.config import settings

class DatabaseFactory:
    @staticmethod
    async def create_database() -> DatabaseInterface:
        db_type = settings.DATABASE_TYPE.lower()
        
        if db_type == "postgres":
            if not settings.POSTGRES_URL:
                raise ValueError("PostgreSQL URL is required")
            db = PostgresDB(settings.POSTGRES_URL)
        elif db_type == "mongodb":
            if not settings.MONGODB_URL:
                raise ValueError("MongoDB URL is required")
            db = MongoDB(settings.MONGODB_URL)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
        
        await db.connect()
        return db
    
    @staticmethod
    async def initialize_sample_data(db: DatabaseInterface):
        print("🔄 Initializing sample data...")
        await db.initialize_sample_data()
        print("✅ Sample data initialization completed")