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


def get_screenshot_base64():
    # Take image of the current top window
    # https://stackoverflow.com/a/31826470
    image = application.top_window().capture_as_image()
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def start_fibratus(executable_name):
    logger.info("Starting fibratus capturing...")
    return subprocess.Popen(
        [
            "fibratus",
            "run",
            "ps.name = '{}' and kevt.category in ('net','file','registry')".format(
                executable_name
            ),
            "-f",
            "capture",
            "--filament.path",
            os.getcwd(),
        ],
        cwd=os.getcwd(),
    )


API_URL = "http://172.28.48.1:8000"
failed_requests = 0

# Request task ID
while True:
    if failed_requests:
        # Cap failed requests at 8
        timeout = 2 ** min(8, failed_requests)
        print("Waiting {} seconds before trying again...".format(timeout))
        time.sleep(timeout)

    try:
        response = requests.post(API_URL + "/vm/request_task", timeout=10)
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

print(task_input)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("logger")

http_handler = JSONHTTPHandler(API_URL, "/vm/log/" + task_input["_id"])
http_handler.setLevel(logging.DEBUG)

logger.addHandler(http_handler)

logger = StyleAdapter(logger)

logger.info("Received task, retrieving application details...")

executable = requests.get(API_URL + "/executable/" + task_input["executable_id"]).json()

logger.info("Retrieved application, downloading executable...")

executable_file_path = "C:\\Users\\piav\\Documents\\{}".format(executable["file_name"])
with open(executable_file_path, "wb") as executable_file:
    executable_file.write(
        requests.get(API_URL + "/executables/" + executable["file_name"]).content
    )

logger.info("Executable downloaded, starting...")

fibratus_process = None

# Delete old fibratus output if it exists
try:
    os.remove("fibratus_capture.json")
except FileNotFoundError:
    pass

# Kill old fibratus process
for proc in psutil.process_iter():
    if proc.name() == "fibratus.exe":
        logger.info("Found old fibratus.exe, killing...")
        proc.kill()

application = pywinauto.Application(backend="uia")

# If there are no setup actions, then we start watching fibratus from the start of the application
if not len(task_input["setup_actions"]):
    fibratus_process = start_fibratus(executable["file_name"])

application.start(executable_file_path)

base64_images = []


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

# Take a picture of the application as it's started
base64_images.append(get_screenshot_base64())


def execute_action(application, base64_images, logger, action):
    # Find the control referenced
    control_reference = application.window(**action["reference"], top_level_only=False)

    timeout = action.get("wait_for_element_timeout", 0)
    try:
        control = control_reference.wait("visible", timeout=timeout)
    except pywinauto.timings.TimeoutError:
        logger.warning(
            "Control {} was not available after {} seconds.",
            action["reference"],
            timeout,
        )
        # TODO: Error handling for when it doesn't go as expected...

    # Now run the action defined on the control (executes control.method(parameters))
    if action["method"] == "set_toggle_state":
        current_state = bool(control.get_toggle_state())
        desired_state = action["method_params"]["state"]

        if current_state != desired_state:
            control.click()
    else:
        getattr(control, action["method"])(**action["method_params"])

    delay = action.get("delay_after_action", 0)
    logger.debug("Waiting for {} seconds.", delay)
    time.sleep(delay)

    # After running this precursor, take a screenshot
    base64_images.append(get_screenshot_base64())


# Execute the setup actions
for index, action in enumerate(task_input["setup_actions"]):
    logger.info(
        "Now executing setup action {} of {}.",
        index + 1,
        len(task_input["setup_actions"]),
    )

    execute_action(application, base64_images, logger, action)

# If there was setup_actions, we can now run fibratus
if len(task_input["setup_actions"]):
    fibratus_process = start_fibratus(executable["file_name"])

# Execute the actions
for index, action in enumerate(task_input["actions"]):
    logger.info(
        "Now executing action {} of {}.",
        index + 1,
        len(task_input["actions"]),
    )

    execute_action(application, base64_images, logger, action)

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
        time.sleep(300)
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

if os.path.exists("fibratus_capture.json"):
    with open("fibratus_capture.json", "r") as fibratus_output_file:
        fibratus_output = json.load(fibratus_output_file)
    os.remove("fibratus_capture.json")
else:
    logger.warning("No Fiberatus output found")

logger.info("Uploading data to server...")
response = requests.post(
    API_URL + "/vm/submit_task/" + task_input["_id"],
    json={"window_enumeration": output, "kernel_events": fibratus_output},
)

if response.status_code == 200:
    logger.info("Successfully posted data")

if "--restart-at-end" in sys.argv:
    # https://stackoverflow.com/a/50826520
    logger.info("Restarting...")

    import ctypes

    user32 = ctypes.WinDLL("user32")
    user32.ExitWindowsEx(0x00000002, 0x00000000)