import json
import logging as log


def format_jsonrpc_req(req):
    args = []
    for key, value in req["params"].items():
        args.append(f"{key}={json.dumps(value)}")

    return f"{req['method']}({', '.join(args)})"


def log_jsonrpc_req(req, response):
    if response.error:
        log.error(f"[RPC] {format_jsonrpc_req(req)} = {json.dumps(response.error, indent=4)}")
    else:
        log.info(f"[RPC] {format_jsonrpc_req(req)} = {json.dumps(response.result)}")


def make_jsonrpc_req(method, *args, **kwargs):
    if args and kwargs:
        raise ValueError("Cannot mix positional and keyword arguments")

    return json.dumps({
        "method": method,
        "params": args or kwargs,
        "jsonrpc": "2.0",
        "id": 0,
    })
