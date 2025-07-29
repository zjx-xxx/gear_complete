@echo off
call %USERPROFILE%\miniforge3\Scripts\activate.bat gear

cd ./Macro

echo =============================
echo 1. Running test777.py (system Python)
echo =============================
python test777.py
if errorlevel 1 (
    echo test777.py failed.
    pause
    exit /b 1
)


echo =============================
echo 2. Running test888.py (system Python)
echo =============================
python test888.py
if errorlevel 1 (
    echo test888.py failed.
    pause
    exit /b 1
)

cd ..

echo =============================
echo 3. Running gear_assemble.py (system Python)
echo =============================
python gear_assemble.py
if errorlevel 1 (
    echo gear_assemble.py failed.
    pause
    exit /b 1
)

cd ./Macro

echo =============================
echo 4. Running Auto.py with Abaqus CAE (no GUI)
echo =============================
abaqus cae noGUI=Auto.py
if errorlevel 1 (
    echo Auto.py failed.
    pause
    exit /b 1
)

echo =============================
echo 5. Running extract_vonmises_stress.py with Abaqus Python
echo =============================
abaqus python extract_vonmises_stress.py
if errorlevel 1 (
    echo extract_vonmises_stress.py failed.
    pause
    exit /b 1
)
cd ..
cd ./gear_step

echo =============================
echo 6. Running move_step
echo =============================
python move_step.py
if errorlevel 1 (
    echo move_step.py failed.
    pause
    exit /b 1
)

echo =============================
echo All scripts completed successfully!
echo =============================
pause
