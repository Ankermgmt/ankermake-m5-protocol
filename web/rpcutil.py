import json
import logging

log = logging.getLogger("RPC")


def format_jsonrpc_req(req):
    args = []
    for key, value in req.get("params", {}).items():
        args.append(f"{key}={json.dumps(value)}")

    return f"{req['method']}({', '.join(args)})"


def format_jsonrpc_resp(resp):
    if isinstance(resp, dict):
        keys = ", ".join(repr(k) for k in resp.keys())
        return f"{{{keys}}}"
    elif isinstance(resp, list):
        keys = ", ".join(resp)
        return f"[{keys}]"
    else:
        return repr(resp)


def log_jsonrpc_req(req, response):
    try:
        if response.error:
            log.error(f"{format_jsonrpc_req(req)} = {json.dumps(response.error, indent=4)}")
        else:
            log.info(f"{format_jsonrpc_req(req)} = {format_jsonrpc_resp(response.result)}")
    except TypeError:
        log.error(f"{format_jsonrpc_req(req)} INVALID JSON VALUE: {response.result}")


def make_jsonrpc_req(method, *args, **kwargs):
    if args and kwargs:
        raise ValueError("Cannot mix positional and keyword arguments")

    return json.dumps({
        "method": method,
        "params": args or kwargs,
        "jsonrpc": "2.0",
        "id": 0,
    })


def format_response(response):
    """
    Format a JSON-RPC response for use with Moonraker

    Args:
        - response: The result of a JSON-RPC request

    Returns:
        - the formatted json response
    """
    if not response.error:
        return response.json

    error = response.data.setdefault("error", {})
    error["code"] = 400
    error["message"] = error.get("data", {}).get("message", "Unknown error")
    return response.json
