from app.settings import get_settings
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

settings = get_settings()

db_client: AsyncIOMotorClient = None

# https://stackoverflow.com/a/65548346


# async def get_db_instance() -> AsyncIOMotorDatabase:
#     """Return a database instance."""
#     return db_client.piav


async def connect_db():
    """Create database connection."""
    global db_client

    db_client = AsyncIOMotorClient(settings.mongo_db_uri)


async def close_db():
    """Close database connection."""
    db_client.close()


def get_db_instance()-> AsyncIOMotorDatabase:
    yield db_client.piav