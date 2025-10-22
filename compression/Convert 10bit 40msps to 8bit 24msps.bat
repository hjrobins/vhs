@echo off
setlocal enabledelayedexpansion

REM === Step 1: Activate Conda and set working directory ===
call "C:\ProgramData\anaconda3\Scripts\activate.bat" "C:\ProgramData\anaconda3"
call conda activate vhsdecode
cd /d "C:\Users\Harriet\vhs-decode"

REM === Step 2: Validate input ===
if "%~1"=="" (
    echo [ERROR] No input file provided. Drag an .lds file onto this script.
    pause
    exit /b
)

set "INPUT_LDS=%~1"
set "INPUT_NAME=%~n1"
set "INPUT_DIR=%~dp1"
set "OUTPUT_LDF=%INPUT_DIR%%INPUT_NAME:_10bit40msps=_8bit20msps%.ldf"
set "STAT_PATH=%INPUT_DIR%%INPUT_NAME%_stat.txt"

REM === Step 3: Generate stat.txt with progress bar (if missing) ===
if exist "%STAT_PATH%" (
    echo [SKIP] Stat file already exists: %STAT_PATH%
) else (
    echo [INFO] Generating stat file...
    python vhs_scripts\progress_lds.py "%INPUT_LDS%" --stat
)

REM === Step 4: Run conversion pipeline with progress tracking ===
ld-lds-converter -i "%INPUT_LDS%" | ^
sox -S --multi-threaded -r 40000 -b 16 -c 1 -e signed -t raw - -b 8 -r 20000 -c 1 -t flac "%OUTPUT_LDF%" sinc -n 2500 0-8670 2>&1 | ^
python vhs_scripts\progress_lds.py "%INPUT_LDS%" --progress

REM === Step 5: Final message ===
echo.
echo [DONE] Conversion complete: %OUTPUT_LDF%
pause
endlocal
