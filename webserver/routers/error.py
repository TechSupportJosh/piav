from typing import List
from bson.objectid import ObjectId
import models
from database import get_db_instance
from fastapi import APIRouter
from fastapi.params import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
import datetime

router = APIRouter(
    prefix="/error",
    tags=["Error Related Endpoints"],
)


async def update_task_status(db: AsyncIOMotorDatabase, task_id: ObjectId, status: str):
    await db.input.update_one({"_id": task_id}, {"$set": {"status": status}})


@router.get(
    "/",
    responses={
        200: {
            "description": "Errors are returned.",
            "model": List[models.ErrorMessage],
        },
    },
    name="Retrieve all errors",
)
async def get_task_errors(db: AsyncIOMotorDatabase = Depends(get_db_instance)):
    errors = await db.error.find().to_list(length=None)
    return errors


@router.get(
    "/{task_id}",
    responses={
        200: {
            "description": "Errors for a specific task are returned.",
            "model": List[models.ErrorMessage],
        },
    },
    name="Retrieve all errors",
)
async def get_task_error(
    task_id: str, db: AsyncIOMotorDatabase = Depends(get_db_instance)
):
    errors = await db.error.find({"task_id": task_id}).to_list(length=None)
    return errors


@router.post(
    "/{task_id}",
    responses={
        200: {"description": "Successfully stored error message.", "model": {}},
    },
    name="Process VM Error",
)
async def task_error(
    task_id: str,
    request: models.ErrorMessage,
    db: AsyncIOMotorDatabase = Depends(get_db_instance),
):
    """Process a error message from a VM."""

    await db.error.insert_one(
        {
            "time": int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp()),
            "task_id": task_id,
            "stack_trace": request.stack_trace.strip(),
        }
    )
    await update_task_status(db, ObjectId(task_id), "failed")
    return {}
