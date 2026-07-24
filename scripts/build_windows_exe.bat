@echo off
chcp 65001 >nul
echo ========================================================
echo        🚀 JobHunter Windows .EXE 自动构建与打包脚本
echo ========================================================
echo.

cd /d %~dp0\..

echo 📦 正在检查并安装打包依赖 PyInstaller...
python -m pip install pyinstaller requests beautifulsoup4 fastapi uvicorn pydantic jinja2

echo.
echo ⚙️ 正在编译打包 JobHunter 单文件可执行程序 (.exe)...
pyinstaller --clean jobhunter.spec

echo.
if exist "dist\JobHunter.exe" (
    echo ========================================================
    echo  ✅ 打包成功！EXE 可执行文件位置:
    echo  📍 dist\JobHunter.exe
    echo ========================================================
    echo.
    echo 双击 dist\JobHunter.exe 即可直接自动唤起本地 Edge/Chrome 浏览器使用！
) else (
    echo ❌ 打包失败，请检查控制台错误日志。
)

pause
