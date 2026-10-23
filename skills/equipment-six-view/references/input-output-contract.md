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

## View names

Use these exact filenames and semantic meanings:

| File | Meaning |
| --- | --- |
| `front.png` | Primary operating or presentation face |
| `back.png` | Opposite face |
| `left.png` | Device's left side when facing the front |
| `right.png` | Device's right side when facing the front |
| `top.png` | Upper face |
| `bottom.png` | Lower face |

The normalized view directory should contain one file for each name. PNG is preferred; JPEG and WebP are accepted as input.

## Output layout

The default composite is a square white PNG with the following placement:

- top view above the front view;
- left and right views on either side of the front view;
- back view to the far right;
- bottom view below the front view.

The composite is intentionally similar to the supplied reference layout while keeping each face separately reusable. The default canvas is 4096×4096 and each standalone view is 2048×2048.

## Delivery note

The user-facing response should name the generated files, identify any inferred view, and state that the result is for product reference only. A separate report file is not required by default; `inspection.json` is an internal or optional diagnostic artifact.
