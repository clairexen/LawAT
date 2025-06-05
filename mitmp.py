from mitmproxy import http
from collections import defaultdict

cache = {}
cachecnt = defaultdict(int)

def request(flow: http.HTTPFlow) -> None:
    if flow.request.method == "GET":
        # key = (flow.request.pretty_url, tuple(flow.request.headers.items()))
        key = flow.request.pretty_url
        if key in cache:
            cachecnt[key] += 1
            flow.marked = True
            flow.response = cache[key].copy()
            flow.response.is_replay = True
            flow.response.headers["x-mitm-proxy-cache-use-count"] = f"{cachecnt[key]} @ {key}"

def response(flow: http.HTTPFlow) -> None:
    if flow.request.method == "GET" and flow.response.status_code == 200:
        # if "set-cookie" in flow.response.headers: return
        # key = (flow.request.pretty_url, tuple(flow.request.headers.items()))
        key = flow.request.pretty_url
        cache[key] = flow.response.copy()
