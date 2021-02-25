import json
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
with open("start.json", "r") as task_input_json:
    task_input = json.load(task_input_json)

# Now execute task_input 
for index, stage in enumerate(task_input["precursors"]):
    print("Now executing precursor {} of {}.".format(index + 1, len(task_input["precursors"])))

    # Find the element referenced
    control = application.window(**stage["reference"])

    try:
        control.wait("visible", timeout=stage.get("wait_delay", None))
    except pywinauto.timings.TimeoutError:
        print("Control {} was not available after {} seconds.")
        # TODO: Error handling for when it doesn't go as expected...
    
    # Now run the action defined on the control
    control[stage["action"]["method"]](**stage["action"]["parameters"])

# Now we've executed all input precusors, check whether the application is still available
# For example, clicking a "Cancel" button may close down the application
# application_alive
# TODO

interactive_control_types = [uia_controls.ButtonWrapper]

def is_interactive_control(element):
    # Check whether it's listed as  a interactive_control_type and that 
    # it's parent is not the title bar (minimise, maximise, etc.) and buttons from a scrollbar
    return type(element) in interactive_control_types and element.parent().friendly_class_name() not in ["ScrollBar", "TitleBar"]

def attempt_unique_id(element):
    if element.automation_id() != "":
        return {
            "auto_id": element.automation_id()
        }
# A list of types that we can interactive with
enumeration = application.windows(top_level_only=False)

interactive_controls = filter(is_interactive_control, enumeration)

output = {
    "input_id": task_input["input_id"],
    "application_alive": True,
    "found_elements": []
}

# Now we need to output the list of possible controls
for control in interactive_controls:
    output["found_elements"].append({
        "type": control.__class__.__name__,
        "reference": attempt_unique_id(control)
    })

with open(f"{task_input['input_id']}-output.json", "w") as task_output_file:
    json.dump(output, task_output_file, indent=2)

# Finally, kill the application
application.kill(soft=False)