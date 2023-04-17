import psutil

from jsonrpc import dispatcher
from pathlib import Path


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
    print(pth, path)
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
def server_files_get_directory(path):
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
def server_files_get_metadata(filename):
    return {
        "print_start_time": None,
        "job_id": None,
        "size": 4926481,
        "modified": 1615077020.2025201,
        "slicer": "SuperSlicer",
        "slicer_version": "2.2.52",
        "layer_height": 0.15,
        "first_layer_height": 0.2,
        "object_height": 48.05,
        "filament_total": 4056.4,
        "estimated_time": 7569,
        "thumbnails": [
            # {
            #     "width": 32,
            #     "height": 32,
            #     "size": 2596,
            #     "relative_path": ".thumbs/3DBenchy_0.15mm_PLA_MK3S_2h6m-32x32.png"
            # },
            # {
            #     "width": 400,
            #     "height": 300,
            #     "size": 73308,
            #     "relative_path": ".thumbs/3DBenchy_0.15mm_PLA_MK3S_2h6m-400x300.png"
            # }
        ],
        "first_layer_bed_temp": 60,
        "first_layer_extr_temp": 215,
        "gcode_start_byte": 79451,
        "gcode_end_byte": 4915668,
        "filename": "3DBenchy_0.15mm_PLA_MK3S_2h6m.gcode"
    }
