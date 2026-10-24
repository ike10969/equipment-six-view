# Manifest schema

Use a manifest whenever the user specifies image-to-view mapping, excludes a view, reuses an identical side, or provides a custom composite layout. The manifest is the executable contract between the user's instructions and the compositor.

```json
{
  "schema_version": 1,
  "allow_inference": false,
  "sources": {
    "candidate_01": "raw/front.png",
    "candidate_02": "raw/back.png",
    "candidate_03": "raw/left.png",
    "candidate_04": "raw/top.png",
    "candidate_05": "raw/bottom.png"
  },
  "views": {
    "front": {"source_id": "candidate_01", "evidence_status": "direct", "cleanup_status": "approved", "cleanup_method": "ai_cutout", "refined_path": "refined/front.png"},
    "back": {"source_id": "candidate_02", "evidence_status": "direct", "cleanup_status": "approved", "cleanup_method": "ai_cutout", "refined_path": "refined/back.png"},
    "left": {"source_id": "candidate_03", "evidence_status": "direct", "cleanup_status": "approved", "cleanup_method": "ai_cutout", "refined_path": "refined/left.png"},
    "right": {"same_as": "left", "evidence_status": "same_as", "cleanup_status": "same_as"},
    "top": {"source_id": "candidate_04", "evidence_status": "direct", "cleanup_status": "approved", "cleanup_method": "ai_cutout", "refined_path": "refined/top.png"},
    "bottom": {"source_id": "candidate_05", "evidence_status": "direct", "cleanup_status": "approved", "cleanup_method": "ai_cutout", "refined_path": "refined/bottom.png"}
  },
  "layout": {
    "template": "front_center_surrounding_back_right",
    "canvas_size": 4096,
    "standalone_size": 2048
  },
  "labels": "none",
  "output": {"standalone": true}
}
```

Rules:

- `sources` maps stable IDs to files; do not use upload order as an implicit mapping.
- Each active view uses `source_id` or `same_as`, never both.
- Reusing a source for another view requires `same_as`; accidental duplicate assignments are rejected.
- Raw source files remain evidence. `refined_path` points to the approved cutout that the compositor actually uses.
- Active direct views require `cleanup_status=approved` and `cleanup_method` of `ai_cutout`, `manual_cutout`, or `already_clean`.
- `cleanup_method=ai_cutout` or `manual_cutout` requires `refined_path`; use `already_clean` only after visually reviewing an already-isolated candidate image.
- `pending` and `needs_review` cutouts are rejected before composition.
- `same_as` views use `cleanup_status=same_as` and inherit the target view's refined image.
- `excluded` views have no source and no layout slot.
- `allow_inference` must be `true` before any view can be marked `inferred`.
- `front_center_surrounding_back_right` is a named layout template, not a universal requirement. Use explicit normalized `x`, `y`, `width`, and `height` slots for other arrangements.
- `labels` accepts `none`, `zh`, `en`, or `bilingual`.

Validate before composing:

```powershell
python scripts/validate_manifest.py --manifest <manifest.json>
python scripts/compose_from_manifest.py --manifest <manifest.json> --output-dir <deliverables>
```

If the user corrects an earlier mapping or layout, discard the previous manifest and create a new one from the latest instruction before running either command.
