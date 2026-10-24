"""Validate an equipment six-view mapping and layout manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


VIEWS = ("front", "back", "left", "right", "top", "bottom")
EVIDENCE_STATUSES = {"direct", "partial", "inferred", "same_as", "excluded"}
LABEL_MODES = {"none", "zh", "en", "bilingual"}
TEMPLATES = {"front_center_surrounding_back_right"}
BEAUTIFY_MODES = {"none", "smart"}
CLEANUP_STATUSES = {"approved", "pending", "needs_review", "same_as"}
CLEANUP_METHODS = {"ai_cutout", "manual_cutout", "already_clean", "same_as"}
RETOUCH_STATUSES = {"approved", "not_requested", "pending", "needs_review", "same_as"}
RETOUCH_METHODS = {"ai_retouch", "manual_retouch", "already_clean", "none", "same_as"}


class ManifestError(ValueError):
    """Raised when a manifest cannot be safely composed."""


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ManifestError(f"Cannot read manifest: {error}") from error
    if not isinstance(value, dict):
        raise ManifestError("Manifest root must be a JSON object")
    return value


def template_slots(name: str) -> dict[str, dict[str, float]]:
    if name != "front_center_surrounding_back_right":
        raise ManifestError(f"Unknown layout template: {name}")
    return {
        "left": {"x": 0.025, "y": 0.30, "width": 0.215, "height": 0.39},
        "front": {"x": 0.257, "y": 0.30, "width": 0.215, "height": 0.39},
        "right": {"x": 0.489, "y": 0.30, "width": 0.215, "height": 0.39},
        "back": {"x": 0.721, "y": 0.30, "width": 0.215, "height": 0.39},
        "top": {"x": 0.257, "y": 0.025, "width": 0.215, "height": 0.18},
        "bottom": {"x": 0.257, "y": 0.75, "width": 0.215, "height": 0.20},
    }


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _rectangles_overlap(first: dict[str, float], second: dict[str, float]) -> bool:
    return not (
        first["x"] + first["width"] <= second["x"]
        or second["x"] + second["width"] <= first["x"]
        or first["y"] + first["height"] <= second["y"]
        or second["y"] + second["height"] <= first["y"]
    )


def _resolve_source_id(view: str, views: dict[str, Any], seen: set[str] | None = None) -> str:
    seen = seen or set()
    if view in seen:
        raise ManifestError(f"same_as cycle detected at view: {view}")
    seen.add(view)
    config = views[view]
    target = config.get("same_as")
    if target is not None:
        if target not in views or target not in VIEWS:
            raise ManifestError(f"View {view} has unknown same_as target: {target}")
        return _resolve_source_id(target, views, seen)
    source_id = config.get("source_id")
    if not isinstance(source_id, str) or not source_id:
        raise ManifestError(f"View {view} must define source_id or same_as")
    return source_id


def validate_manifest(
    manifest: dict[str, Any],
    manifest_path: Path | None = None,
    require_files: bool = True,
) -> dict[str, Any]:
    errors: list[str] = []
    if manifest.get("schema_version") != 1:
        errors.append("schema_version must be 1")

    sources = manifest.get("sources")
    if not isinstance(sources, dict) or not sources:
        errors.append("sources must be a non-empty object mapping source_id to file path")
        sources = {}
    for source_id, source_path in sources.items():
        if not isinstance(source_id, str) or not source_id:
            errors.append("source IDs must be non-empty strings")
        if not isinstance(source_path, str) or not source_path:
            errors.append(f"source {source_id!r} must have a non-empty file path")

    views = manifest.get("views")
    if not isinstance(views, dict):
        errors.append("views must be an object")
        views = {}
    unknown_views = sorted(set(views) - set(VIEWS))
    if unknown_views:
        errors.append(f"unknown view names: {', '.join(unknown_views)}")

    allow_inference = manifest.get("allow_inference", False)
    if not isinstance(allow_inference, bool):
        errors.append("allow_inference must be true or false")
        allow_inference = False

    beautify_mode = manifest.get("beautify_mode")
    if beautify_mode not in BEAUTIFY_MODES:
        errors.append("beautify_mode is required and must be none or smart")

    used_sources: dict[str, str] = {}
    for view in VIEWS:
        config = views.get(view)
        if not isinstance(config, dict):
            errors.append(f"missing view configuration: {view}")
            continue
        status = config.get("evidence_status", "direct")
        if status not in EVIDENCE_STATUSES:
            errors.append(f"{view}: invalid evidence_status {status!r}")
        if status == "inferred" and not allow_inference:
            errors.append(f"{view}: inferred view requires allow_inference=true")

        same_as = config.get("same_as")
        source_id = config.get("source_id")
        if status == "excluded":
            if same_as is not None or source_id is not None:
                errors.append(f"{view}: excluded view cannot define source_id or same_as")
            continue
        if same_as is not None:
            if source_id is not None:
                errors.append(f"{view}: use either same_as or source_id, not both")
            if status != "same_as":
                errors.append(f"{view}: same_as requires evidence_status=same_as")
            if config.get("cleanup_status") != "same_as":
                errors.append(f"{view}: same_as requires cleanup_status=same_as")
            if config.get("retouch_status") != "same_as":
                errors.append(f"{view}: same_as requires retouch_status=same_as")
            if config.get("retouch_method") != "same_as":
                errors.append(f"{view}: same_as requires retouch_method=same_as")
            try:
                resolved = _resolve_source_id(view, views)
                if resolved in used_sources and used_sources[resolved] != view:
                    pass
            except ManifestError as error:
                errors.append(str(error))
            rotation = config.get("rotation", 0)
            if rotation not in (0, 90, 180, 270):
                errors.append(f"{view}: rotation must be 0, 90, 180, or 270")
            continue

        if not isinstance(source_id, str) or not source_id:
            errors.append(f"{view}: source_id is required")
            continue
        if source_id not in sources:
            errors.append(f"{view}: unknown source_id {source_id!r}")
        if source_id in used_sources:
            errors.append(
                f"source_id {source_id!r} is assigned to both {used_sources[source_id]} and {view}; "
                "use same_as for intentional reuse"
            )
        else:
            used_sources[source_id] = view
        cleanup_status = config.get("cleanup_status")
        if cleanup_status not in CLEANUP_STATUSES:
            errors.append(f"{view}: cleanup_status must be one of: {', '.join(sorted(CLEANUP_STATUSES))}")
        elif cleanup_status != "approved":
            errors.append(f"{view}: cutout refinement must be approved before composition")
        cleanup_method = config.get("cleanup_method")
        if cleanup_method not in CLEANUP_METHODS or cleanup_method == "same_as":
            errors.append(f"{view}: cleanup_method must be ai_cutout, manual_cutout, or already_clean")
        refined_path = config.get("refined_path")
        if refined_path is not None and (not isinstance(refined_path, str) or not refined_path):
            errors.append(f"{view}: refined_path must be a non-empty file path")
        if cleanup_method in {"ai_cutout", "manual_cutout"} and not refined_path:
            errors.append(f"{view}: refined_path is required after cutout refinement")
        retouch_status = config.get("retouch_status")
        if retouch_status not in RETOUCH_STATUSES:
            errors.append(f"{view}: retouch_status must be one of: {', '.join(sorted(RETOUCH_STATUSES))}")
        retouch_method = config.get("retouch_method")
        if retouch_method not in RETOUCH_METHODS or retouch_method == "same_as":
            errors.append(f"{view}: retouch_method is invalid")
        elif beautify_mode == "none":
            if retouch_status != "not_requested":
                errors.append(f"{view}: none mode requires retouch_status=not_requested")
            if retouch_method != "none":
                errors.append(f"{view}: none mode requires retouch_method=none")
        elif beautify_mode == "smart":
            if retouch_status != "approved":
                errors.append(f"{view}: smart mode requires retouch_status=approved")
            if retouch_method not in {"ai_retouch", "manual_retouch", "already_clean"}:
                errors.append(f"{view}: smart mode requires an approved retouch method")
        if retouch_method in {"ai_retouch", "manual_retouch"} and not refined_path:
            errors.append(f"{view}: refined_path is required after product retouching")
        rotation = config.get("rotation", 0)
        if rotation not in (0, 90, 180, 270):
            errors.append(f"{view}: rotation must be 0, 90, 180, or 270")

    layout = manifest.get("layout")
    if not isinstance(layout, dict):
        errors.append("layout must be an object")
        layout = {}
    template = layout.get("template")
    explicit_slots = layout.get("slots")
    if template is not None and explicit_slots is not None:
        errors.append("layout cannot define both template and slots")
    try:
        slots = template_slots(template) if template else explicit_slots
    except ManifestError as error:
        errors.append(str(error))
        slots = {}
    if not isinstance(slots, dict):
        errors.append("layout must define a known template or slots object")
        slots = {}

    active_views = [
        view
        for view in VIEWS
        if isinstance(views.get(view), dict) and views[view].get("evidence_status", "direct") != "excluded"
    ]
    for view in active_views:
        slot = slots.get(view)
        if not isinstance(slot, dict):
            errors.append(f"layout slot missing for view: {view}")
            continue
        for key in ("x", "y", "width", "height"):
            if not _number(slot.get(key)):
                errors.append(f"layout slot {view}.{key} must be numeric")
        if all(_number(slot.get(key)) for key in ("x", "y", "width", "height")):
            if not 0 <= slot["x"] < 1 or not 0 <= slot["y"] < 1:
                errors.append(f"layout slot {view} x/y must be in [0, 1)")
            if not 0 < slot["width"] <= 1 or not 0 < slot["height"] <= 1:
                errors.append(f"layout slot {view} width/height must be in (0, 1]")
            if slot["x"] + slot["width"] > 1 or slot["y"] + slot["height"] > 1:
                errors.append(f"layout slot {view} extends outside the canvas")

    active_slots = [(view, slots[view]) for view in active_views if view in slots and isinstance(slots[view], dict)]
    for index, (first_name, first) in enumerate(active_slots):
        if not all(_number(first.get(key)) for key in ("x", "y", "width", "height")):
            continue
        for second_name, second in active_slots[index + 1 :]:
            if not all(_number(second.get(key)) for key in ("x", "y", "width", "height")):
                continue
            if _rectangles_overlap(first, second):
                errors.append(f"layout slots overlap: {first_name} and {second_name}")

    labels = manifest.get("labels", "none")
    if labels not in LABEL_MODES:
        errors.append(f"labels must be one of: {', '.join(sorted(LABEL_MODES))}")

    output = manifest.get("output", {})
    if not isinstance(output, dict):
        errors.append("output must be an object")
    elif not isinstance(output.get("standalone", True), bool):
        errors.append("output.standalone must be true or false")

    canvas_size = layout.get("canvas_size", 4096)
    standalone_size = layout.get("standalone_size", 2048)
    for name, value in (("canvas_size", canvas_size), ("standalone_size", standalone_size)):
        if not isinstance(value, int) or value < 256:
            errors.append(f"layout.{name} must be an integer >= 256")

    if require_files and manifest_path is not None:
        base_dir = manifest_path.parent
        for source_id, source_path in sources.items():
            if not isinstance(source_path, str):
                continue
            path = Path(source_path)
            if not path.is_absolute():
                path = base_dir / path
            if not path.is_file():
                errors.append(f"source file not found for {source_id}: {path}")
        for view in VIEWS:
            config = views.get(view)
            if not isinstance(config, dict) or config.get("evidence_status", "direct") == "excluded":
                continue
            if config.get("same_as") is not None:
                continue
            refined_path = config.get("refined_path")
            if not isinstance(refined_path, str) or not refined_path:
                continue
            path = Path(refined_path)
            if not path.is_absolute():
                path = base_dir / path
            if not path.is_file():
                errors.append(f"refined file not found for {view}: {path}")

    if errors:
        raise ManifestError("\n".join(f"- {error}" for error in errors))

    return {
        "sources": sources,
        "views": views,
        "slots": slots,
        "beautify_mode": beautify_mode,
        "labels": labels,
        "canvas_size": canvas_size,
        "standalone_size": standalone_size,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--skip-file-check", action="store_true")
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        manifest = load_manifest(args.manifest)
        normalized = validate_manifest(
            manifest,
            args.manifest,
            require_files=not args.skip_file_check,
        )
    except ManifestError as error:
        print(str(error), file=sys.stderr)
        return 1
    active = sum(1 for config in normalized["views"].values() if config.get("evidence_status", "direct") != "excluded")
    print(f"Manifest is valid: {active} active view(s), {len(normalized['slots'])} layout slot(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
