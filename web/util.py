from flask import flash, redirect

def flash_redirect(message: str | None = None, category = 'info', path = '/'):
    if message:
        flash(message, category)
    return redirect(path)
