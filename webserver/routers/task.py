from typing import List
import models
from bson.objectid import ObjectId
from database import get_db_instance
from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(
    prefix="/task",
    tags=["Task Endpoints"],
)


@router.get(
    "/input",
    responses={
        200: {
            "description": "Task inputs are returned, however their actions are not resolved.",
            "model": List[models.Task],
        },
    },
    name="Retrieve all task inputs",
)
async def get_task_inputs(db: AsyncIOMotorDatabase = Depends(get_db_instance)):
    tasks = await db.input.find().to_list(length=None)
    return tasks


@router.get(
    "/input/{task_id}",
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
        raise HTTPException(status_code=404, detail="Task does not exist.")

    # We need to retrieve the setup_actions by continously retrieving the previous task id
    setup_actions = []

    resolve_task = response
    while True:
        if resolve_task["parent_task"] is None:
            response["executable_id"] = resolve_task["executable_id"]
            break

        resolve_task = await db.input.find_one(
            {"_id": ObjectId(resolve_task["parent_task"])}
        )

        # Prepend the parent_task's actions
        if resolve_task["actions"] is not None:
            setup_actions = resolve_task["actions"] + setup_actions

    response["setup_actions"] = setup_actions

    return response


@router.get(
    "/output/{task_id}",
    responses={
        200: {"description": "Task output is returned.", "model": models.TaskOutput},
        202: {"description": "Task exists but has not finished."},
        404: {"description": "Task does not exist."},
    },
    name="Retrieve task output",
)
async def get_task_output(
    task_id: str, db: AsyncIOMotorDatabase = Depends(get_db_instance)
):
    # Check whether this task is valid
    response = await db.input.find_one({"_id": ObjectId(task_id)})

    if response is None:
        raise HTTPException(status_code=404, detail="Task does not exist.")

    response = await db.output.find_one({"_id": ObjectId(task_id)}, {"_id": 0})

    # Return no content if the task exists but has no output
    if response is None:
        raise HTTPException(status_code=202, detail="Task exists but has not finished.")

    return response


@router.get(
    "/output",
    responses={
        200: {
            "description": "Task outputs is returned.",
            "model": List[models.TaskOutput],
        },
    },
    name="Retrieve all task outputs",
)
async def get_task_outputs(
    kernel_events: bool = True,
    window_enumeration: bool = True,
    db: AsyncIOMotorDatabase = Depends(get_db_instance),
):
    projection = {"_id": 1, "same_as": 1}

    print(window_enumeration)
    if window_enumeration:
        projection["window_enumeration"] = 1
    if kernel_events:
        projection["kernel_events"] = 1

    tasks = await db.output.find({}, projection).to_list(length=None)
    return tasks
