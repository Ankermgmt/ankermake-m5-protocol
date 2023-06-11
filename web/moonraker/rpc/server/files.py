import psutil

from jsonrpc import dispatcher
from pathlib import Path
from flask import current_app as app

from web.model import FileMetadata


@dispatcher.add_method(name="server.files.list")
def server_files_list(root):
    pth = Path("database") / root

    files = []

    for p in pth.iterdir():
        st = p.stat()
        if p.is_file():
            files.append({
                "modified": st.st_mtime,
                "size": st.st_size,
                "permissions": "rw",
                "filename": p.name,
            })

    return files


@dispatcher.add_method(name="server.files.move")
def server_files_move(source, dest):
    ...


@dispatcher.add_method(name="server.files.post_directory")
def server_files_post_directory(path: Path):
    pth = Path("database") / path
    pth.mkdir()
    return {
        "item": {
            "path": pth.name,
            "root": pth.parts[0],
            "modified": pth.stat().st_mtime,
            "size": pth.stat().st_size,
            "permissions": "rw"
        },
        "action": "create_dir"
    }


@dispatcher.add_method(name="server.files.delete_file")
def server_files_delete_file(path: Path):
    pth = Path("database") / path.lstrip("/")
    pth.unlink()
    return {
        "item": {
            "path": pth.name,
            "root": pth.parts[0],
            "modified": 0,
            "size": 0,
            "permissions": ""
        },
        "action": "delete_file"
    }


@dispatcher.add_method(name="server.files.delete_directory")
def server_files_delete_directory(path: Path, force: bool):
    pth = Path("database") / path.lstrip("/")
    pth.rmdir()
    return {
        "item": {
            "path": pth.name,
            "root": pth.parts[0],
            "modified": 0,
            "size": 0,
            "permissions": ""
        },
        "action": "delete_dir"
    }


@dispatcher.add_method(name="server.files.get_directory")
def server_files_get_directory(path="gcodes", extended=False, root=None):
    if extended:
        raise NotImplementedError()

    pth = Path("database") / path

    dirs = []
    files = []

    for p in pth.iterdir():
        st = p.stat()

        obj = {
            "modified": st.st_mtime,
            "size": st.st_size,
            "permissions": "rw",
        }

        if p.is_file():
            obj["filename"] = p.name
            files.append(obj)
        elif p.is_dir():
            obj["dirname"] = p.name
            dirs.append(obj)

    du = psutil.disk_usage(pth)
    return {
        "dirs": dirs,
        "files": files,
        "disk_usage": {
            "total": du.total,
            "used": du.used,
            "free": du.free,
        },
        "root_info": {
            "name": path,
            "permissions": "rw"
        }
    }


@dispatcher.add_method(name="server.files.metadata")
def server_files_metadata(filename):
    if filename is None:
        return {}

    pth = Path("database") / "gcodes" / filename

    if not pth.exists():
        raise FileNotFoundError(f"File not found: {filename}")

    if not pth.is_file():
        return {}

    with app.svc.borrow("jobqueue") as jq:
        return jq.load_metadata_dict(pth)

@dispatcher.add_method(name="server.files.zip")
def server_files_zip():
    raise NotImplementedError()
