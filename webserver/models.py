from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


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
    _id: str
    precursors: List[Precursor]


class UIControl(BaseModel):
    control_type: str = Field(..., alias="type")
    reference: Reference
    _debug: Dict[str, any]


class WindowEnumeration(BaseModel):
    application_alive: bool
    top_window_texts: List[str]
    found_controls: List[UIControl]


class KernelEvent(BaseModel):
    event_name: str
    params: Dict[str, any]


class KernelEvents(BaseModel):
    net: List[KernelEvent]
    file: List[KernelEvent]
    reg: List[KernelEvent]


class TaskOutput(BaseModel):
    window_enumeration: WindowEnumeration
    kernel_events: KernelEvents