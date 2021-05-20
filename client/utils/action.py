import time
from utils.screenshot import get_screenshot_base64
import pywinauto


def execute_action(application, base64_images, logger, action):
    # Find the control referenced
    control_reference = application.window(
        **action["control"]["reference"], top_level_only=False
    )

    timeout = action.get("wait_for_element_timeout", 0)
    try:
        control = control_reference.wait("visible", timeout=timeout)
    except pywinauto.timings.TimeoutError:
        logger.warning(
            "Control {} was not available after {} seconds.",
            action["control"],
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

    screenshot = get_screenshot_base64(application)
    if screenshot is not None:
        # After running this precursor, take a screenshot
        base64_images.append(screenshot)
