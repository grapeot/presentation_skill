"""Export a canvas (Reveal-mode) deck to a vector PDF through headless Chromium.

A canvas deck has no stable pages: frames live on one moving sheet and every
slide has several click states. Browser printing keeps one arbitrary state per
slide and drops the notes. This exporter instead picks one *print state* per
slide and prints exactly that state.

Contract with the deck (the same one ``tools/shoot.py`` relies on):

- ``js/engine.js`` exists and ``js/deck.js`` defines ``window.DECK``, an array of
  ``{id, steps, print?}`` entries in speaking order;
- the page exposes ``window.deckGoto(slideIndex, step)``, which applies a state
  without animating;
- copy slots that could not be filled carry the class ``missing``;
- speaker notes come from ``window.COPY[slideId].notes`` or, failing that, from
  the Reveal ``<aside class="notes">`` of the slide.

Nothing else about the deck's engine or CSS is assumed.

Page selection: one page per slide, at ``print`` if the slide entry sets it,
otherwise at the slide's last step (``steps - 1``).

Rendering: the deck is served by a private static HTTP server on a free
loopback port, loaded at a 1920x1080 viewport with *screen* media emulated (so
Reveal's print stylesheet never applies), transitions and CSS animations are
switched off, and every state is applied instantly. Each state is printed with
``page.pdf`` at 1920x1080 px (one page, backgrounds on), and the pages are
merged with pypdf. Text stays vector and selectable; DOM links become PDF link
annotations.

During export ``<html>`` carries the class ``pdf-export`` and the attributes
``data-print-slide`` / ``data-print-step``, so a deck can supply a dedicated
handout layout in CSS for a slide whose final state hides information.

The export fails loudly (:class:`HtmlExportError`) on console errors, failed
or non-loopback requests, unfilled copy slots, fonts that failed to load,
invalid ``print`` values, or a page count that does not match the plan.
"""

from __future__ import annotations

import contextlib
import functools
import http.server
import io
import ipaddress
import shutil
import subprocess
import tempfile
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator
from urllib.parse import urlsplit

WIDTH, HEIGHT = 1920, 1080
# page.pdf sizes in CSS px; 1 px = 0.75 pt, so every page is 1440 x 810 pt.
PAGE_PT = (WIDTH * 0.75, HEIGHT * 0.75)

INSTALL_HINT = (
    "pip install 'presentation-skill[pdf-html]' && python -m playwright install chromium"
)

# Engine warnings that mean the slide table and the markup disagree.
_ENGINE_WARNINGS = ("unknown slide id", "missing frame")

# Injected after load: no transitions, CSS animations finish instantly (so
# fill-mode end states still apply), no blinking caret.
FREEZE_CSS = """
*, *::before, *::after {
  transition: none !important;
  animation-duration: 0s !important;
  animation-delay: 0s !important;
  animation-iteration-count: 1 !important;
  caret-color: transparent !important;
}
"""

NOTES_CSS = """
#__pdf_notes__ { position: fixed; inset: 0; width: 1920px; height: 1080px; z-index: 2147483647;
  box-sizing: border-box; padding: 88px 120px 80px; display: none; flex-direction: column;
  font-family: inherit; -webkit-font-smoothing: antialiased; }
#__pdf_notes__.show { display: flex; }
html.pdf-notes body > *:not(#__pdf_notes__), html.pdf-notes body > *:not(#__pdf_notes__) * {
  visibility: hidden !important; }
#__pdf_notes__ .nh { display: flex; justify-content: space-between; align-items: baseline;
  font-size: 20px; letter-spacing: .12em; text-transform: uppercase; opacity: .62;
  padding-bottom: 22px; border-bottom: 1px solid currentColor; }
#__pdf_notes__ .nb { flex: 1; min-height: 0; overflow: hidden; margin-top: 40px;
  column-count: 2; column-gap: 88px; column-fill: auto; }
#__pdf_notes__ .nb p { margin: 0 0 .75em; break-inside: avoid-column; }
#__pdf_notes__ .nb.empty { column-count: 1; font-style: italic; opacity: .55; }
"""


