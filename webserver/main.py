from fastapi import FastAPI, HTTPException, responses
from database import input_collection, output_collection, queue_collection
from bson import ObjectId
import uvicorn
from uvicorn.config import LOGGING_CONFIG
import models

import logging
from CustomFormatter import CustomFormatter

from colorama import init as colorama_init, Fore

colorama_init()

# Setup our task logger
task_logger = logging.getLogger("tasks")
task_logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())
task_logger.addHandler(ch)

app = FastAPI()

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


@app.get("/")
async def root():
    return {"hello": "world"}


async def get_task(task_id: str):
    """Returns the task with the ID task_id"""
    return await input_collection.find_one({"_id": ObjectId(task_id)})


async def get_queued_task():
    """Returns a single queued task that has not yet started."""
    return await queue_collection.find_one({"status": "waiting"})


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
        task_logger.debug("Task requested however no tasks are currently queued.")
        raise HTTPException(status_code=404)

    task_logger.info("Allocated task %s to machine ", task["_id"])
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
        task_logger.warn(
            "Output of task %s was submitted however no tasks exist with that ID.",
            task_id,
        )
        raise HTTPException(status_code=404)

    task_logger.info(
        "Task %s has been completed. Kernel events received: %d",
        task_id,
        len(task_output.kernel_events.file)
        + len(task_output.kernel_events.reg)
        + len(task_output.kernel_events.net),
    )

    # TODO: Add parsing back

    return {}


if __name__ == "__main__":
    uvicorn.run(app, log_config=LOGGING_CONFIG)