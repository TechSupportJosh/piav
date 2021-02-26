import json
import copy
import os
import sys

def add_button_press_to_precusor_list(branches, precursor_list, button_control):
    global task_counter

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
    prepend_precursor = input_task["precursors"]

    branches = []

    # so the strat is 
    # Radio buttons create branches for each value (1 -> button, 2 -> button, 3 -> button)
    # Check boxes create multiple branches for each value (1 -> button, 12 -> button, 123 -> button, 2 -> button etc.)
    # So the strat is to work backwords, iterate through each button, if there's radio buttons, append each of them before hand

    output_controls = output_task["found_controls"]

    print("Input elements: ", output_controls)

    buttons = list(filter(lambda element: element["type"] == "Button", output_controls))
    radio_buttons = list(filter(lambda element: element["type"] == "RadioButton", output_controls))
    checkboxes = list(filter(lambda element: element["type"] == "CheckBox", output_controls))

    print("Buttons: ", buttons)
    print("Radio Buttons: ", radio_buttons)

    import itertools

    if radio_buttons:
        for radio_button, button_control in itertools.product(radio_buttons, buttons):
            new_precursors = copy.deepcopy(prepend_precursor)
            
            # Add new precursor, click on this button
            new_precursors.append({
                "reference": radio_button["reference"],
                "wait_for_element_timeout": 15, # TODO: dynamic delays
                "delay_after_action": 10,
                "action": {
                    "method": "click",
                    "parameters": {}
                }
            })

            add_button_press_to_precusor_list(branches, new_precursors, button_control)
    elif checkboxes:
        nest_me = itertools.product([False, True], repeat=len(checkboxes))
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
        for button_control in buttons:
            new_precursors = copy.deepcopy(prepend_precursor)
            
            add_button_press_to_precusor_list(branches, new_precursors, button_control)

    print("Branches: ", branches)

    #for branch in branches:
    #    with open("input/{}-input.json".format(branch["input_id"]), "w") as output_task_file:
    #        json.dump(branch, output_task_file, indent=2)

    return branches