class HtmlExportError(RuntimeError):
    """The canvas deck could not be exported without a problem showing up in the PDF."""

    def __init__(self, problems: list[str]):
        self.problems = list(problems)
        super().__init__(
            "Canvas PDF export failed:\n" + "\n".join(f"  - {p}" for p in self.problems)
        )


class MissingDependencyError(RuntimeError):
    """Playwright, Chromium, pypdf, Pillow or a PDF rasterizer is not available."""


@dataclass
class SlideInfo:
    index: int
    id: str
    steps: int
    print: object = None  # raw value from deck.js; validated by resolve_print_step
    part: str = ""
    notes: str = ""


@dataclass
class PageSpec:
    kind: str  # "slide" or "notes"
    slide_index: int
    slide_id: str
    step: int

    @property
    def label(self) -> str:
        if self.kind == "notes":
            return f"{self.slide_index + 1:02d} {self.slide_id} · notes"
        return f"{self.slide_index + 1:02d} {self.slide_id} · step {self.step}"


@dataclass
class HtmlExportResult:
    output: Path | None
    slides: int
    pages: int
    plan: list[PageSpec] = field(default_factory=list)
    contact_sheets: list[Path] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------- pure logic


def is_canvas_deck(deck_dir: Path) -> bool:
    """A canvas deck has index.html, js/engine.js and a slide table in js/deck.js."""
    deck_dir = Path(deck_dir)
    deck_js = deck_dir / "js" / "deck.js"
    if not (
        (deck_dir / "index.html").is_file()
        and (deck_dir / "js" / "engine.js").is_file()
        and deck_js.is_file()
    ):
        return False
    return "window.DECK" in deck_js.read_text(encoding="utf-8", errors="replace")


def resolve_print_step(slide: SlideInfo) -> int:
    """Return the step printed for ``slide``: its ``print`` field, else its last step."""
    if slide.print is None:
        return slide.steps - 1
    value = slide.print
    if isinstance(value, bool) or not isinstance(value, (int, float)) or int(value) != value:
        raise ValueError(
            f"slide {slide.id!r}: print must be a step index (integer), got {value!r}"
        )
    value = int(value)
    if not 0 <= value < slide.steps:
        raise ValueError(
            f"slide {slide.id!r}: print={value} is outside its steps (0..{slide.steps - 1})"
        )
    return value


def slides_from_table(table: list[dict]) -> list[SlideInfo]:
    """Normalise the raw ``window.DECK`` rows collected from the page."""
    problems: list[str] = []
    slides: list[SlideInfo] = []
    seen: set[str] = set()
    for i, row in enumerate(table):
        sid = row.get("id")
        if not isinstance(sid, str) or not sid:
            problems.append(f"DECK[{i}] has no id")
            sid = f"slide_{i + 1}"
        elif sid in seen:
            problems.append(f"DECK[{i}]: duplicate slide id {sid!r}")
        seen.add(sid)
        steps = row.get("steps")
        if steps is None:
            steps = 1
        if isinstance(steps, bool) or not isinstance(steps, (int, float)) or int(steps) != steps or steps < 1:
            problems.append(f"slide {sid!r}: steps must be a positive integer, got {steps!r}")
            steps = 1
        slides.append(
            SlideInfo(
                index=i,
                id=sid,
                steps=int(steps),
                print=row.get("print"),
                part=row.get("part") or "",
                notes=row.get("notes") or "",
            )
        )
    if not slides:
        problems.append("window.DECK is empty")
    if problems:
        raise HtmlExportError(problems)
    return slides


