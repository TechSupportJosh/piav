from io import BytesIO
import json
import sys
import time
import subprocess
import os
import signal
import psutil
import base64
from enum import IntEnum
import pywinauto
import pywinauto.controls.uia_controls as uia_controls
from windows_tools.installed_software import get_installed_software
from WindowInteractionState import WindowInteractionState, get_window_interaction_state

import logging
import requests
from JSONHTTPHandler import JSONHTTPHandler, StyleAdapter

BASE_API_URL = "http://172.19.112.1:8000"
API_URL = BASE_API_URL + "/vm"
failed_requests = 0

# Request task ID
while True:
    if failed_requests:
        # Wait a maximum of 256 seconds
        timeout = min(2 ** failed_requests, 256)
        print("Waiting {} seconds before trying again...".format(timeout))
        time.sleep(timeout)

    try:
        response = requests.post(API_URL + "/request_task", timeout=10)
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        print("Unable to connect to server...")
        failed_requests += 1
        continue

    if response.status_code == 404:
        print("No tasks are current queued...")
        failed_requests += 1
        continue

    # Otherwise we have successfully retrieved a task
    break

task_input = response.json()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("logger")

http_handler = JSONHTTPHandler(API_URL, "/log/" + task_input["_id"])
http_handler.setLevel(logging.DEBUG)

logger.addHandler(http_handler)

logger = StyleAdapter(logger)

logger.info("Received task, retrieving application details...")

executable = requests.get(API_URL + "/executable/" + task_input["_id"]).json()

logger.info("Retrieved application, downloading executable...")

executable_file_path = "C:\\Users\\piav\\Documents\\{}".format(executable["file_name"])
with open(executable_file_path, "wb") as executable_file:
    executable_file.write(
        requests.get(BASE_API_URL + "/executables/" + executable["file_name"]).content
    )

logger.info("Executable downloaded, starting...")

application = pywinauto.Application(backend="uia")
application.start(executable_file_path)

base64_images = []


def get_screenshot_base64():
    # Take image of the current top window
    # https://stackoverflow.com/a/31826470
    image = application.top_window().capture_as_image()
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


try:
    application.wait_for_process_exit(timeout=3)

    # If the application has already exited, they may have spawned another process, therefore we'll try and find the
    # application again before erroring
    application.connect(best_match=executable["application_name"])

except pywinauto.timings.TimeoutError:
    logger.debug("Process is still alive.")

# Now attempt to find a top window, if not, we may have the same case as above
try:
    top_window = application.top_window()
except RuntimeError:
    logger.info("Failed to find top window, attempting to reconnect to the application")

    # If the application has already exited, they may have spawned another process, therefore we'll try and find the
    # application again before erroring
    application.connect(best_match=executable["application_name"])

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

# Take a picture of the application as it's started
base64_images.append(get_screenshot_base64())

# Now execute task_input
for index, stage in enumerate(task_input["precursors"]):
    logger.info(
        "Now executing precursor {} of {}.", index + 1, len(task_input["precursors"])
    )

    # If this is the final precursor, then we should start tracking registry changes
    if index + 1 == len(task_input["precursors"]):
        logger.info("Starting fibratus capturing...")
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
        logger.warn(
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
    logger.debug("Waiting for {} seconds.", delay)
    time.sleep(delay)

    # After running this precursor, take a screenshot
    base64_images.append(get_screenshot_base64())

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
        logger.info(
            "Waiting for progress bar to reach 100%, current value: {}",
            progress_bar_value,
        )
        time.sleep(5)

if fibratus_process is not None:
    logger.info("Stopping fibratus...")
    # Send CTRL+C to the fibratus process to stop it
    # However, sending CTRL+C to this subprocess also sends it to this process
    # Therefore, we should wait for the signal, trap it and ignore it. The subprocess
    # will be killed however we will continue to exist
    try:
        fibratus_process.send_signal(signal.CTRL_C_EVENT)
        time.sleep(60)
    except KeyboardInterrupt:
        logger.debug("Captured KeyboardInterrupt (SIGINT)")

    time.sleep(15)
    logger.debug("Fibratus stopped")

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
    logger.info("Application's process has ended.")

    output = {
        "application_alive": False,
        "program_installed": False,
        "base64_images": base64_images,
    }

    # Check whether the program has successfully installed, or whether it's just been closed...
    output["program_installed"] = executable["full_installation_name"] in map(
        lambda software: software["name"], get_installed_software()
    )
else:
    # Take a final image
    base64_images.append(get_screenshot_base64())

    logger.info("Starting window enumeration...")
    enumeration = application.windows(top_level_only=False, enabled_only=True)
    interactive_controls = filter(is_interactive_control, enumeration)
    logger.info("Finished window enumeration...")

    output = {
        "application_alive": True,
        "program_installed": False,
        "base64_images": base64_images,
        "top_window_texts": sorted(application.top_window().children_texts()),
        "found_controls": [],
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
    logger.warn("No Fiberatus output found")

logger.info("Uploading data to server...")
response = requests.post(
    API_URL + "/submit_task/" + task_input["_id"],
    json={"window_enumeration": output, "kernel_events": fibratus_output},
)

if response.status_code == 200:
    logger.info("Successfully posted data, shutting down...")