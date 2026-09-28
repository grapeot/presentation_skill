"""Tests for the HTML (canvas) deck PDF exporter.

The unit tests need no browser. The browser tests export the template deck through
headless Chromium on a loopback server (no network) and are skipped automatically
when Playwright or its Chromium build is not installed.
"""

from __future__ import annotations

import io
import re
import shutil
import sys
from pathlib import Path

import pytest

from presentation_skill import export_html_pdf as ehp
from presentation_skill.cli import build_parser, main as cli_main, resolve_export_mode
from presentation_skill.export_html_pdf import (
    HtmlExportError,
    MissingDependencyError,
    PageSpec,
    SlideInfo,
    compose_contact_sheets,
    default_output,
    dedupe_pdf,
    expected_page_count,
    is_canvas_deck,
    is_local_url,
    plan_pages,
    resolve_print_step,
    slides_from_table,
    split_notes,
    verify_pdf,
)

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "src" / "presentation_skill" / "templates" / "examples"
TEMPLATE = EXAMPLES / "html"
IMAGE_TEMPLATE = EXAMPLES / "image"


# ---------------------------------------------------------------- page selection


def _slide(i, sid, steps, print_=None, notes=""):
    return SlideInfo(index=i, id=sid, steps=steps, print=print_, notes=notes)


def test_print_step_defaults_to_last_step():
    assert resolve_print_step(_slide(0, "a", 1)) == 0
    assert resolve_print_step(_slide(0, "a", 4)) == 3


def test_print_step_override():
    assert resolve_print_step(_slide(0, "a", 4, 1)) == 1
    assert resolve_print_step(_slide(0, "a", 4, 0)) == 0
    assert resolve_print_step(_slide(0, "a", 4, 2.0)) == 2


@pytest.mark.parametrize("bad", [4, -1, 1.5, "2", True, [1]])
def test_print_step_rejects_invalid_values(bad):
    with pytest.raises(ValueError, match="print"):
        resolve_print_step(_slide(0, "a", 4, bad))


def test_plan_pages_one_page_per_slide():
    slides = [_slide(0, "a", 1), _slide(1, "b", 3), _slide(2, "c", 3, 1)]
    plan = plan_pages(slides)
    assert [(p.kind, p.slide_id, p.step) for p in plan] == [
        ("slide", "a", 0),
        ("slide", "b", 2),
        ("slide", "c", 1),
    ]
    assert len(plan) == expected_page_count(3, with_notes=False)


def test_plan_pages_with_notes_interleaves_notes_pages():
    slides = [_slide(0, "a", 2), _slide(1, "b", 3)]
    plan = plan_pages(slides, with_notes=True)
    assert [(p.kind, p.slide_id) for p in plan] == [
        ("slide", "a"),
        ("notes", "a"),
        ("slide", "b"),
        ("notes", "b"),
    ]
    assert len(plan) == expected_page_count(2, with_notes=True)
    assert plan[1].label.endswith("notes")


def test_plan_pages_reports_every_bad_print_value():
    slides = [_slide(0, "a", 2, 5), _slide(1, "b", 3), _slide(2, "c", 1, -1)]
    with pytest.raises(HtmlExportError) as exc:
        plan_pages(slides)
    assert len(exc.value.problems) == 2
    assert "'a'" in exc.value.problems[0] and "'c'" in exc.value.problems[1]


def test_slides_from_table_normalises_rows():
    slides = slides_from_table(
        [
            {"id": "a", "steps": 2, "print": None, "part": "I", "notes": "n"},
            {"id": "b", "print": 0},  # steps missing -> 1, like the engine
        ]
    )
    assert [(s.id, s.steps, s.print) for s in slides] == [("a", 2, None), ("b", 1, 0)]
    assert slides[0].part == "I" and slides[0].notes == "n"


def test_slides_from_table_rejects_bad_tables():
    with pytest.raises(HtmlExportError, match="empty"):
        slides_from_table([])
    with pytest.raises(HtmlExportError, match="duplicate"):
        slides_from_table([{"id": "a", "steps": 1}, {"id": "a", "steps": 1}])
    with pytest.raises(HtmlExportError, match="steps"):
        slides_from_table([{"id": "a", "steps": 0}])