def plan_pages(slides: list[SlideInfo], with_notes: bool = False) -> list[PageSpec]:
    """One page per slide at its print state, each followed by a notes page if asked."""
    problems: list[str] = []
    pages: list[PageSpec] = []
    for s in slides:
        try:
            step = resolve_print_step(s)
        except ValueError as exc:
            problems.append(str(exc))
            continue
        pages.append(PageSpec("slide", s.index, s.id, step))
        if with_notes:
            pages.append(PageSpec("notes", s.index, s.id, step))
    if problems:
        raise HtmlExportError(problems)
    return pages


def expected_page_count(n_slides: int, with_notes: bool) -> int:
    return n_slides * (2 if with_notes else 1)


def default_output(deck_dir: Path, with_notes: bool = False) -> Path:
    name = "handout_with_notes.pdf" if with_notes else "handout.pdf"
    return Path(deck_dir) / "verification" / name


def is_local_url(url: str) -> bool:
    """True for loopback http(s) URLs and inline schemes; everything else leaves the machine."""
    parts = urlsplit(url)
    if parts.scheme in {"data", "blob", "about"}:
        return True
    if parts.scheme not in {"http", "https", "ws", "wss"}:
        return False
    host = (parts.hostname or "").lower()
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def split_notes(text: str) -> list[str]:
    """Paragraphs of a notes string (blank-line separated, inner newlines folded)."""
    paras = []
    for block in text.replace("\r\n", "\n").split("\n\n"):
        para = " ".join(line.strip() for line in block.splitlines() if line.strip())
        if para:
            paras.append(para)
    return paras


# ---------------------------------------------------------------- dependencies


def _require_playwright():
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError as exc:
        raise MissingDependencyError(
            "Canvas-deck PDF export needs Playwright with Chromium, which is not installed.\n"
            f"  Install it with: {INSTALL_HINT}"
        ) from exc
    return sync_playwright


def _require_pypdf():
    try:
        from pypdf import PdfReader, PdfWriter  # type: ignore
    except ImportError as exc:
        raise MissingDependencyError(
            f"Canvas-deck PDF export needs pypdf. Install it with: {INSTALL_HINT}"
        ) from exc
    return PdfReader, PdfWriter


def find_rasterizer() -> str | None:
    """'pymupdf' or 'pdftoppm', whichever is available (pymupdf first)."""
    try:
        import pymupdf  # type: ignore  # noqa: F401

        return "pymupdf"
    except ImportError:
        pass
    try:
        import fitz  # type: ignore  # noqa: F401

        return "pymupdf"
    except ImportError:
        pass
    if shutil.which("pdftoppm"):
        return "pdftoppm"
    return None


# ---------------------------------------------------------------- local server


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".js": "text/javascript",
        ".mjs": "text/javascript",
        ".css": "text/css",
        ".svg": "image/svg+xml",
        ".woff2": "font/woff2",
        ".woff": "font/woff",
        ".wasm": "application/wasm",
        ".json": "application/json",
    }

    def log_message(self, *args):  # pragma: no cover - silence
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


@contextlib.contextmanager
def serve_directory(directory: Path) -> Iterator[str]:
    """Serve ``directory`` on a free loopback port; yields the base URL."""
    handler = functools.partial(_QuietHandler, directory=str(directory))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()


# ---------------------------------------------------------------- page scripts

_JS_READY = """() => typeof window.deckGoto === 'function' && Array.isArray(window.DECK)
  && (!window.Reveal || typeof Reveal.isReady !== 'function' || Reveal.isReady())"""

_JS_TABLE = """() => {
  const copy = window.COPY || {};
  const sections = (window.Reveal && typeof Reveal.getSlides === 'function') ? Reveal.getSlides() : [];
  return window.DECK.map((s, i) => {
    let notes = (copy[s.id] && typeof copy[s.id].notes === 'string') ? copy[s.id].notes : '';
    if (!notes.trim() && sections[i]) {
      const aside = sections[i].querySelector('aside.notes');
      if (aside) {
        const ps = [...aside.querySelectorAll('p')];
        notes = ps.length ? ps.map(p => p.textContent.trim()).join('\\n\\n') : aside.textContent;
      }
    }
    return { id: s.id, steps: s.steps, print: s.print === undefined ? null : s.print,
             part: s.part || '', notes: notes || '' };
  });
}"""

