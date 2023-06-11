import json
import flask_sock

from pathlib import Path
from flask import Blueprint, request, send_from_directory
from werkzeug.utils import secure_filename

from .rpc import server
from ..util import rpc_wrap_get, rpc_wrap_post


sock = flask_sock.Sock()
router = Blueprint("server", __name__)


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

rpc_wrap_get(router,  "/info",             server.server_info)
rpc_wrap_get(router,  "/database/item",    server.database.server_database_get_item)
rpc_wrap_post(router, "/database/item",    server.database.server_database_post_item)