def test_split_notes_paragraphs():
    assert split_notes("One\nline.\n\nTwo.\n\n\n") == ["One line.", "Two."]
    assert split_notes("") == []


@pytest.mark.parametrize(
    "url,local",
    [
        ("http://127.0.0.1:8123/index.html", True),
        ("http://localhost:9000/x.js", True),
        ("http://[::1]:9000/x.js", True),
        ("data:image/svg+xml;utf8,<svg/>", True),
        ("blob:http://127.0.0.1:8123/abc", True),
        ("https://fonts.example.com/a.woff2", False),
        ("http://192.168.1.4/a.png", False),
        ("ftp://127.0.0.1/a", False),
    ],
)
def test_is_local_url(url, local):
    assert is_local_url(url) is local


# ---------------------------------------------------------------- deck detection and CLI


def test_canvas_deck_detection(tmp_path: Path):
    assert is_canvas_deck(TEMPLATE)
    assert not is_canvas_deck(IMAGE_TEMPLATE)
    deck = tmp_path / "deck"
    shutil.copytree(TEMPLATE, deck)
    (deck / "js" / "deck.js").write_text("// no slide table\n", encoding="utf-8")
    assert not is_canvas_deck(deck)


def test_export_mode_resolution():
    assert resolve_export_mode("auto", TEMPLATE) == "html"
    assert resolve_export_mode("auto", IMAGE_TEMPLATE) == "image"
    assert resolve_export_mode("canvas", IMAGE_TEMPLATE) == "html"
    assert resolve_export_mode("image", TEMPLATE) == "image"


def test_export_parser_flags():
    args = build_parser().parse_args(["export-pdf", "deck", "--with-notes", "--mode", "html", "--no-contact-sheet"])
    assert args.with_notes and args.no_contact_sheet and args.mode == "html"
    args = build_parser().parse_args(["export-pdf", "deck"])
    assert not args.with_notes and not args.no_contact_sheet and args.mode == "auto"


def test_default_output_paths(tmp_path: Path):
    assert default_output(tmp_path) == tmp_path / "verification" / "handout.pdf"
    assert default_output(tmp_path, True) == tmp_path / "verification" / "handout_with_notes.pdf"


def test_with_notes_rejected_for_image_decks(capsys):
    assert cli_main(["export-pdf", str(IMAGE_TEMPLATE), "--with-notes"]) == 2
    assert "HTML (canvas) decks" in capsys.readouterr().out


def test_missing_playwright_gives_install_hint(monkeypatch, capsys):
    monkeypatch.setitem(sys.modules, "playwright", None)
    monkeypatch.setitem(sys.modules, "playwright.sync_api", None)
    with pytest.raises(MissingDependencyError, match=r"presentation-skill\[pdf-html\]"):
        ehp._require_playwright()
    assert cli_main(["export-pdf", str(TEMPLATE)]) == 3
    out = capsys.readouterr().out
    assert "playwright install chromium" in out


# ---------------------------------------------------------------- PDF post-processing


def _png_bytes(color, size=(64, 36)):
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()


def test_dedupe_stores_repeated_images_once():
    img2pdf = pytest.importorskip("img2pdf")
    from pypdf import PdfReader

    noisy = _png_bytes("white", (400, 300))
    data = img2pdf.convert([noisy, noisy, noisy])
    out = dedupe_pdf(data)
    reader = PdfReader(io.BytesIO(out))
    assert len(reader.pages) == 3
    refs = {
        page["/Resources"]["/XObject"].raw_get(name).idnum
        for page in reader.pages
        for name in page["/Resources"]["/XObject"]
    }
    assert len(refs) == 1
    assert len(out) <= len(data)


