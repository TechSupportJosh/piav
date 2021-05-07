import pywinauto.controls.uia_controls as uia_controls
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


def get_control_meta(control):
    return {"text": control.texts()}


def get_control_reference(control):
    """Attempt to create a dictionary which references a control as uniquely as possible.
    While auto_id is usually sufficient, there are some programs which re-use auto IDs.
    """

    if control.automation_id() != "":
        return {"auto_id": control.automation_id()}


interactive_control_types = [uia_controls.ButtonWrapper]


def is_interactive_control(control):
    # Check whether it's not inaccessible due to it's parent being blocked by modal dialog
    window_state = get_window_interaction_state(control.parent())
    if (
        window_state is not None
        and window_state == WindowInteractionState.BlockedByModalWindow
    ):
        return False

    # Check whether it's listed as  a interactive_control_type
    if type(control) not in interactive_control_types:
        return False

    # Check it's parent is not the title bar (minimise, maximise, etc.) and buttons from a scrollbar
    if control.parent().friendly_class_name() in ["ScrollBar", "TitleBar"]:
        return False

    # Although not great, for now, we can attempt to ignore file buttons
    if "Browse" in control.texts():
        return False

    return True


def enumerate_controls(application):
    """Enumerates all interactable controls of an application."""

    enumeration = application.windows(top_level_only=False, enabled_only=True)
    interactive_controls = filter(is_interactive_control, enumeration)

    found_controls = []

    # Now we need to output the list of possible controls
    for control in interactive_controls:
        found_controls.append(
            {
                "type": control.friendly_class_name(),
                "reference": get_control_reference(control),
                "meta": get_control_meta(control),
            }
        )

    return found_controls