_JS_MISSING = """() => [...document.querySelectorAll('.missing')].map(e =>
  e.dataset.slot || e.id || e.outerHTML.slice(0, 80))"""

# Finish JS-driven Web Animations (finite ones jump to their end, infinite ones rest at t=0),
# then wait until the DOM stops changing for a few frames (rAF-driven counters, camera, hooks),
# then wait for fonts and images.
_JS_SETTLE = """async ({frames, timeout}) => {
  const settleAnimations = () => {
    for (const a of document.getAnimations()) {
      try {
        const t = a.effect && a.effect.getComputedTiming();
        if (t && t.iterations !== Infinity && t.endTime !== Infinity) a.finish();
        else { a.pause(); a.currentTime = 0; }
      } catch (e) { /* ignore */ }
    }
  };
  const sig = () => {
    const h = document.body.innerHTML; let x = 0;
    for (let i = 0; i < h.length; i++) x = (x * 31 + h.charCodeAt(i)) | 0;
    return h.length + ':' + x;
  };
  const frame = () => new Promise(r => requestAnimationFrame(() => r()));
  settleAnimations();
  const t0 = performance.now(); let last = sig(), same = 0, stable = false;
  while (performance.now() - t0 < timeout) {
    await frame(); settleAnimations();
    const s = sig();
    if (s === last) { if (++same >= frames) { stable = true; break; } } else { same = 0; last = s; }
  }
  await document.fonts.ready;
  await Promise.all([...document.images].filter(i => i.src && !i.complete)
    .map(i => new Promise(r => { i.onload = i.onerror = r; })));
  await frame(); await frame();
  return stable;
}"""

_JS_GOTO = """([i, step, id]) => {
  window.deckGoto(i, step);
  const html = document.documentElement;
  html.dataset.printSlide = id; html.dataset.printStep = String(step);
  const n = document.getElementById('__pdf_notes__'); if (n) n.classList.remove('show');
  html.classList.remove('pdf-notes');
}"""

_JS_NOTES_INIT = r"""(css) => {
  const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
  const n = document.createElement('div'); n.id = '__pdf_notes__';
  n.innerHTML = '<div class="nh"><span class="nl"></span><span class="nr"></span></div><div class="nb"></div>';
  // Paper colour: the first opaque background that covers (nearly) the whole viewport.
  const clear = c => !c || c === 'transparent' || /rgba\(.*,\s*0\)$/.test(c);
  let bg = null;
  for (const el of document.elementsFromPoint(innerWidth / 2, innerHeight / 2)) {
    const r = el.getBoundingClientRect(), c = getComputedStyle(el).backgroundColor;
    if (!clear(c) && r.width >= innerWidth * 0.9 && r.height >= innerHeight * 0.9) { bg = c; break; }
  }
  const cs = getComputedStyle(document.body);
  n.style.background = bg || '#ffffff';
  n.style.color = cs.color || '#111111';
  document.body.appendChild(n);
}"""

_JS_NOTES_SHOW = """({paras, left, right}) => {
  const n = document.getElementById('__pdf_notes__');
  n.querySelector('.nl').textContent = left; n.querySelector('.nr').textContent = right;
  const body = n.querySelector('.nb'); body.innerHTML = ''; body.classList.toggle('empty', !paras.length);
  (paras.length ? paras : ['No speaker notes for this slide.']).forEach(t => {
    const p = document.createElement('p'); p.textContent = t; body.appendChild(p);
  });
  n.classList.add('show'); document.documentElement.classList.add('pdf-notes');
  // Largest size (30px down to 16px) at which the notes fit the two columns.
  let size = 30;
  const fits = () => body.scrollWidth <= body.clientWidth + 1 && body.scrollHeight <= body.clientHeight + 1;
  for (; size >= 16; size -= 1) {
    body.style.fontSize = size + 'px'; body.style.lineHeight = size <= 22 ? '1.45' : '1.5';
    if (fits()) return {size, fits: true};
  }
  return {size: 16, fits: false};
}"""

