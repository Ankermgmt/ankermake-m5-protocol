from flask import flash, redirect

def allowed_file(filename: str, allowed_ext: object):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_ext


def flash_redirect(message: str | None = None, category = 'info', path = '/'):
    if message:
        flash(message, category)
    return redirect(path)
