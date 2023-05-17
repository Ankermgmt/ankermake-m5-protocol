import logging as log
from dataclasses import asdict
from flask import flash, redirect


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


def get_printer(config, index=0):
    """
    Open configuration object, extract and sanitize printer information, then return it.

    Parameters:
    config (object): An object containing application configuration.
    index (int, optional): Index of the printer in the configuration. Default is 0.

    Returns:
    dict: Dictionary containing sanitized printer information.

    The function logs warnings if the provided index is out of range and defaults it to 0. 
    It removes 'mqtt_key' and 'p2p_key' from the printer information before returning.
    """
    with config.open() as cfg:
        printers = cfg.printers
        if index >= len(printers):
            log.warning(f"Printer number {index} out of range, max printer number is {len(printers)-1}")
            log.warning(f"Defaulting index to 0")
            index = 0

        printer_dict = asdict(printers[index])
        printer_dict.pop("mqtt_key", None)
        printer_dict.pop("p2p_key", None)
        return printer_dict
