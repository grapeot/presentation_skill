"""Tests for the image-deck PDF exporter (offline, no network)."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

import pytest

from presentation_skill.cli import main as cli_main
from presentation_skill.export_pdf import (
    CompatibilityError,
    check_compatibility,
    export_pdf,
)


def _tiny_png(path: Path, width: int = 8, height: int = 8) -> None:
    """Write a minimal solid-white PNG without external dependencies."""

    def chunk(tag: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + tag
            + payload
            + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + b"\xff" * (width * 3) for _ in range(height))
    idat = zlib.compress(raw)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", idat)
        + chunk(b"IEND", b"")
    )


OVERLAY_BLOCK = """
  <script id="overlay-data" type="application/json">
  {
    "slide-01": [
      { "href": "https://example.com/repo",
        "rect": [0.25, 0.75, 0.75, 0.85],
        "label": "example.com/repo" }
    ]
  }
  </script>
"""


def _write_deck(deck: Path, *, sections: str, overlay: str = OVERLAY_BLOCK) -> None:
    deck.mkdir(parents=True, exist_ok=True)
    (deck / "generated_slides").mkdir(exist_ok=True)
    _tiny_png(deck / "generated_slides" / "slide_01_0.png")
    _tiny_png(deck / "generated_slides" / "slide_02_0.png")
    (deck / "index.html").write_text(
        "<!DOCTYPE html><html><body><div class=\"reveal\"><div class=\"slides\">"
        + sections
        + "</div></div>"
        + overlay
        + "<script src=\"https://example.com/reveal.js\"></script></body></html>",
        encoding="utf-8",
    )


GOOD_SECTIONS = """
<section id="slide-01" data-background="generated_slides/slide_01_0.png" data-background-size="contain">
  <aside class="notes"><p><em>0:00</em></p><p>Spoken words.</p></aside>
</section>
<section id="slide-02" data-background="generated_slides/slide_02_0.png" data-background-size="contain">
  <aside class="notes">More words.</aside>
</section>
"""


def test_compat_ok(tmp_path: Path) -> None:
    _write_deck(tmp_path / "deck", sections=GOOD_SECTIONS)
    report = check_compatibility(tmp_path / "deck")
    assert report.ok, report.problems
    assert len(report.sections) == 2
    assert sum(len(v) for v in report.overlays.values()) == 1


def test_compat_rejects_extra_content(tmp_path: Path) -> None:
    sections = GOOD_SECTIONS + """
<section id="slide-03" data-background="generated_slides/slide_02_0.png">
  <h1>Live HTML title</h1>
  <aside class="notes">notes</aside>
</section>
"""
    _write_deck(tmp_path / "deck", sections=sections)
    report = check_compatibility(tmp_path / "deck")
    assert not report.ok
    assert any("slide-03" in p and "beyond background" in p for p in report.problems)
    with pytest.raises(CompatibilityError):
        export_pdf(tmp_path / "deck")


def test_compat_rejects_missing_background(tmp_path: Path) -> None:
    sections = """
<section id="slide-01" data-background="generated_slides/missing.png">
  <aside class="notes">x</aside>
</section>
"""
    _write_deck(tmp_path / "deck", sections=sections, overlay="")
    report = check_compatibility(tmp_path / "deck")
    assert not report.ok
    assert any("not found" in p for p in report.problems)


def test_compat_rejects_bad_overlay(tmp_path: Path) -> None:
    bad_overlay = """
  <script id="overlay-data" type="application/json">
  { "slide-01": [ { "href": "ftp://nope", "rect": [0.9, 0.1, 0.2, 0.2] } ],
    "slide-99": [ { "href": "https://ok", "rect": [0.1, 0.1, 0.2, 0.2] } ] }
  </script>
"""
    _write_deck(tmp_path / "deck", sections=GOOD_SECTIONS, overlay=bad_overlay)
    report = check_compatibility(tmp_path / "deck")
    assert not report.ok
    joined = "\n".join(report.problems)
    assert "invalid rect" in joined
    assert "http(s)" in joined
    assert "unknown section id" in joined


def test_export_writes_pdf_with_links(tmp_path: Path) -> None:
    pypdf = pytest.importorskip("pypdf")
    pytest.importorskip("img2pdf")
    deck = tmp_path / "deck"
    _write_deck(deck, sections=GOOD_SECTIONS)
    output, pages, links = export_pdf(deck)
    assert output.is_file()
    assert pages == 2
    assert links == 1
    reader = pypdf.PdfReader(str(output))
    annots = list(reader.pages[0].get("/Annots", []))
    assert len(annots) == 1
    annot = annots[0].get_object()
    assert annot["/A"]["/URI"] == "https://example.com/repo"
    # rect is fractional coords + default 1.5% padding, y flipped to PDF space
    page = reader.pages[0]
    w, h = float(page.mediabox.width), float(page.mediabox.height)
    x1, y1, x2, y2 = [float(v) for v in annot["/Rect"]]
    assert x1 == pytest.approx((0.25 - 0.015) * w, abs=0.5)
    assert x2 == pytest.approx((0.75 + 0.015) * w, abs=0.5)
    assert y1 == pytest.approx(h - (0.85 + 0.015) * h, abs=0.5)
    assert y2 == pytest.approx(h - (0.75 - 0.015) * h, abs=0.5)
    assert reader.pages[1].get("/Annots") in (None, [])


def test_export_without_overlays(tmp_path: Path) -> None:
    pytest.importorskip("img2pdf")
    pytest.importorskip("pypdf")
    deck = tmp_path / "deck"
    _write_deck(deck, sections=GOOD_SECTIONS, overlay="")
    output, pages, links = export_pdf(deck, output=tmp_path / "out" / "deck.pdf")
    assert output == tmp_path / "out" / "deck.pdf"
    assert output.is_file()
    assert pages == 2
    assert links == 0


def test_cli_export_pdf(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    pytest.importorskip("img2pdf")
    pytest.importorskip("pypdf")
    deck = tmp_path / "deck"
    _write_deck(deck, sections=GOOD_SECTIONS)
    rc = cli_main(["export-pdf", str(deck), "--check-only"])
    assert rc == 0
    assert "compatible: 2 slides, 1 link hotzones" in capsys.readouterr().out
    rc = cli_main(["export-pdf", str(deck)])
    assert rc == 0
    assert (deck / "deck.pdf").is_file()


def test_cli_export_pdf_incompatible_exits_nonzero(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    deck = tmp_path / "deck"
    _write_deck(
        deck,
        sections=GOOD_SECTIONS + "<section id=\"s3\" data-background=\"generated_slides/slide_01_0.png\"><div>x</div></section>",
    )
    rc = cli_main(["export-pdf", str(deck), "--check-only"])
    assert rc == 2
    assert "INCOMPATIBLE" in capsys.readouterr().out


def test_cli_legacy_invocation_still_scaffolds(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    rc = cli_main(["Legacy Topic", "--mode", "image", "--output", str(tmp_path / "legacy_deck")])
    assert rc == 0
    assert (tmp_path / "legacy_deck" / "index.html").exists()