_JS_FONTS = """() => [...document.fonts].map(f => ({family: f.family, status: f.status,
  weight: f.weight, style: f.style}))"""


# ---------------------------------------------------------------- export


def _launch(p):
    try:
        return p.chromium.launch()
    except Exception as exc:  # playwright raises its own Error type
        msg = str(exc)
        if "Executable doesn't exist" in msg or "playwright install" in msg:
            raise MissingDependencyError(
                "Playwright is installed but its Chromium build is missing.\n"
                "  Install it with: python -m playwright install chromium"
            ) from exc
        raise


def export_canvas_pdf(
    deck_dir: Path,
    output: Path | None = None,
    *,
    with_notes: bool = False,
    contact_sheet: bool = True,
    check_only: bool = False,
    settle_timeout_ms: int = 4000,
    load_timeout_ms: int = 30000,
) -> HtmlExportResult:
    """Export a canvas deck to PDF (or, with ``check_only``, run the checks without printing).

    Raises :class:`HtmlExportError` when any check fails and
    :class:`MissingDependencyError` when Playwright/Chromium/pypdf/a rasterizer is missing.
    """
    deck_dir = Path(deck_dir).resolve()
    if not is_canvas_deck(deck_dir):
        raise HtmlExportError(
            [f"{deck_dir.name}: not a canvas deck (needs index.html, js/engine.js, window.DECK in js/deck.js)"]
        )
    sync_playwright = _require_playwright()
    PdfReader, PdfWriter = _require_pypdf()
    if contact_sheet and not check_only:
        _require_pillow()
        if find_rasterizer() is None:
            raise MissingDependencyError(
                "The contact sheet needs a PDF rasterizer: install pymupdf (pip install pymupdf) "
                "or poppler's pdftoppm, or pass --no-contact-sheet."
            )

    output = Path(output) if output else default_output(deck_dir, with_notes)
    errors: list[str] = []
    external: list[str] = []
    failed: list[str] = []
    warnings: list[str] = []
    chunks: list[bytes] = []

    def on_console(msg):
        text = msg.text
        if msg.type == "error" or any(w in text for w in _ENGINE_WARNINGS):
            errors.append(f"console {msg.type}: {text}")

    def on_route(route):
        url = route.request.url
        if is_local_url(url):
            route.continue_()
        else:
            external.append(url)
            route.abort()

    def on_failed(req):
        if is_local_url(req.url):
            failed.append(f"{req.url} ({req.failure})")

    def on_response(resp):
        if resp.status >= 400 and is_local_url(resp.url):
            failed.append(f"{resp.url} (HTTP {resp.status})")

    def raise_if_problems(stage: str):
        problems = []
        problems += [f"{stage}: {e}" for e in errors]
        problems += [f"{stage}: request left localhost: {u}" for u in dict.fromkeys(external)]
        problems += [f"{stage}: request failed: {u}" for u in dict.fromkeys(failed)]
        if problems:
            raise HtmlExportError(problems)

    with serve_directory(deck_dir) as base, sync_playwright() as p:
        browser = _launch(p)
        try:
            context = browser.new_context(
                viewport={"width": WIDTH, "height": HEIGHT}, device_scale_factor=1
            )
            context.route("**/*", on_route)
            context.add_init_script(
                "document.addEventListener('DOMContentLoaded', () => "
                "document.documentElement.classList.add('pdf-export'));"
            )
            page = context.new_page()
            page.on("console", on_console)
            page.on("pageerror", lambda e: errors.append(f"page error: {e}"))
            page.on("requestfailed", on_failed)
            page.on("response", on_response)
            page.emulate_media(media="screen")

            page.goto(f"{base}/index.html", wait_until="load", timeout=load_timeout_ms)
            try:
                page.wait_for_function(_JS_READY, timeout=load_timeout_ms)
            except Exception as exc:
                raise HtmlExportError(
                    errors
                    + [
                        "deck never became ready: window.DECK and window.deckGoto(i, step) must exist "
                        f"and Reveal must finish initialising ({type(exc).__name__})"
                    ]
                ) from exc
            page.add_style_tag(content=FREEZE_CSS)
            page.evaluate("() => document.fonts.ready.then(() => true)")

            slides = slides_from_table(page.evaluate(_JS_TABLE))
            plan = plan_pages(slides, with_notes)

            missing = page.evaluate(_JS_MISSING)
            if missing:
                errors.append("unfilled copy slots (.missing): " + ", ".join(missing))
            raise_if_problems("load")

            if with_notes:
                page.evaluate(_JS_NOTES_INIT, NOTES_CSS)

            if check_only:
                for spec in plan:
                    if spec.kind != "slide":
                        continue
                    page.evaluate(_JS_GOTO, [spec.slide_index, spec.step, spec.slide_id])
                    if not page.evaluate(_JS_SETTLE, {"frames": 3, "timeout": settle_timeout_ms}):
                        warnings.append(f"{spec.label}: DOM still changing after {settle_timeout_ms} ms")
                    missing = page.evaluate(_JS_MISSING)
                    if missing:
                        errors.append(f"{spec.label}: unfilled copy slots: " + ", ".join(missing))
            else:
                n = len(slides)
                for spec in plan:
                    slide = slides[spec.slide_index]
                    if spec.kind == "slide":
                        page.evaluate(_JS_GOTO, [spec.slide_index, spec.step, spec.slide_id])
                        if not page.evaluate(_JS_SETTLE, {"frames": 3, "timeout": settle_timeout_ms}):
                            warnings.append(
                                f"{spec.label}: DOM still changing after {settle_timeout_ms} ms; printed as is"
                            )
                    else:
                        left = f"Speaker notes · {slide.part}" if slide.part else "Speaker notes"
                        right = f"{spec.slide_index + 1:02d} / {n:02d} · {slide.id}"
                        fit = page.evaluate(
                            _JS_NOTES_SHOW,
                            {"paras": split_notes(slide.notes), "left": left, "right": right},
                        )
                        if not fit["fits"]:
                            errors.append(
                                f"{spec.label}: notes do not fit one page even at 16px; shorten them"
                            )
                        page.evaluate("() => document.fonts.ready.then(() => true)")
                    pdf = page.pdf(
                        width=f"{WIDTH}px",
                        height=f"{HEIGHT}px",
                        print_background=True,
                        margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
                        page_ranges="1",
                        prefer_css_page_size=False,
                    )
                    chunks.append(pdf)

            missing = page.evaluate(_JS_MISSING)
            if missing:
                errors.append("unfilled copy slots (.missing): " + ", ".join(missing))
            bad_fonts = [f for f in page.evaluate(_JS_FONTS) if f["status"] == "error"]
            for f in bad_fonts:
                errors.append(f"font failed to load: {f['family']} {f['weight']} {f['style']}")
            title = page.title()
        finally:
            browser.close()

    raise_if_problems("export")

    result = HtmlExportResult(output=None, slides=len(slides), pages=0, plan=plan, warnings=warnings)
    if check_only:
        return result

    writer = PdfWriter()
    problems: list[str] = []
    for spec, chunk in zip(plan, chunks):
        reader = PdfReader(io.BytesIO(chunk))
        if len(reader.pages) != 1:
            problems.append(f"{spec.label}: printed {len(reader.pages)} pages instead of 1")
        writer.add_page(reader.pages[0])
    if title:
        writer.add_metadata({"/Title": title})
    buf = io.BytesIO()
    writer.write(buf)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(dedupe_pdf(buf.getvalue()))

    problems += verify_pdf(output, plan, expected_page_count(len(slides), with_notes))
    if problems:
        raise HtmlExportError(problems)

    result.output = output
    result.pages = len(plan)
    if contact_sheet:
        result.contact_sheets = write_contact_sheets(output, [s.label for s in plan])
    return result


