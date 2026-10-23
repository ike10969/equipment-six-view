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
- 不会用错误图片替换缺失或被拒绝的视图；
- 包含基于 Pillow 的图片归一化、组合和检查脚本。

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
python <CODEX_HOME>\skills\.system\skill-installer\scripts\install-skill-from-github.py `
  --url https://github.com/ike10969/equipment-six-view/tree/v1.0.0/skills/equipment-six-view
```

### 依赖安装

图片处理脚本依赖 Pillow：

```powershell
python -m pip install -r requirements.txt
```

可以在 `skills/equipment-six-view/` 目录中运行脚本，也可以传入绝对路径：

```powershell
python scripts/normalize_views.py --input-dir <raw-views> --output-dir <normalized-views>
python scripts/compose_six_views.py --input-dir <normalized-views> --output-dir <deliverables>
python scripts/inspect_result.py --input-dir <deliverables> --output-json <deliverables>\inspection.json
```

当六个标准视图都存在并且固定版式符合用户要求时，使用 `compose_six_views.py`。如果用户提供了自定义参考排版，应使用基于映射清单的组合脚本，并严格保持用户指定的图像映射。

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
- Prevents rejected or missing views from being silently replaced by another view.
- Includes Pillow-based normalization, composition, and inspection scripts.

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
python <CODEX_HOME>\skills\.system\skill-installer\scripts\install-skill-from-github.py `
  --url https://github.com/ike10969/equipment-six-view/tree/v1.0.0/skills/equipment-six-view
```

## Requirements

The deterministic helper scripts use Pillow:

```powershell
python -m pip install -r requirements.txt
```

Run the scripts from `skills/equipment-six-view/` or pass absolute paths:

```powershell
python scripts/normalize_views.py --input-dir <raw-views> --output-dir <normalized-views>
python scripts/compose_six_views.py --input-dir <normalized-views> --output-dir <deliverables>
python scripts/inspect_result.py --input-dir <deliverables> --output-json <deliverables>\inspection.json
```

`compose_six_views.py` is intended for a complete six-view set when its fixed layout matches the request. For a custom reference layout, use a manifest-driven composition script and preserve the user's explicit mapping.

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
