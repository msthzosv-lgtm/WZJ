@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

cd /d %~dp0\..
set "ROOT=%CD%"
set "LOG_DIR=%ROOT%\logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set "LOG_FILE=%LOG_DIR%\startup.log"

echo ==== AI MIDI MVP Startup ==== > "%LOG_FILE%"
echo [%DATE% %TIME%] ROOT=%ROOT% >> "%LOG_FILE%"

set "PY_CMD="
where py >nul 2>nul
if %errorlevel%==0 set "PY_CMD=py -3"
if not defined PY_CMD (
  where python >nul 2>nul
  if %errorlevel%==0 set "PY_CMD=python"
)
if not defined PY_CMD (
  echo [ERROR] 未找到 Python 3.8+。
  pause
  exit /b 1
)

%PY_CMD% -c "import sys; print(sys.version); import sys as _s; _s.exit(0 if _s.version_info[:2] >= (3,8) else 1)" >> "%LOG_FILE%" 2>&1
if %errorlevel% neq 0 (
  echo [ERROR] Python 版本不足，需要 3.8+
  pause
  exit /b 1
)

if not exist .venv (
  %PY_CMD% -m venv .venv >> "%LOG_FILE%" 2>&1
  if %errorlevel% neq 0 (
    echo [ERROR] 创建虚拟环境失败，查看: %LOG_FILE%
    pause
    exit /b 1
  )
)

call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
  echo [ERROR] 激活虚拟环境失败。
  pause
  exit /b 1
)

python -m pip install --upgrade pip >> "%LOG_FILE%" 2>&1
pip install -r backend\requirements.txt >> "%LOG_FILE%" 2>&1
if %errorlevel% neq 0 (
  echo [ERROR] 安装依赖失败，请看日志: %LOG_FILE%
  pause
  exit /b 1
)

python run_local.py >> "%LOG_FILE%" 2>&1
set "APP_EXIT=%errorlevel%"
if not "%APP_EXIT%"=="0" (
  echo [ERROR] 运行失败，退出码: %APP_EXIT%
  echo [INFO] 日志路径: %LOG_FILE%
  pause
  exit /b %APP_EXIT%
)

endlocal
exit /b 0