def test_verify_pdf_checks_count_and_size(tmp_path: Path):
    img2pdf = pytest.importorskip("img2pdf")

    pdf = tmp_path / "x.pdf"
    layout = img2pdf.get_fixed_dpi_layout_fun((96, 96))
    pdf.write_bytes(img2pdf.convert([_png_bytes("white", (1920, 1080))] * 2, layout_fun=layout))
    plan = [PageSpec("slide", 0, "a", 0), PageSpec("slide", 1, "b", 0)]
    problems = verify_pdf(pdf, plan, expected=3)
    assert any("expected 3" in p for p in problems)
    assert not any("pt, expected" in p for p in problems)  # 1920 px at 96 dpi = 1440 pt
    assert any("no extractable text" in p for p in problems)


def test_contact_sheet_grid():
    from PIL import Image

    images = [Image.new("RGB", (320, 180), "white") for _ in range(23)]
    sheets = compose_contact_sheets(images, [f"p{i}" for i in range(23)], cols=4, rows=5)
    assert len(sheets) == 2  # 20 + 3
    assert sheets[0].width == sheets[1].width
    assert sheets[0].height > sheets[1].height


# ---------------------------------------------------------------- browser tests

# A minimal stand-in for the vendored Reveal build (the template vendors Reveal with npm, which
# the offline suite cannot run). It implements exactly what js/engine.js calls.
REVEAL_STUB = """
(function () {
  const handlers = {}; let h = 0, f = -1, ready = false;
  const fire = ev => (handlers[ev] || []).forEach(cb => cb({}));
  window.Reveal = {
    initialize() { setTimeout(() => { ready = true; fire("ready"); }, 0); return Promise.resolve(); },
    on(ev, cb) { (handlers[ev] = handlers[ev] || []).push(cb); },
    isReady() { return ready; },
    getIndices() { return { h, v: 0, f: f < 0 ? undefined : f }; },
    getSlides() { return [...document.querySelectorAll(".reveal .slides > section")]; },
    slide(nh, v, nf) { const moved = nh !== h; h = nh; f = nf == null ? -1 : nf; fire(moved ? "slidechanged" : "fragmentshown"); },
  };
})();
"""


def _chromium_available() -> bool:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    try:
        with sync_playwright() as p:
            p.chromium.launch().close()
    except Exception:
        return False
    return True


needs_browser = pytest.mark.skipif(
    not _chromium_available(), reason="Playwright with Chromium is not installed"
)


@pytest.fixture
def stub_deck(tmp_path: Path) -> Path:
    """The template deck with a stub Reveal and without web fonts (neither is vendored in the repo)."""
    deck = tmp_path / "deck"
    shutil.copytree(TEMPLATE, deck)
    vendor = deck / "vendor" / "reveal"
    (vendor / "notes").mkdir(parents=True)
    (vendor / "reveal.js").write_text(REVEAL_STUB, encoding="utf-8")
    (vendor / "notes" / "notes.js").write_text("window.RevealNotes = { id: 'notes' };\n", encoding="utf-8")
    (vendor / "reveal.css").write_text("", encoding="utf-8")
    (vendor / "reset.css").write_text("", encoding="utf-8")
    css = deck / "css" / "deck.css"
    css.write_text(re.sub(r"@font-face\s*\{[^}]*\}", "", css.read_text(encoding="utf-8")), encoding="utf-8")
    return deck


def _set_print(deck: Path, slide_id: str, step: int) -> None:
    js = deck / "js" / "deck.js"
    text = js.read_text(encoding="utf-8")
    text, n = re.subn(
        rf'S\("{slide_id}", ([^\n]*?)\),\n',
        lambda m: f'Object.assign(S("{slide_id}", {m.group(1)}), {{ print: {step} }}),\n',
        text,
    )
    assert n == 1
    js.write_text(text, encoding="utf-8")


