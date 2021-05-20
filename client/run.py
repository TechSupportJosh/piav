import json
import os
import signal
import sys
import time
import traceback

import pywinauto
import requests
from windows_tools.installed_software import get_installed_software

from fibratus.helper import kill_fibratus, start_fibratus
from utils.logger import get_logger
from utils.screenshot import get_screenshot_base64
from utils.action import execute_action
from utils.control import enumerate_controls

API_URL = "http://172.22.128.1:8000"
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

    if response.status_code != 200:
        if response.status_code == 404:
            print("No tasks are current queued...")
        else:
            print(
                "Received error when requesting task, status code {}".format(
                    response.status_code
                )
            )

        failed_requests += 1
        continue

    # Otherwise we have successfully retrieved a task
    break

task_input = response.json()

logger = get_logger(API_URL, task_input["_id"])
logger.info("Received task, retrieving application details...")

executable = requests.get(API_URL + "/executable/" + task_input["executable_id"]).json()
logger.info("Retrieved application, downloading executable...")

executable_file_path = "C:\\Users\\piav\\Documents\\{}".format(executable["file_name"])
with open(executable_file_path, "wb") as executable_file:
    executable_file.write(
        requests.get(API_URL + "/executables/" + executable["file_name"]).content
    )

logger.info("Executable downloaded, starting...")

try:
    # Delete old fibratus output if it exists
    try:
        os.remove("fibratus_capture.json")
    except FileNotFoundError:
        pass

    if kill_fibratus():
        logger.info("Killed lingering fibratus.exe")

    application = pywinauto.Application(backend="uia")
    base64_images = []
    fibratus_process = None

    # If there are no setup actions, then we start watching fibratus from the start of the application
    if not len(task_input["setup_actions"]):
        logger.info("Starting fibratus capture before starting application...")
        fibratus_process = start_fibratus(executable["file_name"])

    application.start(executable_file_path)

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
        logger.info(
            "Failed to find top window, attempting to reconnect to the application"
        )

        # If the application has already exited, they may have spawned another process, therefore we'll try and find the
        # application again before erroring
        application.connect(best_match=executable["application_name"])

    # Take a picture of the application as it's started
    base64_images.append(get_screenshot_base64(application))

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
        logger.info("Starting fibratus capture before executing actions...")
        fibratus_process = start_fibratus(executable["file_name"])

    # Execute the actions
    for index, action in enumerate(task_input["actions"]):
        logger.info(
            "Now executing action {} of {}.",
            index + 1,
            len(task_input["actions"]),
        )

        execute_action(application, base64_images, logger, action)

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

    # Now we've executed all input precusors, check whether the application is still available
    # For example, clicking a "Cancel" button may close down the application
    if not application.is_process_running():
        logger.info("Application process has ended")

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
        base64_images.append(get_screenshot_base64(application))

        logger.info("Starting window enumeration...")
        found_controls = enumerate_controls(application)
        logger.info("Finished window enumeration...")

        output = {
            "application_alive": True,
            "program_installed": False,
            "base64_images": base64_images,
            "top_window_texts": sorted(application.top_window().children_texts()),
            "found_controls": found_controls,
        }

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
    else:
        logger.error("Failed to post data, status code: {}", response.status_code)

except Exception as exception:
    error_message = "".join(traceback.format_tb(exception.__traceback__)).strip()

    logger.critical("An exception occured:\n{}", error_message)
    response = requests.post(
        API_URL + "/error/" + task_input["_id"],
        json={"stack_trace": error_message},
    )

if "--do-not-shutdown" not in sys.argv:
    # https://stackoverflow.com/a/50824776
    logger.info("Shutting down...")

    # Attempt shutdown via Windows API
    import ctypes

    user32 = ctypes.WinDLL("user32")
    user32.ExitWindowsEx(0x00000008, 0x00000000)

    # If not, try shutdown using the shutdown command
    os.system("shutdown /p /f")