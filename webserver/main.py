import logging
import typing

import uvicorn
from bson import ObjectId
from colorama import Fore
from colorama import init as colorama_init
from fastapi import FastAPI, HTTPException, responses
from uvicorn.config import LOGGING_CONFIG

import models
from logs import ClientFormatter, CustomFormatter, LogEndpointFilter

from database import close_db, connect_db, get_db_instance

from output_handler import get_branches

colorama_init()

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

app = FastAPI()

# https://github.com/encode/uvicorn/blob/master/uvicorn/config.py#L86
# https://docs.python.org/3/library/logging.config.html#user-defined-objects
LOGGING_CONFIG["filters"] = {"logendpointfilter": {"()": "logs.LogEndpointFilter"}}
# Override fastapi's formatters to use our pretty format
LOGGING_CONFIG["formatters"] = {
    "default": {
        "()": "uvicorn.logging.DefaultFormatter",
        "fmt": "[%(asctime)s] <"
        + Fore.CYAN
        + "uvicorn"
        + Fore.RESET
        + ">: %(message)s",
        "use_colors": None,
        "datefmt": "%H:%M:%S",
    },
    "access": {
        "()": "uvicorn.logging.AccessFormatter",
        "fmt": "[%(asctime)s] <"
        + Fore.CYAN
        + "http"
        + Fore.RESET
        + '>: %(client_addr)s - "%(request_line)s" %(status_code)s',
        "datefmt": "%H:%M:%S",
    },
}
LOGGING_CONFIG["handlers"]["access"]["filters"] = ["logendpointfilter"]


@app.get("/")
async def root():
    return {"hello": "world"}


async def get_task(task_id: str):
    """Returns the task with the ID task_id"""
    db = await get_db_instance()
    task = await db.input.find_one({"_id": ObjectId(task_id)})
    return task


async def insert_task(task):
    """Inserts a task"""
    db = await get_db_instance()
    task = await db.input.insert_one(task)
    return task


async def get_queued_task():
    """Returns a single queued task that has not yet started and will mark it as started."""
    db = await get_db_instance()
    queue_entry = await db.queue.find_one({"status": "waiting"})
    if queue_entry is None:
        return None

    await update_queue_status(queue_entry["_id"], "started")
    task = await db.input.find_one({"_id": queue_entry["_id"]})

    return task


async def update_queue_status(task_id: str, status: str):
    db = await get_db_instance()
    await db.queue.update_one({"_id": ObjectId(task_id)}, {"$set": {"status": status}})


async def queue_entry(task_id: str):
    db = await get_db_instance()
    await db.queue.insert_one({"_id": ObjectId(task_id), "status": "waiting"})


async def insert_output(task_id: str, task_output: models.TaskOutput):
    db = await get_db_instance()
    output = {"_id": ObjectId(task_id)}
    output.update(task_output.dict())
    await db.output.insert_one(output)


async def insert_same_output(task_id: str, duplicate_output_id: str):
    db = await get_db_instance()
    output = {"_id": ObjectId(task_id), "same_as": duplicate_output_id}
    await db.output.insert_one(output)


async def find_duplicate_result(task_output: models.TaskOutput):
    db = await get_db_instance()
    window_enumeration = task_output.window_enumeration.dict()
    print(window_enumeration)
    result = await db.output.find_one(
        {
            "top_window_texts": window_enumeration["top_window_texts"],
            "found_controls": window_enumeration["found_controls"],
        }
    )

    return result


async def initialise_task():
    db = await get_db_instance()
    response = await db.input.insert_one({"precursors": []})
    # Add our newest one to the queue
    await queue_entry(str(response.inserted_id))


@app.post(
    "/request_task",
    response_model=models.Task,
    responses={
        200: {"description": "Successfully retrieved a queued task."},
        404: {"description": "No queued tasks found."},
    },
    name="Request queued task",
)
async def request_task():
    """Retrieves a task from the task queue. This is called by VMs when they first boot."""
    task = await get_queued_task()

    # If no task is currently waiting, just return 404
    if task is None:
        process_logger.debug("Task requested however no tasks are currently queued.")
        raise HTTPException(status_code=404)

    process_logger.info("Allocated task %s to machine", task["_id"])
    return task


@app.post(
    "/submit_task/{task_id}",
    responses={
        200: {"description": "Successfully saved task output.", "model": {}},
        404: {"description": "Task with this ID was not found."},
    },
    name="Submit task output",
)
async def submit_task(task_id: str, task_output: models.TaskOutput):
    """Stores the result from executing the task ID. This is called by VMs when they finish."""
    task = await get_task(task_id)

    # If no task is currently waiting, just return 404
    if task is None:
        process_logger.warn(
            "Output of task %s was submitted however no tasks exist with that ID.",
            task_id,
        )
        raise HTTPException(status_code=404)

    process_logger.info(
        "Task %s has been completed. Kernel events received: %d",
        task_id,
        len(task_output.kernel_events.file)
        + len(task_output.kernel_events.registry)
        + len(task_output.kernel_events.net),
    )

    # Mark queue entry as done
    await update_queue_status(task_id, "waiting")

    # Only consider duplicate outputs if they're alive
    if task_output.window_enumeration.application_alive:
        # Detect whether this output is identical to another output, in which case we don't need to process it
        duplicate_result = await find_duplicate_result(task_output)

        if duplicate_result is not None:
            # This output is identical to another output, indiciating that maybe we've hit a "back" button or cancel on a dialog.
            # Rather than inserting the output, insert a entry to the already discovered one
            await insert_same_output(task_id, str(duplicate_result["_id"]))

            process_logger.info(
                "Output of task %s is the same as %s, inserting same_as entry",
                task_id,
                str(duplicate_result["_id"]),
            )

            return {}

    # Insert output into the database
    await insert_output(task_id, task_output)

    # If the application has died, we can end here
    if not task_output.window_enumeration.application_alive:
        if task_output.window_enumeration.program_installed:
            process_logger.info(
                "Application successfully installed after task %s", task_id
            )
        else:
            process_logger.info("Application process ended after task %s", task_id)

        return {}

    task_input = await get_task(task_id)

    task_ids = []

    process_logger.info("Calculating branches for %s", task_id)

    for branch in get_branches(task_input, task_output.dict()["window_enumeration"]):
        result = await insert_task(branch)
        task_ids.append(result.inserted_id)
        process_logger.info(
            "Queuing task %s, branched from %s", result.inserted_id, task_id
        )
        await queue_entry(result.inserted_id)

    return {}


@app.post("/initialise")
async def initialise():
    # TODO: Add form feature so they can submit a new exe
    await initialise_task()


@app.post("/log/{task_id}")
async def task_log(task_id: str, request: models.LogMessage):
    """Log"""
    task_logger.log(request.levelno, request.message, extra={"task_id": task_id})
    return {}


@app.on_event("startup")
async def startup():
    await connect_db()


@app.on_event("shutdown")
async def shutdown():
    await close_db()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", log_config=LOGGING_CONFIG)
