import logging as log
from flask import flash, redirect, request, url_for


def flash_redirect(path: str, message: str | None = None, category="info"):
    """
    Flashes a message and redirects the user to the specified path.

    Args:
        - path (str): A string representing the path to redirect the user to.
        - message (str | None): An optional string message to flash to the user.
        - category (str): A string representing the category of the flashed message. 
            Possible values are "info" (default), "danger", "warning", "success".

    Raises:
        - ValueError: If the path parameter is not provided.

    Returns:
        - A Flask redirect object.
    """
    if not path:
        raise ValueError("Redirect path is required")

    if message:
        flash(message, category)

    return redirect(path)


def upload_file_to_printer(app, file, web_upload=False):
    user_name = request.headers.get("User-Agent", "ankerctl").split(url_for('app_root'))[0]

    with app.svc.borrow("filetransfer") as ft:
        try:
            ft.send_file(file, user_name)
        except ConnectionError as err:
            log.error(f"Connection error: {err}")
            raise ConnectionError(err)
        except Exception as err:
            log.error(f"Unknown error: {err}")
            raise Exception(err)

    return {}
