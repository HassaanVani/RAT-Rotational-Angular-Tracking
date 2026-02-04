@echo off
echo.
echo ========================================
echo    Building RAT Standalone Executable
echo ========================================
echo.

:: Check if venv exists
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found.
    echo Run install_rat.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo [1/3] Installing PyInstaller...
pip install pyinstaller

echo [2/3] Building executable...
pyinstaller RAT.spec --clean

echo [3/3] Copying assets...
if exist "dist\RAT.exe" (
    copy RAT_LOGO.jpg dist\
    echo.
    echo ========================================
    echo    Build Complete!
    echo ========================================
    echo.
    echo Executable location: dist\RAT.exe
    echo.
    echo You can distribute the dist folder to researchers.
    echo They just double-click RAT.exe to run - no Python needed!
) else (
    echo [ERROR] Build failed. Check errors above.
)

echo.
pause
