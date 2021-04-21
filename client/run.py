import json
import sys
import time
import subprocess
import os
import signal
import psutil
from enum import IntEnum
import pywinauto
import pywinauto.controls.uia_controls as uia_controls
from windows_tools.installed_software import get_installed_software
from WindowInteractionState import WindowInteractionState, get_window_interaction_state

import logging
import requests
from JSONHTTPHandler import JSONHTTPHandler

API_URL = "http://172.17.48.1:8000"

# Request task ID
# TODO: Add error handling
response = requests.post(API_URL + "/request_task")

if response.status_code == 404:
    print("No task to do")
    sys.exit(-1)

task_input = response.json()

logger = logging.getLogger("logger")
logger.setLevel(logging.DEBUG)

http_handler = JSONHTTPHandler("http://172.17.48.1:8000", f"/log/{task_input['_id']}")
http_handler.setLevel(logging.DEBUG)
logger.addHandler(http_handler)

logger.info("Received task, starting application...")

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

print(application)

# Now attempt to find a top window, if not, we may have the same case as above
try:
    top_window = application.top_window()
except RuntimeError:
    print("Failed to find top window, attempting to reconnect to the application")

    # If the application has already exited, they may have spawned another process, therefore we'll try and find the
    # application again before erroring
    application.connect(best_match=application_name)

fibratus_process = None

# Delete old fibratus output if it exists
try:
    os.remove("fibratus_capture.json")
except FileNotFoundError:
    pass

# Kill old fibratus process
for proc in psutil.process_iter():
    if proc.name() == "fibratus.exe":
        proc.kill()

# Now execute task_input
for index, stage in enumerate(task_input["precursors"]):
    print(
        "Now executing precursor {} of {}.".format(
            index + 1, len(task_input["precursors"])
        )
    )

    # If this is the final precursor, then we should start tracking registry changes
    if index + 1 == len(task_input["precursors"]):
        print("Starting fibratus capturing...")
        fibratus_process = subprocess.Popen(
            [
                "fibratus",
                "run",
                "ps.name = 'FileZilla.exe' and kevt.category in ('net','file','registry')",
                "-f",
                "capture",
                "--filament.path",
                os.getcwd(),
            ],
            cwd=os.getcwd(),
        )

    # Find the control referenced
    control_reference = application.window(**stage["reference"], top_level_only=False)

    timeout = stage.get("wait_for_element_timeout", 0)
    try:
        control = control_reference.wait("visible", timeout=timeout)
    except pywinauto.timings.TimeoutError:
        print(
            "Control {} was not available after {} seconds.".format(
                stage["reference"], timeout
            )
        )
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
        print(
            "Waiting for progress bar to reach 100%, current value: ",
            progress_bar_value,
        )
        time.sleep(5)

if fibratus_process is not None:
    print("Stopping fibratus...")
    # Send CTRL+C to the fibratus process to stop it
    # However, sending CTRL+C to this subprocess also sends it to this process
    # Therefore, we should wait for the signal, trap it and ignore it. The subprocess
    # will be killed however we will continue to exist
    try:
        fibratus_process.send_signal(signal.CTRL_C_EVENT)
        time.sleep(60)
    except KeyboardInterrupt:
        print("Captured KeyboardInterrupt (SIGINT)")

    time.sleep(15)
    print("Fibratus stopped")

interactive_control_types = [uia_controls.ButtonWrapper]


def is_interactive_control(control):
    print(control)
    print(repr(control))

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


def get_debug_info(control):
    return {"text": control.texts()}


def attempt_unique_id(control):
    if control.automation_id() != "":
        return {"auto_id": control.automation_id()}


# Now we've executed all input precusors, check whether the application is still available
# For example, clicking a "Cancel" button may close down the application
if not application.is_process_running():
    print("Application's process has ended.")

    output = {
        "application_alive": False,
        "program_installed": False,
    }

    # Check whether the program has successfully installed, or whether it's just been closed...
    output["program_installed"] = full_install_name in map(
        lambda software: software["name"], get_installed_software()
    )
else:
    print("Starting window enumeration...")
    enumeration = application.windows(top_level_only=False, enabled_only=True)
    interactive_controls = filter(is_interactive_control, enumeration)
    print("Finished window enumeration...")

    output = {
        "application_alive": True,
        "top_window_texts": sorted(application.top_window().children_texts()),
        "found_controls": [],
        "program_installed": False,
    }

    # Now we need to output the list of possible controls
    for control in interactive_controls:
        control_type = None

        output["found_controls"].append(
            {
                "control_type": control.friendly_class_name(),
                "reference": attempt_unique_id(control),
                "_debug": get_debug_info(control),
            }
        )

    # Finally, kill the application
    application.kill(soft=False)

fibratus_output = {"registry": [], "file": [], "net": []}

try:
    with open("fibratus_capture.json", "r") as fibratus_output_file:
        fibratus_output = json.load(fibratus_output_file)
    os.remove("fibratus_output.json")
except FileNotFoundError:
    print("No Fiberatus output found")

response = requests.post(
    API_URL + "/submit_task/" + task_input["_id"],
    json={"window_enumeration": output, "kernel_events": fibratus_output},
)

print(response.text)

if response.status_code == 200:
    print("Successfully posted data")