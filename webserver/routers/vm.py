import logging
from logs import ClientFormatter, CustomFormatter
from typing import List

import models
from bson.objectid import ObjectId
from database import get_db_instance
from fastapi import APIRouter, HTTPException, Response
from fastapi.params import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from output_handler import get_branches

router = APIRouter(
    prefix="/vm",
    tags=["VM Related Endpoints"],
)

# Output logger
process_logger = logging.getLogger("processor")
process_logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())
process_logger.addHandler(ch)

# Task logger
task_logger = logging.getLogger("task")
task_logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(ClientFormatter())
task_logger.addHandler(ch)


async def update_queue_status(db: AsyncIOMotorDatabase, task_id: str, status: str):
    await db.queue.update_one({"_id": ObjectId(task_id)}, {"$set": {"status": status}})


@router.post(
    "/request_task",
    response_model=models.Task,
    responses={
        200: {"description": "Successfully retrieved a queued task."},
        404: {"description": "No queued tasks found."},
    },
    name="Request queued task",
)
async def request_task(db: AsyncIOMotorDatabase = Depends(get_db_instance)):
    """Retrieves a task from the task queue. This is called by VMs when they first boot."""
    queue_entry = await db.queue.find_one({"status": "waiting"})

    # If no task is currently waiting, just return 404
    if queue_entry is None:
        process_logger.debug("Task requested however no tasks are currently queued.")
        raise HTTPException(status_code=404, detail="No queued tasks found.")

    await update_queue_status(db, queue_entry["_id"], "started")
    task = await db.input.find_one({"_id": queue_entry["_id"]})

    process_logger.info("Allocated task %s to machine", task["_id"])
    return task


@router.post(
    "/submit_task/{task_id}",
    responses={
        200: {"description": "Successfully saved task output.", "model": {}},
        404: {"description": "Task with this ID was not found."},
    },
    name="Submit task output",
)
async def submit_task(
    task_id: str,
    task_output: models.TaskOutput,
    db: AsyncIOMotorDatabase = Depends(get_db_instance),
):
    """Stores the result from executing the task ID. This is called by VMs when they finish."""
    task = await db.input.find_one({"_id": ObjectId(task_id)})

    # If no task is currently waiting, just return 404
    if task is None:
        process_logger.warn(
            "Output of task %s was submitted however no tasks exist with that ID.",
            task_id,
        )
        raise HTTPException(status_code=404, detail="Task with this ID was not found.")

    process_logger.info(
        "Task %s has been completed. Kernel events received: %d",
        task_id,
        len(task_output.kernel_events.file)
        + len(task_output.kernel_events.registry)
        + len(task_output.kernel_events.net),
    )

    # Mark queue entry as done
    await update_queue_status(db, task_id, "waiting")

    # Only consider duplicate outputs if they're alive
    if task_output.window_enumeration.application_alive:
        # Detect whether this output is identical to another output, in which case we don't need to process it
        window_enumeration = task_output.window_enumeration.dict()
        duplicate_result = await db.output.find_one(
            {
                "top_window_texts": window_enumeration["top_window_texts"],
                "found_controls": window_enumeration["found_controls"],
            }
        )

        if duplicate_result is not None:
            # This output is identical to another output, indiciating that maybe we've hit a "back" button or cancel on a dialog.
            # Rather than inserting the output, insert a entry to the already discovered one
            await db.output.insert_one(
                {"_id": ObjectId(task_id), "same_as": str(duplicate_result["_id"])}
            )

            process_logger.info(
                "Output of task %s is the same as %s, inserting same_as entry",
                task_id,
                str(duplicate_result["_id"]),
            )

            return {}

    # Convert task output to dict and insert _id
    output = {"_id": ObjectId(task_id)}
    output.update(task_output.dict())

    await db.output.insert_one(output)

    # If the application has died, we can end here
    if not task_output.window_enumeration.application_alive:
        if task_output.window_enumeration.program_installed:
            process_logger.info(
                "Application successfully installed after task %s", task_id
            )
        else:
            process_logger.info("Application process ended after task %s", task_id)

        return {}

    task_input = await db.input.find_one({"_id": ObjectId(task_id)})

    task_ids = []

    process_logger.info("Calculating branches for %s", task_id)

    for branch in get_branches(task_input, task_output.dict()["window_enumeration"]):
        result = await db.input.insert_one(branch)
        task_ids.append(result.inserted_id)
        process_logger.info(
            "Queuing task %s, branched from %s", result.inserted_id, task_id
        )
        await db.queue.insert_one({"_id": result.inserted_id, "status": "waiting"})

    return {}


@router.post(
    "/log/{task_id}",
    responses={
        200: {"description": "Successfully sent log.", "model": {}},
    },
    name="Process VM Log",
)
async def task_log(task_id: str, request: models.LogMessage):
    """Process a log message from a VM."""
    task_logger.log(request.levelno, request.message, extra={"task_id": task_id})
    return {}
