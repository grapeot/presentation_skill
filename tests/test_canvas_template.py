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


def test_dev_server_reloads_on_everything_a_canvas_deck_loads():
    server = (ROOT / "src" / "presentation_skill" / "templates" / "common" / "start-server.py").read_text(encoding="utf-8")
    watched = set(re.findall(r"server\.watch\('([^']+)'\)", server))
    for pattern in ("*.html", "js/**/*.js", "css/**/*.css", "imgs/**/*", "assets/**/*"):
        assert pattern in watched, pattern


# ---------------------------------------------------------------- jumps, appendix, notes, navigator input


def test_engine_has_jumps_appendix_and_navigator_input():
    engine = (TEMPLATE / "js" / "engine.js").read_text(encoding="utf-8")
    css = (TEMPLATE / "css" / "deck.css").read_text(encoding="utf-8")
    # frames are looked up inside the world, so a Reveal section with the same id can never shadow one
    assert 'world.querySelector("#" + CSS.escape(f))' in engine and "document.getElementById(f)" not in engine
    # jump chips with a return stack (R), and an appendix that plain "next" never walks into
    assert 'closest("[data-goto]")' in engine and "back.pop()" in engine and "s.appendix && !jumping" in engine
    # the overview takes a scroll wheel and shows the digits being typed
    assert 'addEventListener("wheel"' in engine and "{ passive: false }" in engine and "function typeKey(ch)" in engine
    # speaker notes: [click] cues are numbered, bracketed paragraphs render as stage directions
    assert "▶ click" in engine and "click cues" in engine
    # a chip that has not appeared yet cannot be clicked
    assert "[data-in]:not(.on) [data-goto]" in css


def _run(deck: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], cwd=deck, capture_output=True, text=True)


def test_copy_to_js_checks_click_cues_and_the_breath_gate(tmp_path: Path):
    deck = _copy(tmp_path)
    md = deck / "copy" / "copy.md"
    good = "Stages arrive in order.\n\n[click]\n\n[Point at the constraint box.]\n\nThen the constraint appears.\n\n[click]\n\nThen the takeaway."
    base = md.read_text(encoding="utf-8")
    old = "Stages arrive in order, then the constraint appears, then the takeaway."
    md.write_text(base.replace(old, good), encoding="utf-8")
    assert _run(deck, "tools/copy_to_js.py").returncode == 0
    md.write_text(base.replace(old, good.replace("\n\n[click]\n\nThen the takeaway.", " Then the takeaway.")), encoding="utf-8")
    r = _run(deck, "tools/copy_to_js.py")
    assert r.returncode == 1 and "pipeline: 1 [click] cues, the slide has 2 clicks" in r.stdout
    long = " ".join(["word"] * 23) + "."
    md.write_text(base.replace(old, long), encoding="utf-8")
    r = _run(deck, "tools/copy_to_js.py")
    assert r.returncode == 1 and "23-word sentence" in r.stdout


def test_publish_stages_runtime_files_without_notes(tmp_path: Path):
    deck = _copy(tmp_path)
    (deck / "vendor" / "reveal").mkdir(parents=True)
    (deck / "vendor" / "reveal" / "reveal.js").write_text("", encoding="utf-8")
    assert _run(deck, "tools/publish.py").returncode == 0
    dist = deck / "dist"
    assert (dist / "index.html").is_file() and (dist / "js" / "engine.js").is_file()
    assert not (dist / "copy").exists() and not (dist / "tools").exists()
    copy_js = (dist / "js" / "copy.js").read_text(encoding="utf-8")
    assert "Every click either draws something" not in copy_js and '"notes": ""' in copy_js
    assert all(p.stat().st_mode & 0o004 for p in dist.rglob("*"))           # world-readable, or the web server 403s
    assert _run(deck, "tools/publish.py", "--out", "../outside").returncode != 0


def test_present_mode_serves_without_live_reload():
    server = (ROOT / "src" / "presentation_skill" / "templates" / "common" / "start-server.py").read_text(encoding="utf-8")
    assert '"--present"' in server and "def start_present_server" in server
    # livereload is imported only by the editing server, so --present runs without it
    assert "from livereload import Server" in server.split("def start_server", 1)[1]


@needs_browser
def test_browser_jump_return_appendix_guard_and_wheel(stub_deck: Path):
    import functools
    import http.server
    import threading

    from playwright.sync_api import sync_playwright

    table = stub_deck / "js" / "deck.js"
    table.write_text(table.read_text(encoding="utf-8").replace(
        'S("close", "IV · Say it", 2),',
        'S("close", "IV · Say it", 2),\n    S("extra", "Appendix", 1, null, { appendix: true, frame: "title" }),'), encoding="utf-8")
    index = stub_deck / "index.html"
    index.write_text(index.read_text(encoding="utf-8").replace(
        "</body>",
        "<script>document.getElementById('close').insertAdjacentHTML('beforeend',"
        " '<button class=\"jump\" type=\"button\" data-goto=\"extra.0\" style=\"position:absolute;left:160px;top:900px\">Appendix</button>');"
        "</script>\n</body>"), encoding="utf-8")
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
            closed = "!document.body.classList.contains('nav-open')"
            assert page.text_content("#folio") == "01 / 05"         # the appendix is not counted

            # "next" at the very end stays out of the appendix
            page.evaluate("deckGoto(4, 1)")
            page.keyboard.press("ArrowRight")
            assert pos() == 400

            # the chip jumps into the appendix; R returns to the exact slide and step
            page.click("#close .jump")
            assert pos() == 499 and page.text_content("#folio") == "A1 / 05"
            page.keyboard.press("r")
            assert pos() == 400

            # a chip that has not appeared yet ignores clicks
            page.evaluate("deckGoto(4, 0)")
            page.evaluate("document.querySelector('#close .jump').setAttribute('data-in', 'close.1')")
            page.evaluate("deckGoto(4, 0)")
            assert page.evaluate("getComputedStyle(document.querySelector('#close .jump')).pointerEvents") == "none"

            # overview: typed digits show in the HUD; the wheel moves one frame per notch
            page.evaluate("deckGoto(0, 0)")
            page.keyboard.press("m")
            page.keyboard.press("0")
            assert page.text_content("#navhud b") == "0_"
            page.keyboard.press("3")
            assert page.text_content("#navhud b") == "03_"
            page.keyboard.press("Escape")
            page.wait_for_function(closed, timeout=5000)
            page.mouse.move(1, 1)                                    # park the pointer: hover also selects
            page.keyboard.press("m")
            page.wait_for_timeout(1500)
            assert page.text_content("#navhud b") == "01"
            page.mouse.wheel(0, 130)
            assert page.text_content("#navhud b") == "03"           # 130 px of travel: two notches from 01
            page.keyboard.press("Enter")
            page.wait_for_function(closed, timeout=5000)
            assert pos() == 199
            page.keyboard.press("r")
            assert pos() == -1
            assert errors == []
            browser.close()
    finally:
        srv.shutdown()
