@echo off
chcp 65001 >nul

setlocal
set SCRIPT_DIR=%~dp0
set /a loop_count=0

echo Activating conda environment...
call %USERPROFILE%\miniforge3\Scripts\activate.bat gear

:fail
echo ============================= >> "%SCRIPT_DIR%\run.txt"
echo [第 %loop_count% 轮] failed... >> "%SCRIPT_DIR%\run.txt"
echo ============================= >> "%SCRIPT_DIR%\run.txt"
:loop_start
set /a loop_count+=1
echo ============================= >> "%SCRIPT_DIR%\run.txt"
echo [第 %loop_count% 轮] Starting full pipeline... >> "%SCRIPT_DIR%\run.txt"
echo ============================= >> "%SCRIPT_DIR%\run.txt"

cd /d "%SCRIPT_DIR%\Macro"

echo [第 %loop_count% 轮] Step 1: Running test777.py
echo [第 %loop_count% 轮] Step 1: Running test777.py >> "%SCRIPT_DIR%\run.txt"
python test777.py || goto :fail
timeout /t 5 >nul

@REM echo [第 %loop_count% 轮] Step 2: Running test888.py
@REM echo [第 %loop_count% 轮] Step 2: Running test888.py >> "%SCRIPT_DIR%\run.txt"
@REM python test888.py || goto :fail
@REM timeout /t 5 >nul

cd /d "%SCRIPT_DIR%"

echo [第 %loop_count% 轮] Step 3: Running gear_assemble.py
echo [第 %loop_count% 轮] Step 3: Running gear_assemble.py >> "%SCRIPT_DIR%\run.txt"
python gear_assemble.py >> "%SCRIPT_DIR%\run.txt" 2>&1
timeout /t 5 >nul

cd /d "%SCRIPT_DIR%\Macro"

echo [第 %loop_count% 轮] Step 4: Running Auto.py with Abaqus CAE
echo [第 %loop_count% 轮] Step 4: Running Auto.py with Abaqus CAE >> "%SCRIPT_DIR%\run.txt"
start /wait "" cmd /c abaqus cae noGUI=Auto.py >> "%SCRIPT_DIR%\run.txt" 2>&1 || goto :fail

echo Finished Auto.py
echo Finished Auto.py >> "%SCRIPT_DIR%\run.txt"
timeout /t 5 >nul

echo [第 %loop_count% 轮] Step 5: Running extract_vonmises_stress.py
echo [第 %loop_count% 轮] Step 5: Running extract_vonmises_stress.py >> "%SCRIPT_DIR%\run.txt"
start /wait cmd /c "abaqus python extract_vonmises_stress.py >> \"%SCRIPT_DIR%\run.txt\" 2>&1"
timeout /t 5 >nul

cd /d "%SCRIPT_DIR%\gear_step"

echo [第 %loop_count% 轮] Step 6: Running move_step.py >> "%SCRIPT_DIR%\run.txt"
python move_step.py >> "%SCRIPT_DIR%\run.txt" 2>&1
timeout /t 5 >nul

echo ============================= >> "%SCRIPT_DIR%\run.txt"
echo [第 %loop_count% 轮] Loop completed successfully! >> "%SCRIPT_DIR%\run.txt"
echo Press Ctrl+C to stop, or wait 5 seconds to continue... >> "%SCRIPT_DIR%\run.txt"
echo ============================= >> "%SCRIPT_DIR%\run.txt"

timeout /t 5 >nul
goto :loop_start


