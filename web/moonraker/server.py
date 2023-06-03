import json
import flask_sock

from pathlib import Path
from flask import Blueprint, request, send_from_directory
from werkzeug.utils import secure_filename

from .rpc import server


sock = flask_sock.Sock()
router = Blueprint("server", __name__)


@router.get("/info")
def server_info():
    return { "result": server.server_info() }


@router.get("/files/<string:root>/<path:path>")
def server_files(root, path):
    return send_from_directory(Path("database") / root, path)


@router.post("/files/upload")
def server_files_upload():
    root = request.values.get("root", "gcodes")
    if root not in {"gcodes", "config", "config_examples", "docs"}:
        raise ValueError(f"Forbidden root {root!r}")

    file = request.files['file']
    filename = secure_filename(file.filename)
    path = Path("database") / root / filename
    file.save(path)
    stat = path.stat()
    return {
        "item": {
            "path": filename,
            "root": root,
            "modified": stat.st_mtime,
            "size": stat.st_size,
            "permissions": "rw"
        },
        "print_started": False,
        "print_queued": False,
        "action": "create_file"
    }


# http wrapper for websocket endpoint (needed for Fluidd)
@router.get("/database/item")
def get_database_item():
    return {
        "result": server.database.server_database_get_item(
            request.args.get("namespace")
        )
    }


# http wrapper for websocket endpoint (needed for Fluidd)
@router.post("/database/item")
def post_database_item():
    return {
        "result": server.database.server_database_post_item(
            request.args.get("namespace"),
            request.args.get("key"),
            request.args.get("value"),
        )
    }
