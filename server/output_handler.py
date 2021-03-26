import json
import copy
import os
import sys
import itertools
import logging
from CustomFormatter import CustomFormatter

output_logger = logging.getLogger("output")
output_logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())
output_logger.addHandler(ch)

def add_button_press_to_precusor_list(branches, precursor_list, button_control):
    # Add new precursor, click on this button
    precursor_list.append({
        "reference": button_control["reference"],
        "wait_for_element_timeout": 15, # TODO: dynamic delays
        "delay_after_action": 10,
        "action": {
            "method": "click",
            "parameters": {}
        }
    })

    branches.append({
        "precursors": precursor_list
    })

def get_branches(input_task, output_task):
    output_logger.info("Processing output of task %s", input_task["_id"])

    output_controls = output_task["found_controls"]
    prepend_precursor = input_task["precursors"]

    branches = []

    output_logger.debug("Input elements: %s", str(output_controls))

    # Create a list of all the different types of controls
    buttons = list(filter(lambda element: element["type"] == "Button", output_controls))
    radio_buttons = list(filter(lambda element: element["type"] == "RadioButton", output_controls))
    checkboxes = list(filter(lambda element: element["type"] == "CheckBox", output_controls))

    output_logger.debug("Buttons: %s", str(buttons))
    output_logger.debug("Radio Buttons: %s", str(radio_buttons))

    # TODO: What if we have radio buttons and checkboxes on the same page?

    # If we have radio buttons
    if radio_buttons:
        # Generate the cartesian product of radio buttons and regular buttons
        for radio_button, button_control in itertools.product(radio_buttons, buttons):
            new_precursors = copy.deepcopy(prepend_precursor)
            
            # Click on this radio button
            new_precursors.append({
                "reference": radio_button["reference"],
                "wait_for_element_timeout": 15, # TODO: dynamic delays
                "delay_after_action": 10,
                "action": {
                    "method": "click",
                    "parameters": {}
                }
            })

            # Then click on the button
            add_button_press_to_precusor_list(branches, new_precursors, button_control)
    elif checkboxes:
        # If we have checkboxes
        # Generate all possible combinations of the checkboxes and their states (TT, TF, FT, FF)
        nest_me = itertools.product([False, True], repeat=len(checkboxes))
        # Then generate cartesian product of all of those states and buttons
        product_list = itertools.product(nest_me, buttons)
        for checkboxes_state, button_control in product_list:
            new_precursors = copy.deepcopy(prepend_precursor)
            
            # Loop through checkboxes state and set each of them to the state 
            # checkboxes_state = (1, 0, 0) if there's 3 checkboxes
            for box_index, value in enumerate(checkboxes_state):
                new_precursors.append({
                    "reference": checkboxes[box_index]["reference"],
                    "wait_for_element_timeout": 15, # TODO: dynamic delays
                    "delay_after_action": 2,
                    "action": {
                        "method": "set_toggle_state",
                        "parameters": {
                            "state": value
                        }
                    }
                })

            add_button_press_to_precusor_list(branches, new_precursors, button_control)
    else:
        # If we just have buttons, click on them
        for button_control in buttons:
            new_precursors = copy.deepcopy(prepend_precursor)
            
            add_button_press_to_precusor_list(branches, new_precursors, button_control)

    output_logger.debug("Branches: %s", str(branches))

    return branches