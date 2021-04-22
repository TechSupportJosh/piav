from bson.objectid import ObjectId
from database import get_db_instance
from fastapi import APIRouter, HTTPException, Response
from motor.motor_asyncio import AsyncIOMotorDatabase
import models
from typing import List
from fastapi.params import Depends

router = APIRouter(
    prefix="/portal",
    tags=["Portal Related Endpoints"],
)


@router.get("/queue", response_model=List[models.QueueEntry])
async def get_queue(db: AsyncIOMotorDatabase = Depends(get_db_instance)):
    tasks = await db.queue.find().to_list(length=None)
    return tasks


@router.get("/task/{task_id}/input", response_model=models.TaskOutput)
async def get_task_input(
    task_id: str, db: AsyncIOMotorDatabase = Depends(get_db_instance)
):
    response = await db.input.find_one({"_id": ObjectId(task_id)})

    if response is None:
        return HTTPException(status_code=404)

    return response


@router.get("/task/{task_id}/output", response_model=models.TaskOutput)
async def get_task_output(
    task_id: str, db: AsyncIOMotorDatabase = Depends(get_db_instance)
):
    # Check whether this task is valid
    response = await db.input.find_one({"_id": ObjectId(task_id)})

    if response is None:
        return HTTPException(status_code=404)

    response = await db.output.find_one({"_id": ObjectId(task_id)})

    # Return no content if the task exists but has no output
    if response is None:
        return HTTPException(status_code=201)

    return response