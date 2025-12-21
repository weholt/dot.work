@echo off
REM Install zipparu globally using uv if not already installed
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo Installing uv...
    pip install uv
)

echo Installing zipparu as a uv tool...
uv tool install .

echo Adding Explorer context menu...
for /f "usebackq tokens=*" %%H in (`python -c "import sys; print(sys.executable)"`) do set PYTHON_PATH=%%H
for /f "usebackq tokens=*" %%P in (`uv tool path zipparu`) do set ZIPP_PATH=%%P

reg add "HKCR\Directory\Background\shell\Zipparu Upload" /t REG_SZ /v "" /d "Upload folder via Zipparu" /f
reg add "HKCR\Directory\Background\shell\Zipparu Upload\command" /t REG_SZ /v "" /d "\"%ZIPP_PATH%\" \"%%V\"" /f

echo Zipparu installed and integrated.
pause