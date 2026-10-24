# Quality checklist

Run both semantic review and script checks before delivery.

## Semantic review

- The latest user instruction produced a fresh manifest; no stale mapping or layout was reused after a correction.
- The manifest validates with no duplicate source assignment unless the second view uses `same_as`.
- Every active view has evidence or explicit inference permission; excluded views are not silently filled.
- All six faces depict the same device.
- Front/back orientation is not swapped.
- Left/right are defined from the viewer-facing front.
- Repeated features occupy compatible relative positions across views.
- Visible ports, vents, buttons, lights, labels, logos, screws, and seams are preserved.
- No unreadable or unseen text is invented.
- Hidden geometry is not described as observed.
- Any inferred face is listed in the delivery note.

## Visual cleanup

- Plain white background with no room, hand, stand, or photographic clutter.
- No white wedges, triangular remnants, halos, duplicated edges, or jagged cutout borders.
- No transparent fringe left around the device after compositing.
- Object scale is visually consistent across the six standalone views.
- Composite has generous, even spacing and no overlapping panels.
- Labels, when enabled, match the view filenames.
- The chosen layout template or normalized slots match the user's written or visual reference.
- View occupancy is consistent within the intended face orientation; wide top/bottom views are not forced into a misleading scale.

## Script checks

`validate_manifest.py` checks view mapping, `same_as`, inference permission, source files, layout bounds, and slot overlap. `inspect_result.py` checks file presence, readable PNGs, minimum dimensions, near-white borders, canvas contact, excessive blankness, and composite size. Passing script checks do not establish physical truth or semantic identity; a visual review remains mandatory.

## Regeneration rule

Regenerate only the failed view when possible. Do not replace accepted views merely because another face failed. Re-run normalization, composition, and inspection after the replacement.
