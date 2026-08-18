#!/usr/bin/env python3
"""Regression tests for the deterministic Pencil HTML repair pipeline."""

from __future__ import annotations

import tempfile
import unittest
import json
from pathlib import Path

import fix_pen_html as fix


RAW = '''<div data-pencil-name="Phone" class="h-fit rounded-[16px]">
  <div data-pencil-name="Sheet" class="h-fit rounded-[16px]"></div>
  <div data-pencil-name="Clipped" class="h-fit"></div>
</div>'''

RAW_WITH_FLOW_OVERLAY = RAW + '''
<div data-pencil-name="Flow Overlay" class="h-fit">
  <div data-pencil-name="Zone Border" class="h-fit"></div>
</div>'''

INVENTORY = {
    "phone": {"id": "phone", "name": "Phone", "path": [0], "height": 812, "clip": True},
    "sheet": {
        "id": "sheet", "name": "Sheet", "path": [0, 0],
        "cornerRadius": [16, 16, 0, 0], "dockBottom": True,
        "y": 300, "parentBoundsHeight": 812, "clip": False,
    },
    "clipped": {"id": "clipped", "name": "Clipped", "path": [0, 1], "clip": True},
}


class FixPenHtmlTests(unittest.TestCase):
    def test_raw_export_injects_ids_and_is_idempotent(self) -> None:
        patched, report = fix.build_output(RAW, INVENTORY, False)
        self.assertEqual(report["ids_injected"], 3)
        self.assertEqual(len(report["patched"]), 3)
        self.assertIn('data-pencil-id="sheet"', patched)
        self.assertIn('rounded-tl-[16px] rounded-tr-[16px] h-[512px]', patched)
        self.assertNotIn('rounded-br-[', patched)
        self.assertNotIn('rounded-bl-[', patched)
        self.assertNotIn('h-[512px] overflow-hidden" data-pencil-id="sheet"', patched)

        repeated, second_report = fix.build_output(patched, INVENTORY, False)
        self.assertEqual(repeated, patched)
        self.assertEqual(second_report["patched"], [])

    def test_existing_id_before_or_after_class_is_supported(self) -> None:
        html = '<div class="h-fit" data-pencil-id="phone" data-pencil-name="Phone"></div>'
        patched, report = fix.build_output(html, {"phone": INVENTORY["phone"]}, False)
        self.assertEqual(report["ids_injected"], 0)
        self.assertIn('class="h-[812px] overflow-hidden"', patched)

    def test_incomplete_inventory_fails_before_an_output_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            html = root / "raw.html"
            inventory = root / "inventory.jsonl"
            out = root / "patched.html"
            html.write_text(RAW, encoding="utf-8")
            inventory.write_text('{"id":"phone","name":"Phone","path":[0]}\n', encoding="utf-8")

            exit_code = fix.main(["fix_pen_html.py", "--html", str(html), "--inventory", str(inventory), "--out", str(out)])
            self.assertEqual(exit_code, 1)
            self.assertFalse(out.exists())

    def test_check_is_read_only_and_rejects_pending_patches(self) -> None:
        patched, _ = fix.build_output(RAW, INVENTORY, False)
        _, report = fix.build_output(patched, INVENTORY, True)
        self.assertEqual(report["patched"], [])
        with self.assertRaisesRegex(fix.FixError, "still needs patches"):
            fix.build_output(patched.replace("h-[512px]", "h-fit"), INVENTORY, True)

    def test_expected_root_and_report_are_machine_checkable(self) -> None:
        patched, report = fix.build_output(RAW, INVENTORY, False, ["phone"])
        self.assertEqual(report["roots"], ["phone"])
        self.assertEqual(report["docked"], [{"id": "sheet", "height": 512, "ok": True}])
        self.assertEqual(report["clipped"], ["phone", "clipped"])

        with self.assertRaisesRegex(fix.FixError, "export root scope mismatch"):
            fix.build_output(patched, INVENTORY, True, ["sheet"])

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            html = root / "patched.html"
            inventory = root / "inventory.jsonl"
            report_path = root / "report.json"
            html.write_text(patched, encoding="utf-8")
            inventory.write_text("\n".join(json.dumps(row) for row in INVENTORY.values()), encoding="utf-8")
            exit_code = fix.main([
                "fix_pen_html.py", "--html", str(html), "--inventory", str(inventory),
                "--check", "--expected-root", "phone", "--report", str(report_path),
            ])
            self.assertEqual(exit_code, 0)
            self.assertEqual(json.loads(report_path.read_text(encoding="utf-8"))["roots"], ["phone"])

    def test_scope_filter_removes_unapproved_export_root_only_while_building(self) -> None:
        patched, report = fix.build_output(RAW_WITH_FLOW_OVERLAY, INVENTORY, False, ["phone"], True)
        self.assertNotIn('data-pencil-name="Flow Overlay"', patched)
        self.assertEqual(report["excluded_roots"], ["Flow Overlay"])

        with self.assertRaisesRegex(fix.FixError, "roots outside approved scope"):
            fix.build_output(RAW_WITH_FLOW_OVERLAY, INVENTORY, True, ["phone"], True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
