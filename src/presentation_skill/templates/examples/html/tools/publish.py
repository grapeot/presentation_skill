"""Stage the public copy of the deck in dist/ (or --out): runtime files only, speaker notes removed.

    python3 tools/publish.py [--out dist] [--with-notes]

Then upload dist/ with any static host. With rsync, never pass --delete (other pages may live next to the deck):
    rsync -rtp dist/ host:/var/www/site/talk/

Why each rule exists:
- Speaker notes live in js/copy.js, which the browser downloads. Hiding the speaker view is not enough, so the
  public copy rewrites copy.js with every "notes" field emptied (unless --with-notes).
- Only what the page loads goes up: index.html, css/, js/, vendor/, imgs/, assets/. Sources (copy/, tools/,
  node_modules/, shots) stay local.
- Everything is made world-readable: a folder that is 700 locally becomes a 403 on the web server.
After uploading, open the live URL in a browser and step through a few slides; check fonts and the console.
"""
import argparse
import json
import pathlib
import re
import shutil
import stat

D = pathlib.Path(__file__).resolve().parents[1]
RUNTIME = ["index.html", "css", "js", "vendor", "imgs", "assets"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="dist")
    ap.add_argument("--with-notes", action="store_true", help="keep the speaker notes in the public copy")
    a = ap.parse_args()
    out = (D / a.out).resolve()
    if out == D or D not in out.parents:
        raise SystemExit(f"--out must be a folder inside the deck: {out}")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for name in RUNTIME:
        src = D / name
        if src.is_dir():
            shutil.copytree(src, out / name)
        elif src.is_file():
            shutil.copy2(src, out / name)
    if not (out / "vendor").is_dir():
        raise SystemExit("vendor/ is missing: run `npm install && npm run vendor` first, or the deck has no Reveal or fonts")

    copy_js = out / "js" / "copy.js"
    if copy_js.is_file() and not a.with_notes:
        text = copy_js.read_text(encoding="utf-8")
        m = re.match(r"\s*window\.COPY\s*=\s*(\{.*\})\s*;\s*$", text, flags=re.S)
        if not m:
            raise SystemExit("js/copy.js is not the `window.COPY = {...};` that tools/copy_to_js.py writes")
        data = json.loads(m.group(1))
        for v in data.values():
            if isinstance(v, dict) and "notes" in v:
                v["notes"] = ""
        copy_js.write_text("window.COPY = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n", encoding="utf-8")

    for p in [out, *out.rglob("*")]:
        mode = p.stat().st_mode
        p.chmod(mode | stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH | ((stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH) if p.is_dir() else 0))

    files = sum(1 for p in out.rglob("*") if p.is_file())
    size = sum(p.stat().st_size for p in out.rglob("*") if p.is_file())
    print(f"staged {files} files, {size / 1e6:.1f} MB at {out} ({'with' if a.with_notes else 'without'} speaker notes)")
    print(f"upload, never with --delete:  rsync -rtp {out}/ host:/path/to/talk/")


if __name__ == "__main__":
    main()
