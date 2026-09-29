"""Offline checks on the canvas (HTML mode) template: the builder regenerates frames, every data-in/slot
references a slide in the table, and copy conversion round-trips."""
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "src" / "presentation_skill" / "templates" / "examples" / "html"


def _copy(tmp_path: Path) -> Path:
    deck = tmp_path / "deck"
    shutil.copytree(TEMPLATE, deck)
    return deck


def test_builder_regenerates_frames(tmp_path: Path):
    deck = _copy(tmp_path)
    subprocess.run([sys.executable, "tools/build_index.py"], cwd=deck, check=True, capture_output=True)
    html = (deck / "index.html").read_text(encoding="utf-8")
    assert html.count('class="frame"') == 5
    assert html.count("FRAMES:BEGIN") == 1 and html.count("FRAMES:END") == 1


def test_markup_references_known_slides(tmp_path: Path):
    deck = _copy(tmp_path)
    ids = set(re.findall(r'S\("([a-z_0-9]+)"', (deck / "js" / "deck.js").read_text(encoding="utf-8")))
    html = (deck / "index.html").read_text(encoding="utf-8")
    frames = set(re.findall(r'<div class="frame" id="([a-z_0-9]+)"', html))
    assert frames == ids
    refs = re.findall(r'data-(?:in|out|count|bar|follow)="([a-z_0-9]+)\.\d+"', html)
    refs += [t.split("@")[1].split(".")[0] for s in re.findall(r'data-state="([^"]+)"', html) for t in s.split()]
    assert set(refs) - {"end"} <= ids


def test_copy_round_trip(tmp_path: Path):
    deck = _copy(tmp_path)
    subprocess.run([sys.executable, "tools/copy_to_js.py"], cwd=deck, check=True, capture_output=True)
    js = (deck / "js" / "copy.js").read_text(encoding="utf-8")
    html = (deck / "index.html").read_text(encoding="utf-8")
    for slot in re.findall(r'data-slot="([a-z_0-9]+)\.([a-z_0-9]+)"', html):
        assert f'"{slot[1]}"' in js, slot


def test_engine_keeps_canvas_on_phones_and_navigates_by_touch():
    engine = (TEMPLATE / "js" / "engine.js").read_text(encoding="utf-8")
    css = (TEMPLATE / "css" / "deck.css").read_text(encoding="utf-8")
    # Reveal 5 turns viewports narrower than 435 px into scroll view, which bypasses the canvas.
    assert "scrollActivationWidth: null" in engine
    assert "touch: false" in engine
    assert 'addEventListener("touchend"' in engine
    assert "[data-no-nav]" in engine
    assert re.search(r"html,\s*body\s*\{\s*touch-action:\s*manipulation;\s*\}", css)



def test_engine_has_navigator_with_per_frame_final_state():
    engine = (TEMPLATE / "js" / "engine.js").read_text(encoding="utf-8")
    css = (TEMPLATE / "css" / "deck.css").read_text(encoding="utf-8")
    assert "function openNav()" in engine and "function closeNav(k)" in engine
    # the overview shows every frame complete: apply() has a per-frame mode keyed on each frame's final step
    assert "function apply(globalCur, animate, perFrame)" in engine
    assert "FRAME_FINAL" in engine and "apply(here.cur, false, true)" in engine
    assert 'navBtn.id = "navbtn"' in engine and 'hud.id = "navhud"' in engine
    # Reveal's keyboard is suspended while open, the key listener runs in the capture phase, touch is ignored
    assert "Reveal.configure({ keyboard: false })" in engine and "Reveal.configure({ keyboard: true })" in engine
    assert re.search(r'addEventListener\("keydown",[\s\S]*?\}, true\);', engine)
    assert "e.touches.length !== 1 || nav" in engine
    nav_css = css[css.index("/* ---------- navigator"):]
    for selector in ("body.nav-open .frame", ".navlabel", "#navhud", "#navbtn", "body.nav-snap .frame"):
        assert selector in nav_css, selector
    assert "html.pdf-export #navbtn" in nav_css  # the exporter prints with screen media


# ---------------------------------------------------------------- browser: touch navigation on a phone

from test_export_html_pdf import needs_browser, stub_deck  # noqa: E402,F401  (stub Reveal, loopback server)


