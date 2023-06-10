import json
import flask_sock

from flask import Blueprint, Response, request, render_template, stream_with_context
from flask import current_app as app
from jsonrpc import JSONRPCResponseManager, dispatcher
from user_agents import parse as user_agent_parse

import web.config
import web.util


sock = flask_sock.Sock()
router = Blueprint("base", __name__)


@sock.route("/websocket", bp=router)
def websocket(sock):
    with app.svc.borrow("updates") as updates:
        with updates.tap(lambda data: sock.send(data)):
            while True:
                msg = sock.receive()
                response = JSONRPCResponseManager.handle(msg, dispatcher)
                jmsg = json.loads(msg)
                web.rpcutil.log_jsonrpc_req(jmsg, response)
                if response.error:
                    error_msg = response.error.get("data", {}).get("message") or response.error["message"]
                    updates.notify_error(f"<h1>Error in method {jmsg['method']}</h1>\n{error_msg}")
                sock.send(web.rpcutil.format_response(response))


@router.get("/video")
def video_download():
    """
    Handles the video streaming/downloading feature in the Flask app
    """
    def generate():
        if not app.config["login"]:
            return
        for msg in app.svc.stream("videoqueue"):
            yield msg.data

    return Response(stream_with_context(generate()), mimetype="video/mp4")


@router.get("/")
def app_root():
    """
    Renders the html template for the root route, which is the homepage of the Flask app
    """
    config = app.config["config"]
    with config.open() as cfg:
        user_agent = user_agent_parse(request.headers.get("User-Agent"))
        user_os = web.platform.os_platform(user_agent.os.family)

        if cfg:
            anker_config = str(web.config.config_show(cfg))
            printer = cfg.printers[app.config["printer_index"]]
        else:
            anker_config = "No printers found, please load your login config..."
            printer = None

        if ":" in request.host:
            request_host, request_port = request.host.split(":", 1)
        else:
            request_host = request.host
            request_port = "80"

        return render_template(
            "index.html",
            request_host=request_host,
            request_port=request_port,
            configure=app.config["login"],
            login_file_path=web.platform.login_path(user_os),
            anker_config=anker_config,
            printer=printer
        )
