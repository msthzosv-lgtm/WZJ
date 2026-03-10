# AI 扒谱优化方案（准确率提升 + Windows 一键启动）

## 1. 这次优化目标

- 在已有 70%~80% 准确率目标上，继续提升“可用准确率”（听感和可编辑性）。
- 提供**可落地的一键启动**：Windows 下载后双击 `start_windows.bat` 即可启动 GUI 与后端服务。

---

## 2. 准确率进一步优化（可直接实施）

## 2.1 三档转写策略（已在 MVP 接口实现）

- `conservative`（保守）：
  - 过滤短音和低力度噪声音符，减少误检。
  - 适合：你要“干净谱子、少错音”。
- `balanced`（平衡）：
  - 默认策略，兼顾召回和精确。
- `aggressive`（激进）：
  - 保留更多疑似音符，减少漏检。
  - 适合：先尽量抓全，再手动删。

> 本质上是通过阈值调节 Precision/Recall，满足不同编曲场景。

## 2.2 节拍吸附（已在 MVP 接口实现）

- 增加 `snap_grid`（例如 0.125 秒）参数，将 note 的 start/end 对齐节拍网格。
- 作用：减少抖动音符、缩短后期修谱时间。

## 2.3 建议继续加入的两项（下一步）

1. **先分离再转写（Demucs）**
   - 对混音先做人声/伴奏 stem，再对主 stem 调用 Basic Pitch。
   - 对复杂流行歌常有明显收益。

2. **模型路由**
   - 钢琴素材路由到 Onsets & Frames。
   - 单旋律素材路由到 CREPE/pYIN。
   - 混音默认 Basic Pitch + 后处理。

---

## 3. 免费方案怎么选（你关心的）

### 3.1 真正长期免费的可行路线

- **开源模型本地部署（推荐）**：
  - Basic Pitch（主模型）
  - Demucs（分离）
  - librosa/pretty_midi（后处理）
- 优点：调用次数不受限、成本最低、可持续。

### 3.2 在线“免费 API”现实情况

- 长期稳定且高并发的“完全免费 API”基本很少。
- 常见是“试用额度免费”，后续收费。
- 所以产品核心链路建议务必自部署。

---

## 4. Windows 一键启动交付

本仓库新增 `ai_midi_mvp` 最小可运行版本：

- `backend/main.py`：FastAPI 转写服务（Basic Pitch + 后处理）
- `frontend/index.html`：上传音频并下载 MIDI 的图形界面
- `run_local.py`：同时拉起前后端并自动打开浏览器
- `windows/start_windows.bat`：Windows 双击一键启动

### 使用步骤（Windows）

1. 双击 `ai_midi_mvp/windows/start_windows.bat`
2. 首次会自动创建 `.venv` 并安装依赖
3. 浏览器自动打开 GUI 页面
4. 上传音频并导出 MIDI

> 注：首次建议额外安装 `basic-pitch==0.3.0`，否则会提示模型未安装。

---

## 5. 下一版可做成真正“桌面双击即开（无 Python 环境）”

如果你要发给非技术用户，建议下一步打包为：

- `PyInstaller` 打包后端为 exe
- 前端打包进 `Electron`（或 Tauri）
- `Inno Setup` 生成安装包（安装后桌面图标双击打开）

这样可以做到你说的“下载后像普通软件一样双击启动”。
