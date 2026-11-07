"""Render a 1080x1350 post HTML file to PNG.
Usage: python3 _post/render.py _post/weekly.html /home/claude/posts/weekly.png
Needs Playwright and Google Chrome (/usr/bin/google-chrome) and the Inter fonts installed locally."""
import sys, pathlib
from playwright.sync_api import sync_playwright
src, out = pathlib.Path(sys.argv[1]).resolve(), pathlib.Path(sys.argv[2])
out.parent.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    pg = b.new_page(viewport={"width": 1080, "height": 1350})
    pg.goto(src.as_uri()); pg.wait_for_timeout(300)
    pg.screenshot(path=str(out), clip={"x": 0, "y": 0, "width": 1080, "height": 1350})
    b.close()
print("wrote", out)
