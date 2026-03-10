@echo off
setlocal
chcp 65001 >nul
cd /d %~dp0\..

where py >nul 2>nul
if %errorlevel% neq 0 (
  echo [ERROR] 未找到 py 启动器，请安装 Python 3.8+
  exit /b 1
)

py -3 - <<PYCODE
import sys
assert sys.version_info >= (3,8), f"Python >=3.8 required, got {sys.version}"
print("Python version OK:", sys.version.split()[0])
PYCODE
if %errorlevel% neq 0 exit /b 1

if not exist .venv (
  echo [1/4] 创建虚拟环境...
  py -3 -m venv .venv
)

call .venv\Scripts\activate.bat

echo [2/4] 安装依赖...
python -m pip install --upgrade pip
pip install -r backend\requirements.txt

echo [3/4] 可选安装增强引擎（本地）...
echo 如需更高准确率，可执行:
echo   pip install basic-pitch==0.3.0
echo   pip install demucs==4.0.1

echo [4/4] 启动（自动弹出浏览器）...
python run_local.py

endlocal
