from typing import List

import models
from database import get_db_instance
from fastapi import APIRouter
from fastapi.params import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(
    prefix="/queue",
    tags=["Queue Endpoints"],
)


@router.get(
    "/",
    response_model=List[models.QueueEntry],
    description="Retrieve all tasks in queue.",
)
async def get_queue(db: AsyncIOMotorDatabase = Depends(get_db_instance)):
    tasks = await db.queue.find().to_list(length=None)
    return tasks
