import json
import sys
import time
from enum import IntEnum
import pywinauto
import pywinauto.controls.uia_controls as uia_controls
from pywinauto.uia_defines import NoPatternInterfaceError
from windows_tools.installed_software import get_software_list

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

application_name = "FileZilla"
full_install_name = "FileZilla Client 3.52.2"
application = pywinauto.Application(backend="uia")
application.start(r"C:\Users\piav\Documents\FileZilla.exe")

try:
    application.wait_for_process_exit(timeout=3)
    
    # If the application has already exited, they may have spawned another process, therefore we'll try and find the
    # application again before erroring
    application.connect(best_match=application_name)

    print(application)
except pywinauto.timings.TimeoutError:
    print("Process is still alive.")

# Now attempt to find a top window, if not, we may have the same case as above
try:
    top_window = application.top_window()
except RuntimeError:
    print("Failed to find top window, attempting to reconnect to the application")

    # If the application has already exited, they may have spawned another process, therefore we'll try and find the
    # application again before erroring
    application.connect(best_match=application_name)


# Load our input JSON before enumerating
with open("../server/input/{}.json".format(sys.argv[1]), "r") as task_input_json:
    task_input = json.load(task_input_json)

# Now execute task_input 
for index, stage in enumerate(task_input["precursors"]):
    print("Now executing precursor {} of {}.".format(index + 1, len(task_input["precursors"])))

    # Find the control referenced
    control_reference = application.window(**stage["reference"], top_level_only=False)

    timeout = stage.get("wait_for_element_timeout", 0)
    try:
        control = control_reference.wait("visible", timeout=timeout)
    except pywinauto.timings.TimeoutError:
        print("Control {} was not available after {} seconds.".format(stage["reference"], timeout))
        # TODO: Error handling for when it doesn't go as expected...
    
    # Now run the action defined on the control (executes control.method(parameters))
    if stage["action"]["method"] == "set_toggle_state":
        current_state = bool(control.get_toggle_state()) 
        desired_state = stage["action"]["parameters"]["state"]
        
        if current_state != desired_state:
            control.click()
    else:
        getattr(control, stage["action"]["method"])(**stage["action"]["parameters"])

    delay = stage.get("delay_after_action", 0)
    print("Waiting for {} seconds.".format(delay))
    time.sleep(delay)

# Now check whether there's a progress bar on the screen (for example, extracting resources)
# before enumerating options
progress_bar = application.window(control_type="ProgressBar", top_level_only=False)
if progress_bar.exists():
    # Resolve the reference to a ProgressBar object
    progress_bar = progress_bar.wait("exists")

    # Wait until value is 100%
    progress_bar_value = progress_bar.legacy_properties().get("Value", "100%")
    while progress_bar_value != "100%":
        progress_bar_value = progress_bar.legacy_properties().get("Value", "100%")
        print("Waiting for progress bar to reach 100%, current value: ", progress_bar_value)
        time.sleep(5)

interactive_control_types = [uia_controls.ButtonWrapper]

def is_interactive_control(control):
    print(control)
    print(repr(control))
    
    # Check whether it's not inaccessible due to it's parent being blocked by modal dialog
    window_state = get_window_interaction_state(control.parent())
    if window_state is not None and window_state == WindowInteractionState.BlockedByModalWindow:
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

def get_debug_info(control):
    return {
        "text": control.texts()
    }

def attempt_unique_id(control):
    if control.automation_id() != "":
        return {
            "auto_id": control.automation_id()
        }

# Now we've executed all input precusors, check whether the application is still available
# For example, clicking a "Cancel" button may close down the application
if not application.is_process_running():
    print("Application's process has ended.")

    output = {
        "input_id": task_input["_id"],
        "application_alive": False,
        "program_installed": False
    }

    # Check whether the program has successfully installed, or whether it's just been closed...
    output["program_installed"] = full_install_name in map(lambda software: software["name"], get_software_list())
else:
    print("Starting window enumeration...")
    enumeration = application.windows(top_level_only=False, enabled_only=True)
    interactive_controls = filter(is_interactive_control, enumeration)
    print("Finished window enumeration...")

    output = {
        "input_id": task_input["_id"],
        "application_alive": True,
        "top_window_texts": sorted(application.top_window().children_texts()),
        "found_controls": []
    }

    # Now we need to output the list of possible controls
    for control in interactive_controls:
        control_type = None

        output["found_controls"].append({
            "type": control.friendly_class_name(),
            "reference": attempt_unique_id(control),
            "_debug": get_debug_info(control)
        })

    # Finally, kill the application
    application.kill(soft=False)

# Write our output
with open(f"../server/output/{task_input['_id']}.json", "w") as task_output_file:
    json.dump(output, task_output_file, indent=2)

# Once our application has been killed, create a .complete file to inform the server we've finished
with open(f"../server/output/{task_input['_id']}.complete", "w") as complete_file:
    complete_file.write("Done!")