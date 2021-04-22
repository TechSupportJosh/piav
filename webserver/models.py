from typing import Optional, List, Dict, Any
from bson.objectid import ObjectId
from pydantic import BaseModel, Field, validator


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
    precursors: List[Precursor]

    @validator("id", pre=True)  # each_item=True)
    def cast_values(cls, data):
        if isinstance(data, ObjectId):
            return str(data)
        return data

    class Config:
        allow_population_by_field_name = True


class UIControl(BaseModel):
    control_type: str
    reference: Reference
    _debug: Dict[str, any]


class WindowEnumeration(BaseModel):
    application_alive: bool
    program_installed: bool
    top_window_texts: List[str]
    found_controls: List[UIControl]


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

    @validator("id", pre=True)  # each_item=True)
    def cast_values(cls, data):
        if isinstance(data, ObjectId):
            return str(data)
        return data


class LogMessage(BaseModel):
    message: str
    levelno: int