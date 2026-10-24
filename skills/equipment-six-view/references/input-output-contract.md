# Input and output contract

## Recommended input

The skill accepts two or more ordinary device photos. The best evidence set includes:

- a straight-on front photo;
- a straight-on back photo;
- left and right side photos;
- top and bottom photos when those faces contain meaningful details;
- angled photos to clarify depth, corners, and transitions.

Optional user metadata can be supplied as prose or JSON:

```json
{
  "device_name": "example device",
  "known_dimensions_mm": {
    "width": 0,
    "height": 0,
    "depth": 0
  },
  "scale_reference": "A ruler is visible in front of the device",
  "requested_labels": true
}
```

Known dimensions and scale references may improve relative proportions. They do not turn the output into a measured engineering drawing.

Before refinement, ask the user to choose one product-image mode for the whole set:

- `none`: cutout and edge repair only; preserve the original visible product condition.
- `smart`: cutout plus conservative cleanup of screen-protector bubbles, reflections, dust, fingerprints, and capture defects.

Do not start refinement or composition until this choice is recorded as `beautify_mode` in the manifest.

## View names

Use these exact filenames and semantic meanings:

| File | Meaning |
| --- | --- |
| `front.png` | User-designated front face; if the user does not define it, use the primary operating or presentation face |
| `back.png` | Opposite face |
| `left.png` | Device's left side when facing the front |
| `right.png` | Device's right side when facing the front |
| `top.png` | Upper face |
| `bottom.png` | Lower face |

The normalized view directory should contain one file for each name. PNG is preferred; JPEG and WebP are accepted as input.

Raw photos must pass a cutout-refinement step before they become normalized views. In `smart` mode they must also pass product retouching. Keep the original photo as evidence and record the final selected-mode image in the manifest as `refined_path`. The compositor must consume the refined image, not the raw photo.

## Output layout

The named `front_center_surrounding_back_right` template is a square white PNG with the following placement:

- top view above the front view;
- left and right views on either side of the front view;
- back view to the far right;
- bottom view below the front view.

The template is intentionally similar to the supplied reference layout while keeping each face separately reusable. The default canvas is 4096×4096 and each standalone view is 2048×2048. A user-supplied layout reference or written arrangement takes precedence over this template.

If fewer than six views are assigned, do not claim a complete six-view set unless the user explicitly enables inference. Use `excluded` for views the user says are unnecessary.

## Delivery note

The user-facing response should name the generated files, identify any inferred view, and state that the result is for product reference only. A separate report file is not required by default; `inspection.json` is an internal or optional diagnostic artifact.
