import base64
from io import BytesIO


def get_screenshot_base64(application):
    # Take image of the current top window
    # https://stackoverflow.com/a/31826470
    try:
        image = application.top_window().capture_as_image()
    except RuntimeError:
        # If the top window cannot be found, return None
        return None
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")
