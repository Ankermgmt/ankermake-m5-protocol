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


def flash_redirect_root(message: str | None = None, category="info"):
    return flash_redirect(url_for("base.app_root"), message, category)


def upload_file_to_printer(app, file):
    """ This function uploads a file to the printer.

    Args:
        - app (object): The application object.
        - file (file-like object): The file to be uploaded to the printer.
    """
    user_name = request.headers.get("User-Agent", "ankerctl").split("/")[0]

    with app.svc.borrow("filetransfer") as ft:
        ft.send_file(file, user_name)


def get_host_port(app):
    """
    Extracts the host and port from the incoming request.
    If no host or port is provided in the request,
    the function falls back to the host and port from the application configuration.

    Args:
        - app (object): The application object.

    Returns:
    A list containing.
        - request_host (str): A string representing the hostname.
        - request_port (str): A string representing the port number. Defaults to '80'.

    Raises:
        - None
    """
    if hasattr(request, "host"):
        if ":" in request.host:
            request_host, request_port = request.host.split(":", 1)
        else:
            request_host = request.host
            request_port = "80"
    else:
        request_host = app.config["host"]
        request_port = app.config["port"]

    return [request_host, request_port]
