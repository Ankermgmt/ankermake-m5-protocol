from flask import flash, redirect


def flash_redirect(path: str, message: str | None = None, category="info"):
    if not path:
        raise ValueError("Redirect path is required")
    if message:
        flash(message, category)
    return redirect(path)
