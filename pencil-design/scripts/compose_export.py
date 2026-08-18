#!/usr/bin/env python3
"""Compose Pencil MCP Export() PNGs into one flat RGB image.

Manifest schema (see references/export.md). Do not reimplement this math in
the agent prompt.

{
  "scale": 1,
  "pad": 40,
  "indir": "/absolute/path/to/export-dir",
  "outfile": "/absolute/path/to/flow.png",
  "nodes": [{"id": "<id>", "x": 0, "y": 0}]
}

`nodes` must be in document-root index order (later = on top).
`scale` must match the Export() scale that produced the PNGs.
`x`/`y` are document coordinates from Get (node.x / node.y).
Each file is `{indir}/{id}.png`. Paste uses that file's pixel size — do not
put width/height in the manifest; Export size can differ from bounds by 1px.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def fail(msg: str, code: int = 1) -> None:
    print(f"compose_export: {msg}", file=sys.stderr)
    raise SystemExit(code)


def load_manifest(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"manifest not found: {path}")
    except json.JSONDecodeError as e:
        fail(f"manifest is not JSON: {e}")
    if not isinstance(data, dict):
        fail("manifest must be a JSON object")
    return data


def main(argv: list[str]) -> None:
    if len(argv) != 2 or argv[1] in {"-h", "--help"}:
        print("usage: compose_export.py MANIFEST.json", file=sys.stderr)
        raise SystemExit(2)

    try:
        from PIL import Image
    except ImportError:
        fail(
            "Pillow is not installed in this Python. "
            "Ask the user: global install, or a project venv? "
            "Then rerun this script with that same interpreter.",
            2,
        )

    manifest_path = Path(argv[1]).expanduser()
    data = load_manifest(manifest_path)

    try:
        scale = float(data.get("scale", 1))
        pad = float(data.get("pad", 40))
    except (TypeError, ValueError):
        fail("scale and pad must be numbers")
    if scale <= 0:
        fail("scale must be > 0")
    if pad < 0:
        fail("pad must be >= 0")

    indir_raw = data.get("indir")
    outfile_raw = data.get("outfile")
    nodes = data.get("nodes")
    if not indir_raw or not outfile_raw:
        fail("manifest needs indir and outfile")
    if not isinstance(nodes, list) or not nodes:
        fail("manifest.nodes must be a non-empty array in document order")

    indir = Path(str(indir_raw)).expanduser()
    outfile = Path(str(outfile_raw)).expanduser()
    if not indir.is_absolute():
        fail(
            "indir must be absolute. Copy the directory Export printed "
            "(the parent of `{id}.png`), not a path relative to this manifest."
        )
    if not outfile.is_absolute():
        fail("outfile must be absolute — that file is the only deliverable")

    prepared: list[tuple[str, float, float, object]] = []
    for i, node in enumerate(nodes):
        if not isinstance(node, dict):
            fail(f"nodes[{i}] must be an object")
        nid = node.get("id")
        if not nid:
            fail(f"nodes[{i}] missing id")
        try:
            x = float(node["x"])
            y = float(node["y"])
        except (KeyError, TypeError, ValueError):
            fail(f"nodes[{i}] ({nid}) needs numeric x and y")
        png = indir / f"{nid}.png"
        if not png.is_file():
            fail(f"missing export: {png}")
        im = Image.open(png).convert("RGBA")
        prepared.append((str(nid), x, y, im))

    min_x = min(x for _, x, _, _ in prepared) - pad
    min_y = min(y for _, _, y, _ in prepared) - pad
    max_x = max(x + im.size[0] / scale for _, x, _, im in prepared) + pad
    max_y = max(y + im.size[1] / scale for _, _, y, im in prepared) + pad
    width = int(round((max_x - min_x) * scale))
    height = int(round((max_y - min_y) * scale))
    if width < 1 or height < 1:
        fail(f"computed canvas is {width}x{height}")

    canvas = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    for nid, x, y, im in prepared:
        px = int(round((x - min_x) * scale))
        py = int(round((y - min_y) * scale))
        canvas.alpha_composite(im, (px, py))
        print(f"paste {nid} at ({px},{py}) size={im.size[0]}x{im.size[1]}")

    outfile.parent.mkdir(parents=True, exist_ok=True)
    rgb = canvas.convert("RGB")
    rgb.save(outfile)
    print(f"origin=({min_x},{min_y}) canvas={width}x{height} mode={rgb.mode}")
    print(f"wrote {outfile} ({outfile.stat().st_size} bytes)")
    print("deliver this file only — not the per-node PNGs in indir")


if __name__ == "__main__":
    main(sys.argv)