def _digest(obj, memo: dict, stack: set) -> bytes:
    """Content hash of a PDF object; indirect references hash as their targets (Merkle style)."""
    import hashlib

    from pypdf.generic import (  # type: ignore
        ArrayObject,
        DictionaryObject,
        IndirectObject,
        StreamObject,
    )

    if isinstance(obj, IndirectObject):
        key = obj.idnum
        if key in memo:
            return memo[key]
        if key in stack:  # cycles do not occur in resources; stay safe anyway
            return b"cycle:%d" % key
        stack.add(key)
        d = hashlib.sha256(b"R" + _digest(obj.get_object(), memo, stack)).digest()
        stack.discard(key)
        memo[key] = d
        return d
    h = hashlib.sha256(type(obj).__name__.encode())
    if isinstance(obj, DictionaryObject):
        for k in sorted(obj.keys()):
            if k == "/Length" and isinstance(obj, StreamObject):
                continue
            h.update(k.encode() + b"=" + _digest(obj.raw_get(k), memo, stack))
        if isinstance(obj, StreamObject):
            h.update(b"stream" + obj._data)
    elif isinstance(obj, ArrayObject):
        for v in obj:
            h.update(_digest(v, memo, stack))
    else:
        h.update(repr(obj).encode())
    return h.digest()


