"""Screenshot every step of the deck, build contact sheets, and report problems.

usage: python3 tools/shoot.py [--out verification/round1] [--only slide_a,slide_b] [--wait 3.0] [--port 8791]

Reports: console errors, failed requests, any request that leaves localhost (the deck must run offline),
and copy slots that were not filled. Give every critic round its own --out directory; never re-shoot into a
directory a reviewer is reading.
Requires: playwright (python) with a Chromium install, Pillow.
"""
import argparse, functools, http.server, json, pathlib, threading, time
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw

D = pathlib.Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser()
ap.add_argument("--only", default="")
ap.add_argument("--wait", type=float, default=3.0, help="seconds to let transitions settle per step")
ap.add_argument("--out", default="verification/shots")
ap.add_argument("--port", type=int, default=8791)
a = ap.parse_args()
out = D / a.out
out.mkdir(parents=True, exist_ok=True)

handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(D))
http.server.SimpleHTTPRequestHandler.log_message = lambda *args: None
srv = http.server.ThreadingHTTPServer(("127.0.0.1", a.port), handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{a.port}"

errors, failed, external, shots = [], [], [], []
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" or "unknown slide id" in m.text or "missing frame" in m.text else None)
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("requestfailed", lambda r: failed.append(r.url))
    pg.on("request", lambda r: external.append(r.url) if not (r.url.startswith(base) or r.url.startswith("data:")) else None)
    pg.goto(f"{base}/index.html")
    pg.wait_for_function("document.body.classList.contains('ready')")
    time.sleep(1.5)
    deck = pg.evaluate("window.DECK.map(s => [s.id, s.steps])")
    only = set(filter(None, a.only.split(",")))
    for i, (sid, n) in enumerate(deck):
        if only and sid not in only:
            continue
        for st in range(n):
            pg.evaluate(f"deckGoto({i}, {st})")
            time.sleep(a.wait)
            f = out / f"{sid}_{st}.png"
            pg.screenshot(path=str(f))
            shots.append((f"{sid}.{st}", f))
    missing = pg.evaluate("[...document.querySelectorAll('.missing')].map(e => e.dataset.slot)")
    b.close()
srv.shutdown()

W, H = 480, 270
for k in range(0, len(shots), 12):
    chunk = shots[k:k + 12]
    sheet = Image.new("RGB", (W * 4, (H + 24) * 3), "white")
    d = ImageDraw.Draw(sheet)
    for j, (label, f) in enumerate(chunk):
        im = Image.open(f).convert("RGB").resize((W, H), Image.LANCZOS)
        x, y = (j % 4) * W, (j // 4) * (H + 24)
        sheet.paste(im, (x, y))
        d.text((x + 6, y + H + 5), label, fill="black")
    sheet.save(out / f"sheet_{k // 12:02d}.jpg", quality=86)

report = {"shots": len(shots), "errors": errors[:20], "failed": failed[:20], "external": external[:20], "missing_slots": missing}
print(json.dumps(report, indent=1))
raise SystemExit(1 if (errors or failed or external or missing) else 0)
