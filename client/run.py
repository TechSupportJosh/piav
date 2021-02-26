import json
import sys
import time
import pywinauto
import pywinauto.controls.uia_controls as uia_controls

application_name = "FileZilla"
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
with open("../server/input/{}-input.json".format(sys.argv[1]), "r") as task_input_json:
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

# Now we've executed all input precusors, check whether the application is still available
# For example, clicking a "Cancel" button may close down the application
# application_alive
# TODO

interactive_control_types = [uia_controls.ButtonWrapper]

def is_interactive_control(control):
    print(control)
    print(repr(control))
    # Check whether it's listed as  a interactive_control_type and that 
    # it's parent is not the title bar (minimise, maximise, etc.) and buttons from a scrollbar
    return type(control) in interactive_control_types and control.parent().friendly_class_name() not in ["ScrollBar", "TitleBar"]

def attempt_unique_id(control):
    if control.automation_id() != "":
        return {
            "auto_id": control.automation_id()
        }

print("Starting window enumeration...")
enumeration = application.windows(top_level_only=False)
interactive_controls = filter(is_interactive_control, enumeration)
print("Finished window enumeration...")

output = {
    "input_id": task_input["input_id"],
    "application_alive": True,
    "found_controls": []
}

# Now we need to output the list of possible controls
for control in interactive_controls:
    control_type = None

    output["found_controls"].append({
        "type": control.friendly_class_name(),
        "reference": attempt_unique_id(control)
    })

with open(f"../server/output/{task_input['input_id']}-output.json", "w") as task_output_file:
    json.dump(output, task_output_file, indent=2)

# Finally, kill the application
application.kill(soft=False)