from enum import IntEnum
from pywinauto.uia_defines import NoPatternInterfaceError

# pywinauto does not have this natively implemented, see pywinauto notes/WindowInteractionState.txt for explanation
class WindowInteractionState(IntEnum):
    Running = 0
    Closing = 1
    ReadyForUserInteraction = 2
    BlockedByModalWindow = 3
    NotResponding = 4

def get_window_interaction_state(control):
    try:
        return control.iface_window.CurrentWindowInteractionState
    except NoPatternInterfaceError:
        return None