"""Convert copy/copy.md (the writer's output) into js/copy.js, keyed by slide id.
copy.md format, per slide:  "## slide_id", then "slot: text" lines, then "### notes" and the spoken script."""
import json, re, pathlib
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
words = sum(len(v["notes"].split()) for v in out.values())
print(f"{len(out)} slides; {words} spoken words ≈ {words / 135:.1f} min at 135 wpm")
