# 俄罗斯方块（网页版）

这是一个可直接在网页中运行的俄罗斯方块小游戏。

## 运行方式

### 方式 1：直接双击
直接用浏览器打开 `index.html` 即可。

### 方式 2：本地静态服务（推荐）
```bash
python3 -m http.server 8000
```
然后访问：`http://127.0.0.1:8000/index.html`

## 操作说明
- `←` / `→`：左右移动
- `↓`：加速下落
- `↑`：旋转
- `空格`：一键到底
- `P`：暂停/继续

同时提供了页面按钮，可在触屏设备上操作。

## AI 扒谱软件设计方案

- 基础设计文档：`docs/ai_transcription_design.md`
- 优化与一键启动方案：`docs/ai_transcription_optimization_and_oneclick.md`

## AI 扒谱 MVP（一键启动原型）

新增 `ai_midi_mvp/` 目录，包含一个可运行的音频转 MIDI 原型：

- 后端：FastAPI + Basic Pitch + MIDI 后处理
- 前端：上传音频、选择策略、下载 MIDI
- Windows：双击 `ai_midi_mvp/windows/start_windows.bat` 启动

### 本地运行（Linux/macOS）
```bash
cd ai_midi_mvp
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
# 可选但推荐（真实转写所需）
pip install basic-pitch==0.3.0
python run_local.py
```
