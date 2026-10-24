"""Compose a six-view sheet from an explicit mapping and layout manifest."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from compose_six_views import _find_font, _paste_object
from validate_manifest import ManifestError, VIEWS, _resolve_source_id, load_manifest, validate_manifest


LABELS = {
    "zh": {
        "front": "正面",
        "back": "背面",
        "left": "左侧",
        "right": "右侧",
        "top": "俯视",
        "bottom": "底视",
    },
    "en": {
        "front": "FRONT",
        "back": "BACK",
        "left": "LEFT",
        "right": "RIGHT",
        "top": "TOP",
        "bottom": "BOTTOM",
    },
}


def _label(view: str, mode: str) -> str:
    if mode == "zh":
        return LABELS["zh"][view]
    if mode == "en":
        return LABELS["en"][view]
    return f"{LABELS['zh'][view]} / {LABELS['en'][view]}"


def _draw_label(canvas: Image.Image, view: str, slot: tuple[int, int, int, int], font: ImageFont.ImageFont, mode: str) -> None:
    left, top, width, height = slot
    draw = ImageDraw.Draw(canvas)
    text = _label(view, mode)
    bounds = draw.textbbox((0, 0), text, font=font)
    x = left + (width - (bounds[2] - bounds[0])) // 2
    y = top + height - max(32, font.size + 12)
    draw.text((x, y), text, fill=(92, 92, 92, 255), font=font)


def _source_path(manifest_path: Path, path_value: str) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else manifest_path.parent / path


def _pixel_slot(slot: dict[str, float], size: int) -> tuple[int, int, int, int]:
    return (
        round(slot["x"] * size),
        round(slot["y"] * size),
        max(1, round(slot["width"] * size)),
        max(1, round(slot["height"] * size)),
    )


def _load_view(manifest_path: Path, normalized: dict, view: str) -> Image.Image:
    source_id = _resolve_source_id(view, normalized["views"])
    source = _source_path(manifest_path, normalized["sources"][source_id])
    with Image.open(source) as image:
        result = ImageOps.exif_transpose(image).convert("RGBA")
    rotation = normalized["views"][view].get("rotation", 0)
    if rotation:
        result = result.rotate(rotation, expand=True)
    return result


def compose(manifest_path: Path, output_dir: Path, label_override: str | None = None) -> None:
    manifest = load_manifest(manifest_path)
    normalized = validate_manifest(manifest, manifest_path, require_files=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    active_views = [
        view
        for view in VIEWS
        if normalized["views"].get(view, {}).get("evidence_status", "direct") != "excluded"
    ]
    images = {view: _load_view(manifest_path, normalized, view) for view in active_views}
    label_mode = label_override or normalized["labels"]

    if manifest.get("output", {}).get("standalone", True):
        for view, image in images.items():
            standalone = Image.new("RGBA", (normalized["standalone_size"], normalized["standalone_size"]), "white")
            _paste_object(standalone, image, (0, 0, normalized["standalone_size"], normalized["standalone_size"]))
            standalone.convert("RGB").save(output_dir / f"{view}.png", format="PNG", optimize=True)

    canvas_size = normalized["canvas_size"]
    composite = Image.new("RGBA", (canvas_size, canvas_size), "white")
    font = _find_font(max(18, round(canvas_size * 0.014))) if label_mode != "none" else None
    for view, image in images.items():
        slot = _pixel_slot(normalized["slots"][view], canvas_size)
        _paste_object(composite, image, slot)
        if font is not None:
            _draw_label(composite, view, slot, font, label_mode)
    composite.convert("RGB").save(output_dir / "six-view-composite.png", format="PNG", optimize=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--labels", choices=("none", "zh", "en", "bilingual"))
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        compose(args.manifest, args.output_dir, args.labels)
    except (ManifestError, OSError, KeyError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(f"Wrote manifest-driven six-view deliverables into {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