def dedupe_pdf(data: bytes) -> bytes:
    """Store repeated resources once.

    Chromium prints each page as its own document, so an image, pattern or font that
    appears on many slides (a grain layer, a shadow, a recurring plate) arrives as a
    separate copy per page. Resource entries are re-pointed at the first object with the
    same content; the copies are dropped when the document is cloned for writing.
    """
    PdfReader, PdfWriter = _require_pypdf()
    from pypdf.generic import DictionaryObject, IndirectObject, NameObject  # type: ignore

    reader = PdfReader(io.BytesIO(data))
    memo: dict = {}
    canonical: dict[bytes, IndirectObject] = {}
    seen: set[int] = set()

    def walk_resources(res) -> None:
        res = res.get_object() if isinstance(res, IndirectObject) else res
        if not isinstance(res, DictionaryObject):
            return
        for cat in ("/XObject", "/Pattern", "/Font", "/ExtGState", "/Shading", "/ColorSpace"):
            group = res.get(cat)
            if group is None:
                continue
            group = group.get_object()
            if not isinstance(group, DictionaryObject):
                continue
            for name in list(group.keys()):
                ref = group.raw_get(name)
                if not isinstance(ref, IndirectObject):
                    continue
                d = _digest(ref, memo, set())
                keep = canonical.setdefault(d, ref)
                if keep.idnum != ref.idnum:
                    group[NameObject(name)] = keep
                if keep.idnum in seen:
                    continue
                seen.add(keep.idnum)
                target = keep.get_object()
                if isinstance(target, DictionaryObject) and "/Resources" in target:
                    walk_resources(target["/Resources"])

    for page in reader.pages:
        if "/Resources" in page:
            walk_resources(page["/Resources"])
    writer = PdfWriter(clone_from=reader)  # cloning keeps only what is still referenced
    buf = io.BytesIO()
    writer.write(buf)
    out = buf.getvalue()
    return out if len(out) < len(data) else data