@needs_browser
def test_browser_export_template_with_notes(stub_deck: Path):
    from pypdf import PdfReader

    _set_print(stub_deck, "pipeline", 0)
    # A handout-only element (shown only while the exporter prints "close") and a link.
    index = stub_deck / "index.html"
    index.write_text(
        index.read_text(encoding="utf-8")
        .replace(
            '<div class="kicker" style="position:absolute; left:160px; top:150px">Closing line</div>',
            '<div class="kicker" style="position:absolute; left:160px; top:150px">Closing line</div>\n'
            '  <div class="handout-only" style="position:absolute; left:160px; top:700px">Handout row</div>\n'
            '  <a href="https://example.com/further-reading" style="position:absolute; left:160px; top:800px">Further reading</a>',
        )
        .replace(
            "</head>",
            "<style>.handout-only { display: none; }\n"
            'html.pdf-export[data-print-slide="close"] .handout-only { display: block; }</style>\n</head>',
        ),
        encoding="utf-8",
    )
    result = ehp.export_canvas_pdf(stub_deck, with_notes=True, contact_sheet=ehp.find_rasterizer() is not None)
    assert result.output == stub_deck / "verification" / "handout_with_notes.pdf"
    assert result.slides == 5 and result.pages == 10
    reader = PdfReader(str(result.output))
    assert len(reader.pages) == 10
    for page in reader.pages:
        assert round(float(page.mediabox.width)) == 1440 and round(float(page.mediabox.height)) == 810
    texts = [page.extract_text() for page in reader.pages]
    # Slide pages carry their own frame only; the notes page carries notes, not the slide.
    assert "A reference deck" in texts[0] and "Stages arrive" not in texts[0]
    assert "vocabulary of the canvas mode" in texts[1] and "A reference deck" not in texts[1]
    # print: 0 on "pipeline" prints its first state: the step-2 caption is not there yet.
    assert "Collect" in texts[2] and "made the pipeline necessary" not in texts[2]
    # The default print state is the last step: the split card's step-2 takeaway is printed.
    assert "patch half expires" in texts[4]
    assert "6.2" in texts[6] and "18.7" in texts[6]
    assert "Handout row" in texts[8] and not any("Handout row" in t for t in texts[:8])
    annots = [a.get_object() for a in reader.pages[8].get("/Annots", [])]
    assert any(a.get("/A", {}).get("/URI") == "https://example.com/further-reading" for a in annots)
    if result.contact_sheets:
        assert all(p.is_file() for p in result.contact_sheets)


@needs_browser
def test_browser_export_fails_on_missing_slot(stub_deck: Path):
    copy_js = stub_deck / "js" / "copy.js"
    copy_js.write_text(re.sub(r'"subtitle":\s*"[^"]*"', '"subtitle": ""', copy_js.read_text(encoding="utf-8")), encoding="utf-8")
    with pytest.raises(HtmlExportError, match=r"unfilled copy slots.*title\.subtitle"):
        ehp.export_canvas_pdf(stub_deck, check_only=True)


@needs_browser
def test_browser_export_fails_on_external_request_and_console_error(stub_deck: Path):
    index = stub_deck / "index.html"
    html = index.read_text(encoding="utf-8").replace(
        "</body>",
        '<img src="https://cdn.example.com/pixel.png" alt="">\n'
        "<script>console.error('boom from the deck')</script>\n</body>",
    )
    index.write_text(html, encoding="utf-8")
    with pytest.raises(HtmlExportError) as exc:
        ehp.export_canvas_pdf(stub_deck, check_only=True)
    text = "\n".join(exc.value.problems)
    assert "request left localhost: https://cdn.example.com/pixel.png" in text
    assert "boom from the deck" in text


@needs_browser
def test_browser_export_rejects_bad_print_value(stub_deck: Path):
    _set_print(stub_deck, "close", 7)
    with pytest.raises(HtmlExportError, match=r"'close': print=7"):
        ehp.export_canvas_pdf(stub_deck, check_only=True)


@needs_browser
def test_cli_exports_html_deck(stub_deck: Path, capsys):
    out = stub_deck / "out" / "slides.pdf"
    assert cli_main(["export-pdf", str(stub_deck), "--output", str(out), "--no-contact-sheet"]) == 0
    assert out.is_file()
    assert "5 pages: 5 slides" in capsys.readouterr().out
