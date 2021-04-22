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


@router.get(
    "/queue",
    response_model=List[models.QueueEntry],
    description="Retrieve all tasks in queue.",
)
async def get_queue(db: AsyncIOMotorDatabase = Depends(get_db_instance)):
    tasks = await db.queue.find().to_list(length=None)
    return tasks


@router.get(
    "/task/{task_id}/input",
    responses={
        200: {"description": "Task input is returned.", "model": models.Task},
        404: {"description": "Task does not exist.", "model": None},
    },
    name="Retrieve task input",
)
async def get_task_input(
    task_id: str, db: AsyncIOMotorDatabase = Depends(get_db_instance)
):
    response = await db.input.find_one({"_id": ObjectId(task_id)})

    if response is None:
        return HTTPException(status_code=404)

    return response


@router.get(
    "/task/{task_id}/output",
    responses={
        200: {"description": "Task output is returned.", "model": models.TaskOutput},
        201: {"description": "Task exists but has not finished.", "model": None},
        404: {"description": "Task does not exist.", "model": None},
    },
    name="Retrieve task output",
)
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


@router.post("/initialise")
async def initialise(db: AsyncIOMotorDatabase = Depends(get_db_instance)):
    # TODO: Add form feature so they can submit a new exe
    result = await db.input.insert_one({"precursors": []})
    await db.queue.insert_one({"_id": result.inserted_id, "status": "waiting"})
