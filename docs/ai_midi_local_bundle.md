# AI MIDI Local Bundle（全本地离线版）

这个版本不依赖外部在线 API，全部在本地处理。

## 特性
- Python 3.8+
- 命令行一键启动，并自动打开浏览器操作界面
- 上传音频 -> 本地转写 -> 下载 MIDI
- 前端可直接播放转写出的音符（WebAudio 合成播放）
- 优先使用本地增强引擎（basic_pitch），不可用时自动回退 `local_pyin`
- 自动识别硬件信息（CPU/GPU）并反馈到 UI

## 目录
- `ai_midi_local_bundle/backend/main.py`：后端 API 与本地转写流程
- `ai_midi_local_bundle/frontend/index.html`：上传、结果展示、播放、下载
- `ai_midi_local_bundle/run_local.py`：启动后端+前端并自动打开浏览器
- `ai_midi_local_bundle/scripts/start.sh`：Linux/macOS 一键启动
- `ai_midi_local_bundle/windows/start_windows.bat`：Windows 双击一键启动

## 启动
### Linux / macOS
```bash
cd ai_midi_local_bundle
./scripts/start.sh
```

### Windows
双击：
```text
ai_midi_local_bundle\windows\start_windows.bat
```

## API
- `GET /health`：查看服务和硬件状态
- `POST /api/transcribe`：上传音频转写
  - 参数：
    - `engine`: `auto|basic_pitch|local_pyin`
    - `profile`: `clean|balanced|rich`
    - `snap_grid`: 可选，节拍吸附网格（秒）
- `GET /api/result/{job_id}`：下载 MIDI