def verify_pdf(path: Path, plan: list[PageSpec], expected: int) -> list[str]:
    """Page count, page size and text layer of the merged PDF."""
    PdfReader, _ = _require_pypdf()
    reader = PdfReader(str(path))
    problems: list[str] = []
    if len(reader.pages) != expected:
        problems.append(f"PDF has {len(reader.pages)} pages, expected {expected}")
    total_text = 0
    for spec, pg in zip(plan, reader.pages):
        w, h = float(pg.mediabox.width), float(pg.mediabox.height)
        if abs(w - PAGE_PT[0]) > 1 or abs(h - PAGE_PT[1]) > 1:
            problems.append(f"{spec.label}: page is {w:.0f}x{h:.0f} pt, expected {PAGE_PT[0]:.0f}x{PAGE_PT[1]:.0f}")
        total_text += len((pg.extract_text() or "").strip())
    if reader.pages and total_text == 0:
        problems.append("PDF has no extractable text: pages were rasterised")
    return problems


# ---------------------------------------------------------------- contact sheet


def _require_pillow():
    try:
        from PIL import Image  # type: ignore  # noqa: F401
    except ImportError as exc:
        raise MissingDependencyError(
            f"The contact sheet needs Pillow. Install it with: {INSTALL_HINT}"
        ) from exc


def rasterize_pdf(path: Path, width: int = 640) -> list:
    """Render every PDF page to a PIL image ``width`` px wide."""
    from PIL import Image  # type: ignore

    engine = find_rasterizer()
    if engine == "pymupdf":
        try:
            import pymupdf  # type: ignore
        except ImportError:  # pragma: no cover - old installs
            import fitz as pymupdf  # type: ignore
        images = []
        with pymupdf.open(str(path)) as doc:
            for pg in doc:
                zoom = width / pg.rect.width
                pix = pg.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
                images.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
        return images
    if engine == "pdftoppm":
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(
                ["pdftoppm", "-png", "-scale-to-x", str(width), "-scale-to-y", "-1", str(path), f"{tmp}/p"],
                check=True,
                capture_output=True,
            )
            files = sorted(Path(tmp).glob("p-*.png"), key=lambda f: int(f.stem.split("-")[-1]))
            return [Image.open(f).convert("RGB") for f in files]
    raise MissingDependencyError("No PDF rasterizer: install pymupdf or poppler's pdftoppm.")


def compose_contact_sheets(images: list, labels: list[str], cols: int = 4, rows: int = 5) -> list:
    """Grid the page images into sheets of ``cols x rows`` with a label under each tile."""
    from PIL import Image, ImageDraw  # type: ignore

    if not images:
        return []
    tw = images[0].width
    th = round(tw * HEIGHT / WIDTH)
    pad, label_h = 12, 26
    per = cols * rows
    sheets = []
    for k in range(0, len(images), per):
        chunk = list(zip(images[k : k + per], labels[k : k + per]))
        n_rows = (len(chunk) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * (tw + pad) + pad, n_rows * (th + label_h + pad) + pad), "#d9d9d9")
        draw = ImageDraw.Draw(sheet)
        for j, (im, label) in enumerate(chunk):
            x = pad + (j % cols) * (tw + pad)
            y = pad + (j // cols) * (th + label_h + pad)
            tile = im if im.size == (tw, th) else im.resize((tw, th))
            sheet.paste(tile, (x, y))
            draw.rectangle([x - 1, y - 1, x + tw, y + th], outline="#9a9a9a")
            draw.text((x + 2, y + th + 7), f"p{k + j + 1:02d}  {label}", fill="black")
        sheets.append(sheet)
    return sheets


def write_contact_sheets(pdf_path: Path, labels: list[str]) -> list[Path]:
    """Write ``<pdf stem>_contact_NN.jpg`` next to the PDF; returns the paths."""
    pdf_path = Path(pdf_path)
    for old in pdf_path.parent.glob(f"{pdf_path.stem}_contact_*.jpg"):
        old.unlink()
    sheets = compose_contact_sheets(rasterize_pdf(pdf_path), labels)
    paths = []
    for i, sheet in enumerate(sheets, 1):
        out = pdf_path.with_name(f"{pdf_path.stem}_contact_{i:02d}.jpg")
        sheet.save(out, quality=88)
        paths.append(out)
    return paths
