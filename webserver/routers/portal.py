import base64
import binascii
import os
import logging
import hashlib
from logs import CustomFormatter
from typing import List

import models
from bson.objectid import ObjectId
from database import get_db_instance
from fastapi import APIRouter, HTTPException, Response
from fastapi.params import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from settings import get_settings

router = APIRouter(
    prefix="/portal",
    tags=["Portal Related Endpoints"],
)

settings = get_settings()

# Portal logger
portal_logger = logging.getLogger("portal")
portal_logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())
portal_logger.addHandler(ch)


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
    "/task/{task_id}/output",
    responses={
        200: {"description": "Task output is returned.", "model": models.TaskOutput},
        202: {"description": "Task exists but has not finished."},
        404: {"description": "Task does not exist."},
    },
    name="Retrieve task output",
)
@router.get("/task/{task_id}/output")
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
    "/executable",
    response_model=List[models.Executable],
    description="Retrieve all executables.",
)
async def get_executables(db: AsyncIOMotorDatabase = Depends(get_db_instance)):
    executables = await db.executable.find().to_list(length=None)
    return executables


@router.get(
    "/executable/{executable_id}",
    response_model=models.Executable,
    description="Retrieve a executable.",
)
async def get_executable(
    executable_id: str, db: AsyncIOMotorDatabase = Depends(get_db_instance)
):
    executable = await db.executable.find_one({"_id": ObjectId(executable_id)})
    return executable


@router.post(
    "/executable",
    responses={
        201: {
            "description": "PIAV has been setup with this executable.",
            "model": models.Executable,
        },
        409: {"description": "An installer already exists with this name."},
    },
    name="Start PIAV with a new executable",
    status_code=201,
)
async def setup_executable(
    request: models.SetupExecutable, db: AsyncIOMotorDatabase = Depends(get_db_instance)
):
    # Decode the installer and save it
    try:
        installer_bytes = base64.b64decode(request.installer)
    except binascii.Error:
        raise HTTPException(status_code=422, detail="Invalid installer base64.")

    # Check whether an installer already exists with this name
    file_path = os.path.join(settings.upload_directory, request.installer_name)
    if os.path.exists(file_path):
        raise HTTPException(
            status_code=409, detail="An installer already exists with this name."
        )

    with open(file_path, "wb") as installer_file:
        installer_file.write(installer_bytes)

    sha256sum = hashlib.sha256(installer_bytes).hexdigest()
    portal_logger.info(
        "Saved new exectuable to %s, SHA256sum: %s",
        file_path,
        sha256sum,
    )

    executable_result = await db.executable.insert_one(
        {
            "file_name": request.installer_name,
            "file_sha256sum": sha256sum,
            "application_name": request.application_name,
            "full_installation_name": request.full_installation_name,
        }
    )

    # Create the base task
    task_result = await db.input.insert_one(
        {
            "executable_id": str(executable_result.inserted_id),
            "parent_task": None,
            "setup_actions": [],
            "actions": [],
        }
    )

    # Create queue entry
    await db.queue.insert_one({"_id": task_result.inserted_id, "status": "waiting"})

    sha256sum = hashlib.sha256(installer_bytes).hexdigest()
    portal_logger.info("Added %s to the queue", request.application_name)

    executable = await db.executables.find_one({"_id": executable_result.inserted_id})

    return executable