import logging
from typing import List
import hashlib
import base64
import binascii
import models
import os
from bson.objectid import ObjectId
from database import get_db_instance
from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from logs import CustomFormatter
from motor.motor_asyncio import AsyncIOMotorDatabase
from settings import get_settings

router = APIRouter(
    prefix="/executable",
    tags=["Executable Endpoints"],
)

logger = logging.getLogger("executable")
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())
logger.addHandler(ch)

settings = get_settings()


@router.get(
    "/",
    response_model=List[models.Executable],
    description="Retrieve all executables.",
)
async def get_executables(db: AsyncIOMotorDatabase = Depends(get_db_instance)):
    executables = await db.executable.find().to_list(length=None)
    return executables


@router.get(
    "/{executable_id}",
    response_model=models.Executable,
    description="Retrieve a executable.",
)
async def get_executable(
    executable_id: str, db: AsyncIOMotorDatabase = Depends(get_db_instance)
):
    executable = await db.executable.find_one({"_id": ObjectId(executable_id)})
    return executable


@router.post(
    "/",
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
    logger.info(
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
    logger.info("Added %s to the queue", request.application_name)

    executable = await db.executables.find_one({"_id": executable_result.inserted_id})

    return executable
