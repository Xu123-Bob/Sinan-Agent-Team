@echo off
setlocal

echo ========================================================
echo          司南 (Sinan) 安装助手
echo ========================================================
echo.

:: 1. 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 未找到 python，请先安装 Python 3.10~3.12
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo 检测到 Python %PYVER%

:: 2. 询问 venv
set /p USE_VENV=是否创建虚拟环境？(推荐 y/n):
if /i "%USE_VENV%"=="y" (
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo [OK] 已激活 venv
)

:: 3. 安装
echo 正在安装司南...
python -m pip install --upgrade pip
python -m pip install -e .

:: 4. 验证
echo.
echo 验证安装...
python -m agent.doctor

echo.
echo [OK] 安装完成！
echo   启动: sinan  或  python -m agent
endlocal