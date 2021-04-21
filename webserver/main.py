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
    task = db.input.find_one({"_id": ObjectId(task_id)})
    return task


async def get_queued_task():
    """Returns a single queued task that has not yet started."""
    db = await get_db_instance()
    queue_entry = await db.queue.find_one({"status": "waiting"})
    if queue_entry is None:
        return None
    task = await db.input.find_one({"_id": ObjectId(queue_entry["task_id"])})

    return task


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

    process_logger.info("Allocated task %s to machine ", task["_id"])
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
        + len(task_output.kernel_events.reg)
        + len(task_output.kernel_events.net),
    )

    # TODO: Add parsing back

    return {}


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
