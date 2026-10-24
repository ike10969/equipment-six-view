from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw


SKILL_ROOT = Path(__file__).parents[1] / "skills" / "equipment-six-view"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from validate_manifest import ManifestError, validate_manifest  # noqa: E402
from compose_from_manifest import compose  # noqa: E402


class ManifestWorkflowTests(unittest.TestCase):
    def _make_inputs(self, root: Path) -> Path:
        raw = root / "raw"
        refined = root / "refined"
        raw.mkdir()
        refined.mkdir()
        for name, color in {
            "front": (30, 30, 30),
            "back": (50, 50, 50),
            "left": (70, 70, 70),
            "top": (90, 90, 90),
            "bottom": (110, 110, 110),
        }.items():
            image = Image.new("RGB", (320, 180), (210, 40, 40))
            draw = ImageDraw.Draw(image)
            draw.rectangle((40, 30, 280, 150), fill=color)
            image.save(raw / f"{name}.png")
            clean = Image.new("RGB", (320, 180), "white")
            clean_draw = ImageDraw.Draw(clean)
            clean_draw.rectangle((40, 30, 280, 150), fill=color)
            clean.save(refined / f"{name}.png")
        return raw

    def test_same_as_manifest_composes_named_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._make_inputs(root)
            manifest_path = root / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "allow_inference": False,
                        "beautify_mode": "smart",
                        "sources": {
                            "front": "raw/front.png",
                            "back": "raw/back.png",
                            "left": "raw/left.png",
                            "top": "raw/top.png",
                            "bottom": "raw/bottom.png",
                        },
                        "views": {
                            "front": {"source_id": "front", "evidence_status": "direct", "cleanup_status": "approved", "cleanup_method": "ai_cutout", "retouch_status": "approved", "retouch_method": "ai_retouch", "refined_path": "refined/front.png"},
                            "back": {"source_id": "back", "evidence_status": "direct", "cleanup_status": "approved", "cleanup_method": "ai_cutout", "retouch_status": "approved", "retouch_method": "ai_retouch", "refined_path": "refined/back.png"},
                            "left": {"source_id": "left", "evidence_status": "direct", "cleanup_status": "approved", "cleanup_method": "ai_cutout", "retouch_status": "approved", "retouch_method": "ai_retouch", "refined_path": "refined/left.png"},
                            "right": {"same_as": "left", "evidence_status": "same_as", "cleanup_status": "same_as", "retouch_status": "same_as", "retouch_method": "same_as"},
                            "top": {"source_id": "top", "evidence_status": "direct", "cleanup_status": "approved", "cleanup_method": "ai_cutout", "retouch_status": "approved", "retouch_method": "ai_retouch", "refined_path": "refined/top.png"},
                            "bottom": {"source_id": "bottom", "evidence_status": "direct", "cleanup_status": "approved", "cleanup_method": "ai_cutout", "retouch_status": "approved", "retouch_method": "ai_retouch", "refined_path": "refined/bottom.png"},
                        },
                        "layout": {"template": "front_center_surrounding_back_right"},
                        "labels": "none",
                    }
                ),
                encoding="utf-8",
            )
            validate_manifest(json.loads(manifest_path.read_text()), manifest_path)
            output = root / "deliverables"
            compose(manifest_path, output)
            self.assertTrue((output / "six-view-composite.png").is_file())
            self.assertTrue((output / "right.png").is_file())
            with Image.open(output / "front.png") as image:
                self.assertEqual(image.getpixel((0, 0)), (255, 255, 255))

    def test_duplicate_source_requires_same_as(self) -> None:
        manifest = {
            "schema_version": 1,
            "sources": {"one": "one.png"},
            "views": {
                view: {"source_id": "one", "evidence_status": "direct"}
                for view in ("front", "back", "left", "right", "top", "bottom")
            },
            "layout": {"template": "front_center_surrounding_back_right"},
        }
        with self.assertRaises(ManifestError):
            validate_manifest(manifest, require_files=False)

    def test_inference_requires_explicit_opt_in(self) -> None:
        manifest = {
            "schema_version": 1,
            "sources": {"one": "one.png"},
            "views": {
                "front": {"source_id": "one", "evidence_status": "inferred"},
                **{
                    view: {"evidence_status": "excluded"}
                    for view in ("back", "left", "right", "top", "bottom")
                },
            },
            "layout": {"template": "front_center_surrounding_back_right"},
        }
        with self.assertRaises(ManifestError):
            validate_manifest(manifest, require_files=False)

    def test_pending_cutout_is_rejected(self) -> None:
        manifest = {
            "schema_version": 1,
            "sources": {"one": "one.png"},
            "views": {
                "front": {
                    "source_id": "one",
                    "evidence_status": "direct",
                    "cleanup_status": "pending",
                    "cleanup_method": "ai_cutout",
                    "refined_path": "refined/front.png",
                },
                **{
                    view: {"evidence_status": "excluded"}
                    for view in ("back", "left", "right", "top", "bottom")
                },
            },
            "layout": {"template": "front_center_surrounding_back_right"},
        }
        with self.assertRaises(ManifestError):
            validate_manifest(manifest, require_files=False)

    def test_missing_beautify_choice_is_rejected(self) -> None:
        manifest = {
            "schema_version": 1,
            "sources": {"one": "one.png"},
            "views": {
                "front": {
                    "source_id": "one",
                    "evidence_status": "direct",
                    "cleanup_status": "approved",
                    "cleanup_method": "already_clean",
                    "retouch_status": "not_requested",
                    "retouch_method": "none",
                },
                **{
                    view: {"evidence_status": "excluded"}
                    for view in ("back", "left", "right", "top", "bottom")
                },
            },
            "layout": {"template": "front_center_surrounding_back_right"},
        }
        with self.assertRaises(ManifestError):
            validate_manifest(manifest, require_files=False)

    def test_none_mode_requires_no_retouch(self) -> None:
        manifest = {
            "schema_version": 1,
            "beautify_mode": "none",
            "sources": {"one": "one.png"},
            "views": {
                "front": {
                    "source_id": "one",
                    "evidence_status": "direct",
                    "cleanup_status": "approved",
                    "cleanup_method": "already_clean",
                    "retouch_status": "approved",
                    "retouch_method": "ai_retouch",
                },
                **{
                    view: {"evidence_status": "excluded"}
                    for view in ("back", "left", "right", "top", "bottom")
                },
            },
            "layout": {"template": "front_center_surrounding_back_right"},
        }
        with self.assertRaises(ManifestError):
            validate_manifest(manifest, require_files=False)

    def test_none_mode_manifest_is_valid(self) -> None:
        manifest = {
            "schema_version": 1,
            "beautify_mode": "none",
            "sources": {"one": "one.png"},
            "views": {
                "front": {
                    "source_id": "one",
                    "evidence_status": "direct",
                    "cleanup_status": "approved",
                    "cleanup_method": "already_clean",
                    "retouch_status": "not_requested",
                    "retouch_method": "none",
                },
                **{
                    view: {"evidence_status": "excluded"}
                    for view in ("back", "left", "right", "top", "bottom")
                },
            },
            "layout": {"template": "front_center_surrounding_back_right"},
        }
        normalized = validate_manifest(manifest, require_files=False)
        self.assertEqual(normalized["beautify_mode"], "none")


if __name__ == "__main__":
    unittest.main()
