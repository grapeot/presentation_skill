"""Generate the frames inside index.html (between FRAMES:BEGIN and FRAMES:END).

Edit this file, then run:  python3 tools/build_index.py

Conventions (enforced by js/engine.js):
- One frame per slide, id = slide id from js/deck.js. Each frame is a 1920x1080 page; the engine lays frames out
  on the sheet in slide order, so reordering slides never means recomputing coordinates.
- data-in="slide.step" makes an element present from that step (data-out retires it). data-state adds a class
  inside a step range. State depends only on the position, so going back or jumping is exact.
- data-slot="slide.slot" is filled from js/copy.js (the writer's copy). Literal text written here is
  builder-authored: keep it to structural labels and list it in validation.md.
- Frame content box: x 160..1760, y 130..950 (the running header and footer sit outside it).
"""
import pathlib

D = pathlib.Path(__file__).resolve().parents[1]


def plate(src, x, y, w, h, when, extra=""):
    """A textless illustration printed onto the page; inks in with a radial mask when present."""
    return (f'<div class="plate" data-in="{when}" {extra} style="left:{x}px; top:{y}px; width:{w}px; height:{h}px">'
            f'<img src="{src}" alt=""></div>')


def kicker(text, x=160, y=150):
    return f'<div class="kicker" style="position:absolute; left:{x}px; top:{y}px">{text}</div>'


def split_card(sid, name, catno, taxon, split_at, left=160, top=300):
    """A museum-label card that cracks into a lasting half (left, blue) and an expiring half (right, hatched)."""
    return f'''
  <div class="specimen" data-in="{sid}.0" data-state="split@{split_at}" style="left:{left}px; top:{top}px">
    <div class="half l"><div class="frameline"></div><div class="inside"><div class="tag">Keeps</div><div class="body" data-slot="{sid}.problem"></div></div></div>
    <div class="half r"><div class="frameline"></div><div class="inside"><div class="tag">Expires</div><div class="body" data-slot="{sid}.patch"></div></div></div>
    <svg class="crack" viewBox="0 0 24 436" preserveAspectRatio="none"><path pathLength="1" d="M12 0 L16 60 L8 120 L15 190 L9 250 L16 320 L10 380 L12 436"/></svg>
    <div class="catno">{catno}</div><div class="name">{name}</div><div class="taxon">{taxon}</div>
  </div>'''


F = []

F.append(f'''<div class="frame" id="title">
  {plate("imgs/cpu-blueprint.svg", 1100, 300, 560, 460, "title.0")}
  <div class="kicker rise" data-in="title.0" style="position:absolute; left:160px; top:300px">Presentation skill · HTML canvas</div>
  <div class="display h1 type" data-in="title.0" style="position:absolute; left:160px; top:350px; width:860px">Reference Canvas Deck</div>
  <div class="lede rise" data-in="title.0" style="position:absolute; left:160px; top:600px; width:820px; transition-delay:.9s" data-slot="title.subtitle"></div>
</div>''')

stages = ["Collect", "Transform", "Store", "Retrieve", "Assemble"]
boxes = "".join(f'<div class="pstage rise" data-in="pipeline.0" style="transition-delay:{.3 + i * .22:.2f}s"><span class="pn">0{i + 1}</span>{t}</div>' for i, t in enumerate(stages))
F.append(f'''<div class="frame" id="pipeline">
  {kicker("Pen, stagger, one claim per beat")}
  <div class="display h2 rise" data-in="pipeline.0" style="position:absolute; left:160px; top:190px; width:1600px" data-slot="pipeline.headline"></div>
  <div class="pipeline" style="left:160px; top:440px; width:1300px">{boxes}</div>
  <div class="window rise" data-in="pipeline.1" style="left:1520px; top:410px"><div class="wfill"></div><span>The constraint</span></div>
  <div class="display h3 rise closer" data-in="pipeline.2" style="position:absolute; left:160px; top:720px; width:1300px" data-slot="pipeline.caption"></div>
</div>''')

F.append(f'''<div class="frame" id="split">
  {kicker("A card that splits on the beat")}
  {split_card("split", "Specimen", "Specimen · 2026", "what it promised", "split.1")}
  <div class="display h3 rise closer" data-in="split.2" style="position:absolute; left:160px; top:790px; width:880px" data-slot="split.what_to_do"></div>
</div>''')

F.append('''<div class="frame" id="numbers">
  <div class="display h2 rise" data-in="numbers.0" style="position:absolute; left:160px; top:150px; width:1600px" data-slot="numbers.headline"></div>
  <svg class="bars" data-in="numbers.0" width="900" height="560" viewBox="0 0 900 560" style="position:absolute; left:200px; top:330px; overflow:visible">
    <defs><pattern id="hatchB" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="10" stroke="#23407a" stroke-width="3"/></pattern>
          <pattern id="hatchR" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="10" stroke="#b6422a" stroke-width="3"/></pattern></defs>
    <line x1="0" y1="480" x2="900" y2="480" stroke="#1b2130" stroke-width="1.5"/>
    <g><rect x="110" y="266" width="200" height="214" fill="none" stroke="#8b8f99" stroke-dasharray="6 6"/>
      <text x="96" y="274" text-anchor="end" font-size="22" fill="#8b8f99">before · 10.7</text>
      <rect class="bar-rect" data-bar="numbers.1" data-h0="214" data-h1="124" x="110" y="266" width="200" height="214" fill="url(#hatchR)" stroke="#b6422a" stroke-width="2"/>
      <text class="counter" data-count="numbers.1" data-from="10.7" data-to="6.2" data-dec="1" x="330" y="300" font-size="46" fill="#b6422a" data-follow="numbers.1" data-y0="300" data-y1="392">10.7</text></g>
    <g><rect x="560" y="164" width="200" height="316" fill="none" stroke="#8b8f99" stroke-dasharray="6 6"/>
      <text x="546" y="172" text-anchor="end" font-size="22" fill="#8b8f99">before · 15.8</text>
      <rect class="bar-rect" data-bar="numbers.1" data-h0="316" data-h1="374" x="560" y="164" width="200" height="316" fill="url(#hatchB)" stroke="#23407a" stroke-width="2"/>
      <text class="counter" data-count="numbers.1" data-from="15.8" data-to="18.7" data-dec="1" x="780" y="198" font-size="46" fill="#23407a" data-follow="numbers.1" data-y0="198" data-y1="140">15.8</text></g>
  </svg>
  <div class="source rise" data-in="numbers.0" style="position:absolute; left:160px; top:905px">Illustrative values · every data frame carries a source line from its first step</div>
  <div class="display h3 rise" data-in="numbers.2" style="position:absolute; left:1180px; top:560px; width:580px" data-slot="numbers.takeaway"></div>
</div>''')

F.append('''<div class="frame" id="close">
  <div class="kicker" style="position:absolute; left:160px; top:150px">Closing line</div>
  <div class="display type" data-in="close.1" style="position:absolute; left:160px; top:420px; width:1600px; font-size:66px; line-height:1.18" data-slot="close.closing"></div>
</div>''')

html = (D / "index.html").read_text(encoding="utf-8")
a = html.index("<!-- FRAMES:BEGIN")
a = html.index("-->", a) + 3
b = html.index("<!-- FRAMES:END -->")
(D / "index.html").write_text(html[:a] + "\n" + "\n\n".join(F) + "\n" + html[b:], encoding="utf-8")
print("frames:", len(F))
