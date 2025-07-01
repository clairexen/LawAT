from mitmproxy import http
from collections import defaultdict
import os, re

cache = {}
cachecnt = defaultdict(int)

if not os.access("__riscache__", os.F_OK):
    os.mkdir("__riscache__")

def url_to_filename(url):
        fn = re.sub(r'[^a-zA-Z0-9\.-]', '_', url.replace('/', '-'))
        fn = re.sub(r"_[a-zA-Z_]{5,}_", lambda t: hex(hash(t))[10:], fn)

def request(flow: http.HTTPFlow) -> None:
    if flow.request.method == "GET":
        # key = (flow.request.pretty_url, tuple(flow.request.headers.items()))
        key = flow.request.pretty_url
        if key in cache:
            cachecnt[key] += 1
            flow.response = cache[key].copy()
            flow.response.is_replay = True
            flow.response.headers["x-mitm-proxy-cache-use-count"] = f"{cachecnt[key]} @ {key}"
        else:
            flow.marked = True
    else:
        flow.marked = True

def response(flow: http.HTTPFlow) -> None:
    if flow.request.method == "GET" and flow.response.status_code == 200:
        # if "set-cookie" in flow.response.headers: return
        # key = (flow.request.pretty_url, tuple(flow.request.headers.items()))
        key = flow.request.pretty_url
        fn = url_to_filename(key)
        cache[key] = flow.response.copy()
        open(f"__riscache__/{re.sub(r'[^a-zA-Z0-9\.-]', '_', key.replace('/', '-'))}", "wb").write(flow.response.content)
