import psutil

from jsonrpc import dispatcher
from pathlib import Path
from flask import current_app as app

from web.model import FileMetadata
from web.lib.gcodemeta import GCodeMetaAuto
from web.lib.gcodemeta.ankerslicer import GCodeMetaAnkerSlicer
from web.lib.gcodemeta.prusaslicer import GCodeMetaPrusaSlicer
from web.lib.gcodemeta.superslicer import GCodeMetaSuperSlicer


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

    stat = pth.stat()

    gcm = GCodeMetaAuto([
        GCodeMetaAnkerSlicer(),
        GCodeMetaPrusaSlicer(),
        GCodeMetaSuperSlicer(),
    ])

    md = FileMetadata()

    if pth.is_file():
        fd = pth.open(mode="rb")
        if gcm.detect(fd):
            props = gcm.load_props(fd)
            md = gcm.load_metadata(props)

    md.size = stat.st_size
    md.modified = stat.st_mtime
    md.filename = filename

    with app.svc.borrow("jobqueue") as jq:
        job_info = {}
        for h in jq.queue.history:
            if h.filename == filename:
                job_info["job_id"] = h.job_id
                job_info["uuid"] = h.metadata.uuid
                break

    return {
        **md.to_dict(),
        **job_info,
    }

@dispatcher.add_method(name="server.files.zip")
def server_files_zip():
    raise NotImplementedError()
