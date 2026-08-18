#!/usr/bin/env python3
"""Make a Pencil ``html-tailwind`` export faithful to a Get() inventory.

Usage:
  python3 fix_pen_html.py --html raw.html --inventory inventory.jsonl --out patched.html \
    --expected-root Phone --scope-filter --report report.json
  python3 fix_pen_html.py --html patched.html --inventory inventory.jsonl --check \
    --expected-root Phone --report report.json

The inventory is JSONL (or a JSON array) produced by the recipe in
``references/export.md``. It contains every named Pencil node, not just the
nodes expected to change. Every row needs ``id``, ``name``, and ``path``.
``path`` is the zero-based path of Pencil sibling indexes from document root.

The first command injects ``data-pencil-id`` into a raw export, then patches
only properties that the export loses: corner radii, numeric height, and
``clip:true``. The second command is read-only and fails if another patch would
be necessary. Missing, duplicate, or unexpected nodes are errors; no output is
written in those cases.

``--expected-root`` makes export scope machine-checkable. A screen export must
name exactly the screen root; a flow export must explicitly name all of its
roots, including annotations. ``--report`` writes a JSON assertion report so a
model does not need to inspect a screenshot to accept or reject the artifact.
``--scope-filter`` is build-only: it removes top-level export roots that Pencil
adds outside the approved scope (for example ``Flow Overlay`` in a screen
export). A later ``--check`` rejects, rather than hides, any such root.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


CLASS_ATTR_RE = re.compile(r"(\bclass\s*=\s*)([\"'])(.*?)(\2)", re.DOTALL)
ROUNDED_TOKEN = re.compile(
    r"rounded(?:-[trbl]{1,2})?(?:-\[[^\]]+\]|-(?:none|sm|md|lg|xl|2xl|3xl|full|\d+))"
)
HEIGHT_TOKEN = re.compile(r"h-(?:fit|\[(?:[^\]]+)\])")
VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}


class FixError(Exception):
    """An input mismatch that must not produce a patched output."""


def fail(message: str) -> None:
    raise FixError(message)


def load_inventory(path: Path) -> dict[str, dict[str, Any]]:
    try:
        raw = path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        fail(f"inventory not found: {path}")
    try:
        rows = json.loads(raw) if raw.startswith("[") else [
            json.loads(line) for line in raw.splitlines() if line.strip()
        ]
    except json.JSONDecodeError as exc:
        fail(f"inventory is not valid JSON: {exc}")
    if not isinstance(rows, list) or not rows:
        fail("inventory must be a non-empty JSON array or JSONL file")

    by_id: dict[str, dict[str, Any]] = {}
    paths: set[tuple[int, ...]] = set()
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            fail(f"inventory row {index} is not an object")
        node_id, name, path_value = row.get("id"), row.get("name"), row.get("path")
        if not isinstance(node_id, str) or not node_id:
            fail(f"inventory row {index} missing string id")
        if not isinstance(name, str) or not name:
            fail(f"inventory row {index} ({node_id}) missing string name")
        if not isinstance(path_value, list) or not path_value or any(
            not isinstance(part, int) or part < 0 for part in path_value
        ):
            fail(f"inventory row {index} ({node_id}) needs non-empty integer path")
        path_key = tuple(path_value)
        if node_id in by_id:
            fail(f"duplicate inventory id: {node_id}")
        if path_key in paths:
            fail(f"duplicate inventory path: {list(path_key)}")
        by_id[node_id] = row
        paths.add(path_key)
    return by_id


@dataclass
class PencilElement:
    name: str
    path: tuple[int, ...]
    attrs: dict[str, str | None]
    start: int
    end: int
    text: str
    next_child: int = 0
    close_end: int | None = None


@dataclass
class StackEntry:
    tag: str
    pencil: PencilElement | None


class PencilHTMLParser(HTMLParser):
    """Extract named export nodes while retaining their exact source ranges."""

    def __init__(self, source: str) -> None:
        super().__init__(convert_charrefs=False)
        self.source = source
        self.cursor = 0
        self.stack: list[StackEntry] = []
        self.pencil_stack: list[PencilElement] = []
        self.roots = 0
        self.elements: list[PencilElement] = []
        self.line_starts = [0]
        self.line_starts.extend(index + 1 for index, char in enumerate(source) if char == "\n")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._start(tag, attrs, False)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._start(tag, attrs, True)

    def _start(self, tag: str, attrs: list[tuple[str, str | None]], self_closing: bool) -> None:
        text = self.get_starttag_text()
        start = self.source.find(text, self.cursor)
        if start < 0:
            fail("could not locate parsed HTML start tag in source")
        self.cursor = start + len(text)
        attr_map = {key.lower(): value for key, value in attrs}
        pencil: PencilElement | None = None
        name = attr_map.get("data-pencil-name")
        if name is not None:
            if not name:
                fail("HTML contains an empty data-pencil-name")
            if self.pencil_stack:
                parent = self.pencil_stack[-1]
                path = parent.path + (parent.next_child,)
                parent.next_child += 1
            else:
                path = (self.roots,)
                self.roots += 1
            pencil = PencilElement(name, path, attr_map, start, self.cursor, text)
            self.elements.append(pencil)

        entry = StackEntry(tag.lower(), pencil)
        if not self_closing and tag.lower() not in VOID_TAGS:
            self.stack.append(entry)
            if pencil is not None:
                self.pencil_stack.append(pencil)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        line, column = self.getpos()
        end_start = self.line_starts[line - 1] + column
        end = self.source.find(">", end_start)
        if end < 0:
            fail("could not locate parsed HTML end tag in source")
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index].tag != tag:
                continue
            popped = self.stack[index:]
            del self.stack[index:]
            if popped[0].pencil is not None:
                popped[0].pencil.close_end = end + 1
            for entry in reversed(popped):
                if entry.pencil is not None:
                    if not self.pencil_stack or self.pencil_stack[-1] is not entry.pencil:
                        fail("HTML nesting did not preserve Pencil node hierarchy")
                    self.pencil_stack.pop()
            return


def parse_elements(source: str) -> list[PencilElement]:
    parser = PencilHTMLParser(source)
    try:
        parser.feed(source)
        parser.close()
    except FixError:
        raise
    except Exception as exc:
        fail(f"could not parse HTML: {exc}")
    if not parser.elements:
        fail("HTML has no data-pencil-name nodes; this is not a Pencil HTML export")
    return parser.elements


def px(value: int | float) -> str:
    return f"{int(value) if isinstance(value, float) and value.is_integer() else value}px"


def numeric_value(node: dict[str, Any], modern: str, legacy: str) -> int | float | None:
    value = node.get(modern, node.get(legacy))
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value


def radius_classes(radius: Any) -> list[str] | None:
    if isinstance(radius, bool):
        return None
    if isinstance(radius, (int, float)):
        return [f"rounded-[{px(radius)}]"]
    if not isinstance(radius, list) or len(radius) != 4:
        return None
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in radius):
        fail("cornerRadius/r must be a number or four numeric values")
    tl, tr, br, bl = radius
    if tl == tr == br == bl:
        return [f"rounded-[{px(tl)}]"] if tl else []
    return [
        f"rounded-{side}-[{px(value)}]"
        for side, value in (("tl", tl), ("tr", tr), ("br", br), ("bl", bl))
        if value
    ]


def target_height(node: dict[str, Any]) -> int | None:
    explicit = numeric_value(node, "height", "h")
    if explicit is not None:
        return int(round(explicit))
    if not node.get("dockBottom"):
        return None
    y = numeric_value(node, "y", "y")
    parent_height = numeric_value(node, "parentBoundsHeight", "pbh")
    if y is None or parent_height is None:
        fail(f"dockBottom node {node['id']} needs numeric y and parentBoundsHeight")
    return max(int(round(parent_height - y)), 1)


def patch_class(value: str, node: dict[str, Any]) -> tuple[str, list[str]]:
    tokens = value.split()
    notes: list[str] = []

    radius = node.get("cornerRadius", node.get("r"))
    classes = radius_classes(radius)
    if classes is not None:
        updated = [token for token in tokens if not ROUNDED_TOKEN.fullmatch(token)] + classes
        if updated != tokens:
            notes.append("radius")
        tokens = updated

    height = target_height(node)
    if height is not None:
        updated = [token for token in tokens if not HEIGHT_TOKEN.fullmatch(token)] + [f"h-[{height}px]"]
        if updated != tokens:
            notes.append(f"height={height}")
        tokens = updated

    if node.get("clip") is True:
        had_clip = "overflow-hidden" in tokens
        tokens = [token for token in tokens if token != "overflow-hidden"]
        tokens.append("overflow-hidden")
        if not had_clip:
            notes.append("clip")

    return " ".join(tokens), notes


def replace_class(tag: str, new_class: str, node_id: str) -> str:
    match = CLASS_ATTR_RE.search(tag)
    if match is None:
        fail(f"node {node_id} needs a class attribute for its requested patch")
    return tag[:match.start(3)] + new_class + tag[match.end(3):]


def inject_id(tag: str, node_id: str) -> str:
    close = " />" if tag.endswith("/>") else ">"
    before = tag[: -len(close)]
    return f'{before} data-pencil-id="{node_id}"{close}'


def validate_expected_roots(inventory: dict[str, dict[str, Any]], expected_roots: list[str]) -> list[str]:
    roots = sorted(row["id"] for row in inventory.values() if len(row["path"]) == 1)
    if not roots:
        fail("inventory has no root nodes")
    if expected_roots and set(roots) != set(expected_roots):
        missing = sorted(set(expected_roots) - set(roots))
        unexpected = sorted(set(roots) - set(expected_roots))
        fail(f"export root scope mismatch: missing={missing} unexpected={unexpected}")
    return roots


def filter_extra_roots(source: str, inventory: dict[str, dict[str, Any]], roots: list[str]) -> tuple[str, list[str]]:
    root_names = {inventory[node_id]["name"] for node_id in roots}
    if len(root_names) != len(roots):
        fail("approved export roots must have unique names")
    elements = parse_elements(source)
    extra = [element for element in elements if len(element.path) == 1 and element.name not in root_names]
    if not extra:
        return source, []
    removals: list[tuple[int, int]] = []
    for element in extra:
        if element.close_end is None:
            fail(f"cannot remove unclosed extra root: {element.name}")
        removals.append((element.start, element.close_end))
    output = source
    for start, end in reversed(removals):
        output = output[:start] + output[end:]
    return output, [element.name for element in extra]


def contract_report(output: str, inventory: dict[str, dict[str, Any]], roots: list[str]) -> dict[str, Any]:
    elements = parse_elements(output)
    by_id: dict[str, PencilElement] = {}
    for element in elements:
        node_id = element.attrs.get("data-pencil-id")
        if not node_id:
            fail("post-patch HTML is missing data-pencil-id")
        if node_id in by_id:
            fail(f"post-patch HTML has duplicate data-pencil-id: {node_id}")
        by_id[node_id] = element
    if set(by_id) != set(inventory):
        fail("post-patch HTML no longer matches inventory ids")

    docked: list[dict[str, Any]] = []
    clipped: list[str] = []
    for node_id, node in inventory.items():
        classes = (by_id[node_id].attrs.get("class") or "").split()
        expected_height = target_height(node)
        if expected_height is not None:
            required = f"h-[{expected_height}px]"
            if required not in classes:
                fail(f"post-patch node {node_id} lacks {required}")
        if node.get("dockBottom"):
            docked.append({"id": node_id, "height": expected_height, "ok": True})
        if node.get("clip") is True:
            if "overflow-hidden" not in classes:
                fail(f"post-patch node {node_id} lacks overflow-hidden")
            clipped.append(node_id)
    return {"roots": roots, "docked": docked, "clipped": clipped}


def build_output(
    source: str,
    inventory: dict[str, dict[str, Any]],
    check: bool,
    expected_roots: list[str] | None = None,
    scope_filter: bool = False,
) -> tuple[str, dict[str, Any]]:
    roots = validate_expected_roots(inventory, expected_roots or [])
    excluded_roots: list[str] = []
    if scope_filter:
        scoped_source, excluded_roots = filter_extra_roots(source, inventory, roots)
        if check and excluded_roots:
            fail(f"HTML contains roots outside approved scope: {excluded_roots}")
        source = scoped_source
    elements = parse_elements(source)
    paths = {element.path: element for element in elements}
    ids = [element.attrs.get("data-pencil-id") for element in elements]
    has_id = [value is not None for value in ids]
    if any(has_id) and not all(has_id):
        fail("HTML mixes nodes with and without data-pencil-id")

    injected = 0
    if not any(has_id):
        if check:
            fail("--check requires HTML that already has data-pencil-id")
        inventory_paths = {tuple(row["path"]): row for row in inventory.values()}
        if len(inventory_paths) != len(inventory) or len(inventory_paths) != len(elements):
            fail(
                "raw HTML requires a full inventory: one unique path for every "
                f"data-pencil-name node (HTML={len(elements)}, inventory={len(inventory)})"
            )
        if set(inventory_paths) != set(paths):
            missing = sorted(set(inventory_paths) - set(paths))
            extra = sorted(set(paths) - set(inventory_paths))
            fail(f"inventory/HTML path mismatch: missing_html={missing[:5]} extra_html={extra[:5]}")
        for path, element in paths.items():
            row = inventory_paths[path]
            if row["name"] != element.name:
                fail(f"name mismatch at path {list(path)}: inventory={row['name']!r} html={element.name!r}")
            element.attrs["data-pencil-id"] = row["id"]
            injected += 1
    else:
        seen_ids = [str(value) for value in ids]
        duplicates = sorted({node_id for node_id in seen_ids if seen_ids.count(node_id) > 1})
        if duplicates:
            fail(f"duplicate data-pencil-id in HTML: {duplicates[:5]}")
        if set(seen_ids) != set(inventory):
            missing = sorted(set(inventory) - set(seen_ids))
            unexpected = sorted(set(seen_ids) - set(inventory))
            fail(f"inventory/HTML id mismatch: missing_html={missing[:5]} unexpected_html={unexpected[:5]}")

    replacements: list[tuple[int, int, str]] = []
    patched: list[str] = []
    for element in elements:
        node_id = str(element.attrs["data-pencil-id"])
        node = inventory[node_id]
        tag = inject_id(element.text, node_id) if not any(has_id) else element.text
        old_class = element.attrs.get("class")
        new_class, notes = patch_class(old_class or "", node)
        if new_class != (old_class or ""):
            tag = replace_class(tag, new_class, node_id)
            patched.append(f"{node_id} {node['name']} {','.join(notes)}")
        if tag != element.text:
            replacements.append((element.start, element.end, tag))

    if check and patched:
        fail("HTML still needs patches: " + "; ".join(patched))
    output = source
    for start, end, replacement in reversed(replacements):
        output = output[:start] + replacement + output[end:]
    contract = contract_report(output, inventory, roots)
    return output, {
        "ok": True,
        "nodes": len(elements),
        "ids_injected": injected,
        "patched": patched,
        "excluded_roots": excluded_roots,
        **contract,
    }


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        os.replace(temp_name, path)
    except Exception:
        Path(temp_name).unlink(missing_ok=True)
        raise


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", required=True)
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--out")
    parser.add_argument("--check", action="store_true", help="verify an already patched file without writing")
    parser.add_argument("--expected-root", action="append", default=[], help="required exported root id; repeat per allowed root")
    parser.add_argument("--scope-filter", action="store_true", help="build-only: remove extra top-level roots before patching")
    parser.add_argument("--report", help="write a machine-readable JSON assertion report")
    args = parser.parse_args(argv[1:])
    if args.check == bool(args.out):
        parser.error("use exactly one of --out or --check")

    html_path = Path(args.html)
    if not html_path.is_file():
        print(f"fix_pen_html: html not found: {html_path}", file=sys.stderr)
        return 1
    try:
        output, report = build_output(
            html_path.read_text(encoding="utf-8"),
            load_inventory(Path(args.inventory)),
            args.check,
            args.expected_root,
            args.scope_filter,
        )
        if args.check:
            print(f"verified {report['nodes']} nodes; no patches needed")
        else:
            atomic_write(Path(args.out), output)
            print(f"wrote {args.out}")
            print(f"injected {report['ids_injected']} data-pencil-id attributes")
            print(f"patched {len(report['patched'])} nodes")
            for item in report["patched"]:
                print(f"  {item}")
        if args.report:
            atomic_write(Path(args.report), json.dumps(report, ensure_ascii=False, indent=2) + "\n")
            print(f"wrote report {args.report}")
    except FixError as exc:
        print(f"fix_pen_html: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
