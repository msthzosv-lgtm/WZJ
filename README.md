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

## AI 扒谱相关文档
- `docs/ai_transcription_design.md`
- `docs/ai_transcription_optimization_and_oneclick.md`
- `docs/ai_midi_local_bundle.md`（全本地离线版说明）

## 全本地离线版（推荐下载目录）

新增 `ai_midi_local_bundle/`：
- 不使用外部 API，优先本地开源引擎
- 支持 Python 3.8+
- 一键启动并自动打开浏览器
- 上传音频后本地处理，输出 MIDI，可在页面播放与下载

### Linux/macOS
```bash
cd ai_midi_local_bundle
./scripts/start.sh
```

### Windows
双击：
```text
ai_midi_local_bundle\windows\start_windows.bat
```
