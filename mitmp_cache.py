from mitmproxy import http
from collections import defaultdict

cache = {}
cachecnt = defaultdict(int)

def request(flow: http.HTTPFlow) -> None:
    if flow.request.method == "GET":
        key = (flow.request.pretty_url, tuple(flow.request.headers.items()))
        if key in cache:
            cachecnt[key] += 1
            flow.response = cache[key].copy()
            flow.response.is_replay = True
            flow.response.headers["X-MITM-Proxy-Cache-Use-Count"] = f"{cachecnt[key]}"

def response(flow: http.HTTPFlow) -> None:
    if flow.request.method == "GET" and flow.response.status_code == 200:
        if "set-cookie" not in flow.response.headers:
            key = (flow.request.pretty_url, tuple(flow.request.headers.items()))
            cache[key] = flow.response.copy()
