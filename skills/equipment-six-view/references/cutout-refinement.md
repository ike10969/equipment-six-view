# Cutout refinement procedure

Use this procedure whenever an input is a real photo, contains a hand or room background, or has a visible photographic shadow. Do not send the raw image directly to a six-view compositor.

## Refinement instruction

Use the available image-editing capability with the following constraints:

```text
Isolate the exact device from the supplied image onto a transparent or pure white background.
Remove hands, people, room/floor/background, stands, cables that are not part of the device, and unwanted photographic shadows.
Preserve the device's real silhouette, corners, ports, buttons, seams, vents, labels, screws, reflections, material texture, and visible wear.
Do not redesign, repaint, reshape, mirror, or add hidden components.
Do not reconstruct a feature covered by a hand or object. Keep that area unresolved and report it for review.
Clean the contour at high zoom: remove halos, white wedges, jagged edges, holes, and transparent fringe.
Return a clean product-reference cutout with the same orientation as the source.
```

## Approval gate

Review the refined image at high zoom before marking it approved:

- the entire visible device is retained;
- no hand, floor, room, stand, or unrelated cable remains;
- no real device feature was erased;
- the contour has no halo, wedge, hole, or jagged fringe;
- the background is transparent or uniformly white;
- the orientation and proportions are unchanged.

If an occlusion hides a feature, use `cleanup_status: needs_review` and request a clearer source or explicit inference permission. Do not mark the image approved just because the object is in the correct position.

## Manifest fields

Keep the original source in `sources`. Put the cleaned image in `refined_path` and set:

```json
{
  "cleanup_status": "approved",
  "cleanup_method": "ai_cutout",
  "refined_path": "refined/front.png"
}
```

Use `cleanup_method: manual_cutout` for a manually corrected mask. Use `cleanup_method: already_clean` only when a supplied candidate view already has a clean background and passes the same visual review. `same_as` views inherit the approved refined image from their target view.
