"""Convert copy/copy.md (the writer's output) into js/copy.js, keyed by slide id.
copy.md format, per slide:  "## slide_id", then "slot: text" lines, then "### notes" and the spoken script.

Notes conventions (rendered by js/engine.js in the speaker view):
  a paragraph "[click]"            marks a build step; when a slide's notes use them, their count must equal
                                   the slide's steps - 1 in js/deck.js
  a paragraph wholly in [brackets] is a stage direction: shown, not read aloud, exempt from the breath gate
Checks (exit 1 on failure): click count per slide, and the breath gate: no spoken sentence over 22 words."""
import json, re, pathlib, sys
D = pathlib.Path(__file__).resolve().parents[1]
text = (D / "copy/copy.md").read_text(encoding="utf-8")
parts = re.split(r"^## ([a-z_0-9]+)\s*$", text, flags=re.M)
out = {}
for sid, body in zip(parts[1::2], parts[2::2]):
    slots, _, notes = body.partition("### notes")
    d = {}
    for line in slots.strip().splitlines():
        m = re.match(r"^([a-z_0-9]+):\s*(.*)$", line.strip())
        if m:
            d[m.group(1)] = m.group(2).strip().strip('"')
    d["notes"] = notes.strip()
    out[sid] = d
(D / "js/copy.js").write_text("window.COPY = " + json.dumps(out, ensure_ascii=False, indent=1) + ";\n", encoding="utf-8")

# ---- checks ----
steps = {m.group(1): int(m.group(2)) for m in re.finditer(r'S\("([a-z_0-9]+)",\s*"[^"]*",\s*(\d+)', (D / "js/deck.js").read_text(encoding="utf-8"))}
DIRECTION = re.compile(r"^`?\[[^\]]+\]`?$")
problems = []
for sid, d in out.items():
    paras = [p.strip() for p in re.split(r"\n\s*\n", d["notes"]) if p.strip()]
    clicks = sum(1 for p in paras if re.fullmatch(r"`?\[click\]`?", p, flags=re.I))
    if clicks and sid in steps and clicks != steps[sid] - 1:
        problems.append(f"{sid}: {clicks} [click] cues, the slide has {steps[sid] - 1} clicks")
    for p in paras:
        if DIRECTION.match(p):
            continue
        for sent in re.split(r"(?<=[.!?])\s+", p):
            n = len(sent.split())
            if n > 22:
                problems.append(f"{sid}: {n}-word sentence (breath gate 22): {sent[:70]}...")
for line in problems:
    print("PROBLEM", line)
spoken = lambda t: " ".join(p for p in re.split(r"\n\s*\n", t) if not DIRECTION.match(p.strip()))
words = sum(len(spoken(v["notes"]).split()) for v in out.values())
print(f"{len(out)} slides; {words} spoken words ≈ {words / 135:.1f} min at 135 wpm")
if problems:
    sys.exit(1)
