from mitmproxy import http, ctx
import os
import re
import hashlib

# Directory where cached bodies (.content) and header metadata (.headers) are stored
CACHE_DIR = "__riscache__"
CACHED_ONLY = False

memcache = dict()

# Ensure the cache directory exists.
os.makedirs(CACHE_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sanitize(url: str) -> str:
    """Return a filesystem‑safe filename derived from *url*."""
    safe = re.sub(r"[^a-zA-Z0-9\.-]", "_", url)
    if len(safe) > 200:
        digest = hashlib.sha256(url.encode()).hexdigest()[:16]
        safe = f"{safe[:200]}_{digest}"
    return safe


def _paths(url: str):
    base = _sanitize(url)
    return (
        os.path.join(CACHE_DIR, f"{base}.content"),
        os.path.join(CACHE_DIR, f"{base}.headers"),
        base,
    )

# ---------------------------------------------------------------------------
# Mitmproxy hooks
# ---------------------------------------------------------------------------

def request(flow: http.HTTPFlow):
    """Serve cached responses *or* return a 502 cache‑miss error."""
    if flow.request.method.upper() != "GET":
        return  # Only cache GETs

    content_path, headers_path, base = _paths(flow.request.pretty_url)


    if not (os.path.exists(content_path) and os.path.exists(headers_path)):
        ctx.log.warn(f"Uncached request: {base}")
        if CACHED_ONLY:
            flow.response = http.Response.make(
                502,
                b"Cache miss: no stored response available.\n",
                {
                    "content-type": "text/plain; charset=utf-8",
                    "x-mitmp-missing-filename": base,
                },
            )
            flow.response.is_replay = True
        return

    # ---------------- Cache‑HIT ----------------
    if base in memcache:
        ctx.log.info(f"Cached Request in Memory: {base}")
        flow.response = memcache[base].copy()
        flow.response.is_replay = True
        return

    ctx.log.info(f"Cached Request: {base}")

    with open(content_path, "rb") as f:
        body = f.read()

    with open(headers_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()

    # Request section ends at first blank line
    try:
        blank = lines.index("")
        resp_meta = lines[blank + 1 :]
    except ValueError:
        resp_meta = []

    # --- Parse status line ---
    status_code = 200
    if resp_meta:
        status_line = resp_meta[0]
        m = re.match(r"HTTP/\d\.\d\s+(\d+)", status_line)
        if m:
            status_code = int(m.group(1))
        resp_meta = resp_meta[1:]

    # --- Parse headers ---
    resp_headers: dict[str, str] = {}
    for line in resp_meta:
        if ": " in line:
            name, value = line.split(": ", 1)
            low = name.lower()
            if low in {"transfer-encoding", "content-length"}:
                continue
            resp_headers[name] = value

    resp_headers["x-mitmp-cached-filename"] = base
    resp_headers["Content-Length"] = str(len(body))

    flow.response = http.Response.make(status_code, body, resp_headers)
    flow.response.is_replay = True


def response(flow: http.HTTPFlow):
    """Persist successful GETs that were not served from cache."""
    if flow.request.method.upper() != "GET":
        return

    if getattr(flow.response, "is_replay", False):
        return

    content_path, headers_path, base = _paths(flow.request.pretty_url)
    memcache[base] = flow.response.copy()

    # --- Save body ---
    with open(content_path, "wb") as f:
        f.write(flow.response.raw_content or b"")

    # --- Save request & response headers ---
    with open(headers_path, "w", encoding="utf-8") as f:
        # Full request line
        f.write(
            f"{flow.request.method} {flow.request.pretty_url} HTTP/{flow.request.http_version}\n"
        )
        # Request headers
        for name, value in flow.request.headers.items():
            f.write(f"{name}: {value}\n")

        f.write("\n")  # blank line delimiter

        # **Complete status line** (no 'Status:' prefix)
        try:
            version = flow.response.http_version  # e.g. '1.1'
        except AttributeError:
            version = "1.1"
        reason = getattr(flow.response, "reason", "")
        f.write(f"HTTP/{version} {flow.response.status_code} {reason}\n")

        # Response headers (omit hop‑by‑hop / size headers)
        for name, value in flow.response.headers.items():
            low = name.lower()
            if low in {"transfer-encoding", "content-length"}:
                continue
            f.write(f"{name}: {value}\n")

    flow.response.headers["x-mitmp-cached-filename"] = base
