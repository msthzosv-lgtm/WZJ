@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

cd /d %~dp0\..
set "ROOT=%CD%"
set "LOG_DIR=%ROOT%\logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set "LOG_FILE=%LOG_DIR%\startup.log"

echo ==== AI MIDI Local Bundle Startup ==== > "%LOG_FILE%"
echo [%DATE% %TIME%] ROOT=%ROOT% >> "%LOG_FILE%"

echo [INFO] 工作目录: %ROOT%

REM 1) 找 Python（优先 py，其次 python）
set "PY_CMD="
where py >nul 2>nul
if %errorlevel%==0 set "PY_CMD=py -3"
if not defined PY_CMD (
  where python >nul 2>nul
  if %errorlevel%==0 set "PY_CMD=python"
)
if not defined PY_CMD (
  echo [ERROR] 未找到 Python。请安装 Python 3.8+ 并勾选 Add to PATH。
  echo [ERROR] Python not found. >> "%LOG_FILE%"
  pause
  exit /b 1
)

echo [INFO] 使用解释器: %PY_CMD%

REM 2) Python 版本检查（不要用 heredoc，Windows bat 不支持）
%PY_CMD% -c "import sys; print('Python version:', sys.version.split()[0]); import sys as _s; _s.exit(0 if _s.version_info[:2] >= (3,8) else 1)" >> "%LOG_FILE%" 2>&1
if %errorlevel% neq 0 (
  echo [ERROR] 需要 Python 3.8 及以上。
  echo [ERROR] Python version check failed. >> "%LOG_FILE%"
  pause
  exit /b 1
)

REM 3) 创建虚拟环境
if not exist .venv (
  echo [1/5] 创建虚拟环境...
  %PY_CMD% -m venv .venv >> "%LOG_FILE%" 2>&1
  if %errorlevel% neq 0 (
    echo [ERROR] 创建虚拟环境失败，请查看日志: %LOG_FILE%
    pause
    exit /b 1
  )
)

REM 4) 激活环境
if not exist .venv\Scripts\activate.bat (
  echo [ERROR] 虚拟环境激活脚本不存在。
  echo [ERROR] Missing .venv\Scripts\activate.bat >> "%LOG_FILE%"
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
  echo [ERROR] 激活虚拟环境失败。
  echo [ERROR] venv activation failed. >> "%LOG_FILE%"
  pause
  exit /b 1
)

REM 5) 安装依赖（如果网络问题会保留窗口，不闪退）
echo [2/5] 升级 pip...
python -m pip install --upgrade pip >> "%LOG_FILE%" 2>&1
if %errorlevel% neq 0 (
  echo [WARN] pip 升级失败，继续尝试安装依赖。
)

echo [3/5] 安装核心依赖...
pip install -r backend\requirements.txt >> "%LOG_FILE%" 2>&1
if %errorlevel% neq 0 (
  echo [ERROR] 依赖安装失败，请查看日志: %LOG_FILE%
  echo [TIP] 你可手动执行: pip install -r backend\requirements.txt
  pause
  exit /b 1
)

echo [4/5] 可选增强引擎（按需手动安装）
echo        pip install basic-pitch==0.3.0
echo        pip install demucs==4.0.1

echo [5/5] 启动服务（将自动打开浏览器）...
python run_local.py >> "%LOG_FILE%" 2>&1
set "APP_EXIT=%errorlevel%"

if not "%APP_EXIT%"=="0" (
  echo [ERROR] 程序异常退出，退出码: %APP_EXIT%
  echo [ERROR] run_local.py exited with %APP_EXIT% >> "%LOG_FILE%"
  echo [INFO] 请把日志发给我: %LOG_FILE%
  pause
  exit /b %APP_EXIT%
)

echo [INFO] 程序已正常退出。
endlocal
exit /b 0
