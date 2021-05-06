from settings import get_settings
from bson.objectid import ObjectId
import pydantic
import uvicorn
import os
from colorama import Fore
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.config import LOGGING_CONFIG

from database import close_db, connect_db
from routers import executable, task, vm, queue

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(executable.router)
app.include_router(task.router)
app.include_router(vm.router)
app.include_router(queue.router)

app.mount(
    "/executables",
    StaticFiles(directory=get_settings().upload_directory),
    name="executable files",
)


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


pydantic.json.ENCODERS_BY_TYPE[ObjectId] = str


@app.get("/")
async def root():
    return {"hello": "world"}


@app.on_event("startup")
async def startup():
    await connect_db()


@app.on_event("shutdown")
async def shutdown():
    await close_db()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", log_config=LOGGING_CONFIG)
