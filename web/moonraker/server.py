import json
from pathlib import Path

from flask import request, send_from_directory
from werkzeug.utils import secure_filename

from .. import sock, app, rpcutil
from .rpc import server

@app.get("/server/info")
def server_info():
    return { "result": server.server_info() }


@app.get("/server/files/<string:root>/<path:path>")
def server_files(root, path):
    return send_from_directory(Path("database") / root, path)


@app.post("/server/files/upload")
def server_files_upload():
    root = request.values["root"]
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
