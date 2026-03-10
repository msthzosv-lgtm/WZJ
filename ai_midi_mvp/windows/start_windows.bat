@echo off
setlocal
chcp 65001 >nul

cd /d %~dp0\..

if not exist .venv (
  echo [1/4] 创建虚拟环境...
  py -3 -m venv .venv
)

call .venv\Scripts\activate.bat

echo [2/4] 安装依赖...
python -m pip install --upgrade pip
pip install -r backend\requirements.txt

echo [3/4] 可选安装 Basic Pitch（首次推荐）...
echo 如果你没有安装 basic-pitch，转写会报错。
echo 你可以手动执行: pip install basic-pitch==0.3.0

echo [4/4] 启动服务（关闭窗口即停止）...
python run_local.py

endlocal
