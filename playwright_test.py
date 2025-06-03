#!.venv/bin/python
# RIS Extractor -- Copyright (C) 2025  Claire Xenia Wolf <claire@clairexen.net>
# Shared freely under ISC license (https://en.wikipedia.org/wiki/ISC_license)

from playwright.sync_api import sync_playwright
import time, getopt, sys

# Remember to launch
#   mitmproxy --mode regular --listen-port 8080 -s mitmp_cache.py
# (or similar) when using useProxyMode.
useProxyMode = True

useHeadlessMode = True
printHttpRequests = False


#%% Usage + Getopt

def usage():
    print()
    print(f"Usage: {sys.argv[0]} [options]")
    print()
    print("    -P, --no-proxy ...... do not use local proxy on port 8080")
    print("    -H, --no-headless ... no headless mode (i.e. show browser window)")
    print("    -r, --print-http .... print a log line for each HTTP request")
    print()
    print("Note: Run 'mitmproxy -s mitmp_cache.py' (or mitmweb) in another")
    print("terminal window for a simple local proxy when -P is not used.")
    print()

try:
    opts, args = getopt.getopt(sys.argv[1:], "ho:PHr",
                               ["help", "output=", "no-proxy", "no-headless",
                                "print-http"])
except getopt.GetoptError as err:
    # print help information and exit:
    print(err)  # will print something like "option -a not recognized"
    usage()
    sys.exit(2)

for o, a in opts:
    if o in ("-h", "--help"):
        usage()
        sys.exit()
    elif o in ("-P", "--no-proxy"):
        useProxyMode = False
    elif o in ("-H", "--no-headless"):
        useHeadlessMode = False
    elif o in ("-r", "--print-http"):
        printHttpRequests = True
    #elif o in ("-o", "--output"):
    #    output = a
    else:
        assert False, "unhandled option"


#%% Initialize Browser Context

playwright = sync_playwright().start()

if useProxyMode:
    browser = playwright.chromium.launch(
        headless=useHeadlessMode,
        proxy={"server": "http://127.0.0.1:8080"},
        args=["--ignore-certificate-errors"],
    )
    context = browser.new_context(
        ignore_https_errors=True,  # this is also required
    )
else:
    browser = playwright.chromium.launch(
        headless=useHeadlessMode,
    )
    context = browser.new_context(
    )

page = context.new_page()

if printHttpRequests:
    page.on("request", lambda request: print(f"> {request.method} {request.url}"))


#%% Actual Playwright Script

page.goto("https://example.com/")
print(page.title())


#%% Shutdown Playwright

if not useHeadlessMode:
    time.sleep(3)
browser.close()

playwright.stop()
