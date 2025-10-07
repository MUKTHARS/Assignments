from .postgres import PostgresDB
from .mongodb import MongoDB
from .base import DatabaseInterface
from app.config import settings
import traceback

class DatabaseFactory:
    @staticmethod
    async def create_database(database_type: str = None) -> DatabaseInterface:
        # Use provided database_type or fall back to settings
        db_type = database_type or settings.DATABASE_TYPE.lower()
        
        print(f"🔄 Creating database connection for type: {db_type}")
        
        try:
            if db_type == "postgres":
                if not settings.POSTGRES_URL:
                    raise ValueError("PostgreSQL URL is required")
                print(f"🔗 PostgreSQL URL: {settings.POSTGRES_URL[:20]}...")  # Log first 20 chars
                db = PostgresDB(settings.POSTGRES_URL)
            elif db_type == "mongodb":
                if not settings.MONGODB_URL:
                    raise ValueError("MongoDB URL is required")
                print(f"🔗 MongoDB URL: {settings.MONGODB_URL[:20]}...")  # Log first 20 chars
                db = MongoDB(settings.MONGODB_URL)
            else:
                raise ValueError(f"Unsupported database type: {db_type}")
            
            await db.connect()
            print(f"✅ Successfully connected to {db_type}")
            return db
            
        except Exception as e:
            print(f"❌ Error creating database connection for {db_type}: {str(e)}")
            print(f"🔍 Full error traceback: {traceback.format_exc()}")
            raise
    
    @staticmethod
    async def initialize_sample_data(db: DatabaseInterface):
        """Initialize sample data only if needed"""
        print("🔄 Checking if sample data initialization is needed...")
        try:
            await db.initialize_sample_data()
            print("✅ Sample data initialization completed")
        except Exception as e:
            print(f"❌ Error during sample data initialization: {str(e)}")
            print(f"🔍 Full error traceback: {traceback.format_exc()}")
            raise