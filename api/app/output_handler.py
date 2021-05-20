import itertools
import logging
from logs import CustomFormatter

output_logger = logging.getLogger("output")
output_logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())
output_logger.addHandler(ch)


def get_action_for_button(button_control):
    # Add new precursor, click on this button
    return {
        "control": button_control,
        "wait_for_element_timeout": 15,  # TODO: dynamic delays
        "delay_after_action": 10,
        "method": "click_input",
        "method_params": {},
    }


def enumerate_output_and_generate_actions(task_output):
    output_controls = task_output["found_controls"]

    # Actions is a list of lists of actions
    actions = []

    output_logger.debug("Input elements: %s", str(output_controls))

    # Create a list of all the different types of controls
    buttons = list(filter(lambda element: element["type"] == "Button", output_controls))
    radio_buttons = list(
        filter(lambda element: element["type"] == "RadioButton", output_controls)
    )
    checkboxes = list(
        filter(lambda element: element["type"] == "CheckBox", output_controls)
    )

    output_logger.debug("Buttons: %s", str(buttons))
    output_logger.debug("Radio Buttons: %s", str(radio_buttons))

    # TODO: What if we have radio buttons and checkboxes on the same page?

    # If we have radio buttons
    if radio_buttons:
        # Generate the cartesian product of radio buttons and regular buttons
        for radio_button, button_control in itertools.product(radio_buttons, buttons):
            output = []

            # Click on this radio button
            output.append(
                {
                    "control": radio_button,
                    "wait_for_element_timeout": 15,  # TODO: dynamic delays
                    "delay_after_action": 10,
                    "method": "click_input",
                    "method_params": {},
                }
            )

            # Then click on the button
            output.append(get_action_for_button(button_control))

            # Add to actions list
            actions.append(output)
    elif checkboxes:
        # If we have checkboxes
        # Generate all possible combinations of the checkboxes and their states (TT, TF, FT, FF)
        nest_me = itertools.product([False, True], repeat=len(checkboxes))
        # Then generate cartesian product of all of those states and buttons
        product_list = itertools.product(nest_me, buttons)
        for checkboxes_state, button_control in product_list:
            # Loop through checkboxes state and set each of them to the state
            # checkboxes_state = (1, 0, 0) if there's 3 checkboxes
            output = []

            for box_index, value in enumerate(checkboxes_state):
                output.append(
                    {
                        "control": checkboxes[box_index],
                        "wait_for_element_timeout": 15,  # TODO: dynamic delays
                        "delay_after_action": 2,
                        "method": "set_toggle_state",
                        "method_params": {
                            "state": value,
                        },
                    }
                )

            # Then click on the button
            output.append(get_action_for_button(button_control))

            # Add to actions list
            actions.append(output)
    else:
        # If we just have buttons, click on them
        for button_control in buttons:
            actions.append([get_action_for_button(button_control)])

    output_logger.debug("Branches: %s", str(actions))

    return actions