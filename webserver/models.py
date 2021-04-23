from typing import Optional, List, Dict, Any
from bson.objectid import ObjectId
from pydantic import BaseModel, Field, validator
from pydantic.main import BaseConfig
import pydantic
from bson.objectid import ObjectId


class Reference(BaseModel):
    auto_id: str


class Action(BaseModel):
    method: str
    parameters: Dict[str, Any]


class Precursor(BaseModel):
    reference: Reference
    wait_for_element_timeout: int = 15
    delay_after_action: int = 10

    action: Action


class Task(BaseModel):
    id: str = Field(alias="_id")
    executable_id: str

    precursors: List[Precursor]

    @validator("id", pre=True, each_item=True)
    def convert_id(cls, value):
        if isinstance(value, ObjectId):
            return str(value)
        return value


class UIControl(BaseModel):
    control_type: str
    reference: Reference
    _debug: Dict[str, any]


class WindowEnumeration(BaseModel):
    application_alive: bool
    program_installed: bool
    base64_images: List[str]
    top_window_texts: Optional[List[str]]
    found_controls: Optional[List[UIControl]]


class KernelEvent(BaseModel):
    event_name: str
    params: Dict[str, Any]


class KernelEvents(BaseModel):
    net: List[KernelEvent]
    file: List[KernelEvent]
    registry: List[KernelEvent]


class TaskOutput(BaseModel):
    window_enumeration: WindowEnumeration
    kernel_events: KernelEvents


class QueueEntry(BaseModel):
    id: str = Field(alias="_id")
    status: str

    @validator("id", pre=True, each_item=True)
    def convert_id(cls, value):
        if isinstance(value, ObjectId):
            return str(value)
        return value


class LogMessage(BaseModel):
    message: str
    levelno: int


class SetupExecutable(BaseModel):
    application_name: str
    full_installation_name: str
    installer: str
    installer_name: str


class Executable(BaseModel):
    id: str = Field(alias="_id")
    file_name: str
    file_sha256sum: str
    application_name: str
    full_installation_name: str

    @validator("id", pre=True, each_item=True)
    def convert_id(cls, value):
        if isinstance(value, ObjectId):
            return str(value)
        return value