@needs_browser
def test_browser_touch_navigation_on_portrait_phone(stub_deck: Path):
    import functools
    import http.server
    import threading

    from playwright.sync_api import sync_playwright

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(stub_deck))
    handler.func.log_message = lambda *args: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            ctx = browser.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True)
            page = ctx.new_page()
            page.goto(f"http://127.0.0.1:{srv.server_address[1]}/index.html#/2")
            page.wait_for_function("document.body.classList.contains('ready')")
            pos = lambda: page.evaluate("(() => { const i = Reveal.getIndices(); return i.h * 100 + (i.f == null ? -1 : i.f); })()")
            assert pos() == 199  # slide index 2, no fragment shown yet
            assert page.text_content("#folio") == "03 / 05"

            cdp = ctx.new_cdp_session(page)

            def touch(kind, points):
                cdp.send("Input.dispatchTouchEvent", {
                    "type": kind, "touchPoints": [{"x": x, "y": y, "id": i} for i, (x, y) in enumerate(points)],
                })

            def swipe(x0, x1, y=420):
                touch("touchStart", [(x0, y)])
                for k in range(1, 9):
                    touch("touchMove", [(x0 + (x1 - x0) * k / 8, y)])
                touch("touchEnd", [])

            page.touchscreen.tap(330, 420)  # right side: next
            assert pos() == 200
            page.touchscreen.tap(40, 420)  # left 30%: back
            assert pos() == 199
            swipe(320, 120)  # swipe left: next
            assert pos() == 200
            swipe(120, 320)  # swipe right: back
            assert pos() == 199

            touch("touchStart", [(150, 400)])  # two-finger pinch: no navigation
            touch("touchStart", [(150, 400), (240, 460)])
            for k in range(1, 8):
                touch("touchMove", [(150 - 10 * k, 400 - 10 * k), (240 + 10 * k, 460 + 10 * k)])
            touch("touchEnd", [(80, 330)])
            touch("touchEnd", [])
            assert pos() == 199

            page.mouse.click(330, 420)  # mouse clicks never navigate
            assert pos() == 199
            assert page.evaluate("getComputedStyle(document.body).touchAction") == "manipulation"
            browser.close()
    finally:
        srv.shutdown()


# ---------------------------------------------------------------- browser: the navigator


@needs_browser
def test_browser_navigator_overview_select_dive_and_escape(stub_deck: Path):
    import functools
    import http.server
    import threading

    from playwright.sync_api import sync_playwright

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(stub_deck))
    handler.func.log_message = lambda *args: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 720})
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.goto(f"http://127.0.0.1:{srv.server_address[1]}/index.html#/0")
            page.wait_for_function("document.body.classList.contains('ready')")
            pos = lambda: page.evaluate("(() => { const i = Reveal.getIndices(); return i.h * 100 + (i.f == null ? -1 : i.f); })()")
            has = lambda sel, cls: page.evaluate(f"document.querySelector({sel!r}).classList.contains({cls!r})")
            nav_open = lambda: has("body", "nav-open")
            closed = "!document.body.classList.contains('nav-open')"
            assert pos() == -1
            assert not has('#close [data-in="close.1"]', "on")

            # M opens the overview: every frame labelled and shown in its own final state
            page.keyboard.press("m")
            assert nav_open()
            assert page.evaluate("[...document.querySelectorAll('.frame')].every(f => f.querySelectorAll(':scope > .navlabel').length === 1)")
            assert page.evaluate("document.querySelectorAll('.frame').length") == 5
            assert has('#close [data-in="close.1"]', "on")          # last step of the last slide
            assert has('#numbers [data-in="numbers.2"]', "on")
            assert has('#pipeline [data-in="pipeline.2"]', "on")
            assert has("#split .specimen", "split")                  # data-state range reached
            assert page.evaluate("[...document.querySelectorAll('[data-count]')].map(e => e.textContent)") == ["6.2", "18.7"]
            assert has("#title", "nav-sel") and page.text_content("#navhud b") == "01"

            # arrows move the selection and never reach Reveal
            page.keyboard.press("ArrowRight")
            assert has("#pipeline", "nav-sel") and not has("#title", "nav-sel")
            assert page.text_content("#navhud b") == "02"
            assert pos() == -1

            # Enter dives into the selection; the layout and the global state come back
            page.keyboard.press("Enter")
            page.wait_for_function(closed, timeout=5000)
            assert pos() == 99
            assert page.evaluate("document.getElementById('pipeline').style.left") == "2200px"
            assert not has('#close [data-in="close.1"]', "on")
            assert not has('#pipeline [data-in="pipeline.2"]', "on")

            # M, move the selection, Esc: back where we were, nothing navigated
            page.keyboard.press("m")
            assert nav_open()
            page.keyboard.press("ArrowRight")
            page.keyboard.press("ArrowRight")
            assert has("#numbers", "nav-sel")
            page.keyboard.press("Escape")
            page.wait_for_function(closed, timeout=5000)
            assert pos() == 99

            # Reveal's keyboard is back
            page.keyboard.press("ArrowRight")
            assert pos() == 100

            # the corner button opens it too; hover selects, a typed number selects, Enter goes there
            page.click("#navbtn")
            assert nav_open()
            page.wait_for_timeout(1500)                              # let the camera and the frames land
            box = page.locator("#numbers").bounding_box()
            page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            assert has("#numbers", "nav-sel")
            page.keyboard.press("5")
            assert has("#close", "nav-sel") and not has("#numbers", "nav-sel")
            page.keyboard.press("Enter")
            page.wait_for_function(closed, timeout=5000)
            assert pos() == 399

            page.evaluate("document.documentElement.classList.add('pdf-export')")
            assert page.evaluate("getComputedStyle(document.getElementById('navbtn')).display") == "none"
            assert errors == []
            browser.close()
    finally:
        srv.shutdown()


def test_world_layer_is_promoted_only_while_the_camera_flies():
    engine = (TEMPLATE / "js" / "engine.js").read_text(encoding="utf-8")
    css = (TEMPLATE / "css" / "deck.css").read_text(encoding="utf-8")
    world_rule = re.search(r"#world\s*\{[^}]*\}", css).group(0)
    assert "will-change" not in world_rule          # a permanent layer rasterises at 1x and blurs deep zooms
    assert 'world.style.willChange = "transform"' in engine and 'world.style.willChange = "auto"' in engine
