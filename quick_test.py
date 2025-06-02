#!.venv/bin/python
# RIS Extractor -- Copyright (C) 2025  Claire Xenia Wolf <claire@clairexen.net>
# Shared freely under ISC license (https://en.wikipedia.org/wiki/ISC_license)

from playwright.sync_api import sync_playwright
import requests
import time

useMitmProxyMode = False    # Remember to launch "mitmproxy --mode regular --listen-port 8080"
useHeadlessMode = True

def log_request(request):
    print(f"> {request.method} {request.url}")

with sync_playwright() as p:
    if useMitmProxyMode:
        browser = p.chromium.launch(
            headless=useHeadlessMode,
            proxy={"server": "http://127.0.0.1:8080"},
            args=["--ignore-certificate-errors"],
        )
        context = browser.new_context(
            ignore_https_errors=True,  # this is also required
        )
    else:
        browser = p.chromium.launch(
            headless=useHeadlessMode,
        )
        context = browser.new_context(
        )

    page = context.new_page()
    page.on("request", log_request)

    page.goto("https://example.com/")
    print(page.title())
    
    if not useHeadlessMode:
        time.sleep(3)
    browser.close()
