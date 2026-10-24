# Equipment Six-View Composer

## 中文版

`equipment-six-view` 是一个 Codex skill，用于根据设备照片或候选视图图像，生成一致的设备六视图参考图。

该 skill 将“图片对应哪个视图”和“组合图如何排版”分开处理。用户可以按照任意顺序上传图片，也可以明确指定“图1=正面图”等映射。参考图只用于确定排列、间距和展示方式，不会把参考设备的实体细节添加到用户设备上。

### 功能

- 支持正面、背面、左侧、右侧、俯视和底视图；
- 不要求用户按照视图顺序上传图片；
- 用户明确指定图号映射后，优先遵循用户映射；
- 左右两侧相同时，支持通过 `same_as` 使用同一张已确认图片；
- 支持自定义组合版式，例如正面图居中、上下左右视图环绕、背面图放在最右侧；
- 通过 `manifest.json` 固化图像映射、排版、旋转和证据状态；
- 强制执行抠图精修：去除手、房间、地面和杂物，修复边缘后才能进入组合；
- 处理前强制询问美化等级：`none`（无美化，仅抠图）或 `smart`（智能美化，清理气泡、倒影、灰尘和拍摄瑕疵）；
- 智能美化会保留真实结构、接口、按钮、文字和真实损伤，不会擅自重绘产品；
- 缺失视图默认不会被推断，只有用户明确允许时才启用推断；
- 不会用错误图片替换缺失或被拒绝的视图；
- 包含基于 Pillow 的归一化、manifest 校验、组合和检查脚本。

原始照片不会直接进入组合器。请先使用可用的图像编辑能力生成干净的透明或白底 cutout，并在 manifest 中填写 `cleanup_status=approved`、`cleanup_method` 和 `refined_path`。具体要求见 [cutout-refinement.md](skills/equipment-six-view/references/cutout-refinement.md)。

收到新图片后，skill 的第一步必须先询问：

> A. 无美化：仅抠图、去背景、修复边缘，保留产品原始状态；
> B. 智能美化：在抠图基础上，清理屏幕膜气泡、倒影、灰尘、指纹和拍摄瑕疵，并适度统一观感。

模式会记录在 manifest 的 `beautify_mode` 字段中，未选择模式不能进入组合。

### 目录结构

```text
equipment-six-view/
├─ plugin.json
├─ .codex-plugin/plugin.json
├─ skills/equipment-six-view/
│  ├─ SKILL.md
│  ├─ agents/openai.yaml
│  ├─ references/
│  └─ scripts/
├─ requirements.txt
├─ LICENSE
└─ README.md
```

### 从 GitHub 安装

使用 Codex 的 skill 安装脚本，并指定仓库中的 skill 目录：

```powershell
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
python (Join-Path $codexHome "skills\.system\skill-installer\scripts\install-skill-from-github.py") `
  --url https://github.com/ike10969/equipment-six-view/tree/v1.3.1/skills/equipment-six-view
```

### 依赖安装

图片处理脚本依赖 Pillow：

```powershell
python -m pip install -r requirements.txt
```

可以在 `skills/equipment-six-view/` 目录中运行脚本，也可以传入绝对路径：

```powershell
python scripts/normalize_views.py --input-dir <raw-views> --output-dir <normalized-views>
python scripts/validate_manifest.py --manifest <manifest.json>
python scripts/compose_from_manifest.py --manifest <manifest.json> --output-dir <deliverables>
python scripts/inspect_result.py --input-dir <deliverables> --output-json <deliverables>\inspection.json
```

如果只是完整六视图的旧式固定排版，可以使用 `compose_six_views.py`；只要用户指定了图号映射、排除视图、左右复用或自定义排版，就应使用 manifest 驱动的脚本。

manifest 结构和 `front_center_surrounding_back_right` 排版模板见 [manifest-schema.md](skills/equipment-six-view/references/manifest-schema.md)。

### 使用示例

```text
使用 equipment-six-view skill。
图片上传顺序不代表视图顺序。
图1是正面图。
图2是背面图。
图3同时作为左侧图和右侧图。
图4是俯视图。
图5是底视图。
组合时，正面图放在中央，俯视图放在上方，底视图放在下方，左右侧图放在两侧，背面图放在最右侧。
```

### 开源协议

本项目采用 MIT 协议，详见 [LICENSE](LICENSE)。

## English

`equipment-six-view` is a Codex skill for creating consistent equipment six-view reference images from device photos or candidate view images.

The skill keeps source mapping and composite layout separate. Users may upload images in any order and explicitly assign mappings such as `image 1 = front`. A layout reference controls placement and presentation only; it does not add physical details to the device.

## Features

- Supports front, back, left, right, top, and bottom views.
- Accepts source images in arbitrary upload order.
- Honors explicit user mappings before visual inference.
- Supports identical left and right sides through `same_as` mapping.
- Supports custom composite layouts, including a centered front view with surrounding side views and the back view on the far right.
- Uses a manifest to make source mapping, evidence status, rotation, and layout executable and reviewable.
- Requires an explicit `none` or `smart` beautification choice before processing.
- Requires every raw photo to pass cutout refinement and approval before composition.
- In `smart` mode, performs conservative product retouching for screen-protector bubbles, reflections, dust, fingerprints, and capture defects.
- Requires explicit permission before inferring a missing view.
- Prevents rejected or missing views from being silently replaced by another view.
- Includes Pillow-based normalization, manifest validation, composition, and inspection scripts.

## Package layout

```text
equipment-six-view/
├─ plugin.json
├─ .codex-plugin/plugin.json
├─ skills/equipment-six-view/
│  ├─ SKILL.md
│  ├─ agents/openai.yaml
│  ├─ references/
│  └─ scripts/
├─ requirements.txt
├─ LICENSE
└─ README.md
```

## Install from GitHub

Use the Codex skill installer with the skill directory inside this repository:

```powershell
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
python (Join-Path $codexHome "skills\.system\skill-installer\scripts\install-skill-from-github.py") `
  --url https://github.com/ike10969/equipment-six-view/tree/v1.3.1/skills/equipment-six-view
```

## Requirements

The deterministic helper scripts use Pillow:

```powershell
python -m pip install -r requirements.txt
```

Run the scripts from `skills/equipment-six-view/` or pass absolute paths:

```powershell
python scripts/normalize_views.py --input-dir <raw-views> --output-dir <normalized-views>
python scripts/validate_manifest.py --manifest <manifest.json>
python scripts/compose_from_manifest.py --manifest <manifest.json> --output-dir <deliverables>
python scripts/inspect_result.py --input-dir <deliverables> --output-json <deliverables>\inspection.json
```

Use `compose_six_views.py` only for legacy fixed-layout work. For explicit mapping, excluded views, `same_as`, or custom reference layouts, use `validate_manifest.py` and `compose_from_manifest.py`.

## Usage example

```text
Use the equipment-six-view skill.
The upload order is arbitrary.
Image 1 is the front view.
Image 2 is the back view.
Image 3 is used for both left and right sides.
Image 4 is the top view.
Image 5 is the bottom view.
Arrange the front view in the center, place the top and bottom views above and below it, place the left and right views on both sides, and place the back view on the far right.
```

## License

MIT. See [LICENSE](LICENSE).
