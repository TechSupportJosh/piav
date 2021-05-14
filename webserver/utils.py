from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId


async def update_task_status(db: AsyncIOMotorDatabase, task_id: ObjectId, status: str):
    await db.input.update_one({"_id": task_id}, {"$set": {"status": status}})
