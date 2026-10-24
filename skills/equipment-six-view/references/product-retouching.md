# Product retouching modes

This reference defines the user's explicit choice after image intake. The choice applies to the whole device set and must be recorded as `beautify_mode` in the manifest.

## Mode `none`

Use when the user selects “无美化” or asks to preserve the original condition.

- Remove the background, hands, unrelated objects, and unwanted photographic shadow.
- Repair the silhouette mask and transparent/white edge artifacts.
- Preserve screen bubbles, reflections, dust, fingerprints, scratches, wear, exposure variation, and other visible product condition.
- Do not smooth, repaint, deglare, clean, recolor, or cosmetically improve the device.
- Set direct views to `retouch_status: not_requested` and `retouch_method: none`.

This mode is still a product cutout workflow. A raw photograph must not be placed directly into the composite.

## Mode `smart`

Use when the user selects “智能美化” or asks for product-image cleanup.

After the cutout pass, apply conservative presentation retouching:

- remove screen-protector bubbles, adhesive haze, fingerprints, dust spots, and temporary smudges;
- reduce accidental glare and strong screen reflections while preserving real display content and intentional indicators;
- reduce sensor noise and obvious capture artifacts;
- balance exposure and white balance across views without changing the real product color or material;
- clean minor cosmetic distractions only when they are clearly capture artifacts.

Do not:

- change the silhouette, proportions, ports, buttons, seams, vents, labels, screws, or logos;
- invent screen content, hidden geometry, text, or components;
- erase genuine cracks, dents, scratches, wear, warning labels, or other real damage without explicit user approval;
- make the display blank, active, glossy, or matte beyond the evidence;
- use a different beautification intensity for different views of the same device.

If a mark could be either a real defect or a capture artifact, preserve it and set `retouch_status: needs_review` rather than guessing.

## Prompt block

For image-editing or image-generation tools, use the following mode-specific instruction after the device and view mapping are established:

```text
Keep the exact device identity, geometry, proportions, ports, buttons, seams, vents, labels, logos, screws, and observed screen content.
Apply the selected product-image mode exactly:
- none: isolate the device and repair only the mask and background; preserve all visible product condition and photographic defects.
- smart: isolate the device, then conservatively remove temporary screen/surface defects such as protector bubbles, adhesive haze, fingerprints, dust, accidental glare, strong reflections, and capture smudges; keep real wear and damage unless explicitly authorized.
Do not invent hidden geometry, text, components, or screen content. Return the same view orientation on a clean transparent or white background.
```

## Manifest fields

Smart mode example:

```json
{
  "beautify_mode": "smart",
  "retouch_status": "approved",
  "retouch_method": "ai_retouch",
  "refined_path": "refined/front.png"
}
```

None mode example:

```json
{
  "beautify_mode": "none",
  "retouch_status": "not_requested",
  "retouch_method": "none",
  "refined_path": "refined/front.png"
}
```
