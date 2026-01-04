@echo off
echo Clearing Python cache files...

REM Delete all __pycache__ directories
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

REM Delete all .pyc files
del /s /q *.pyc 2>nul

REM Delete all .pyo files
del /s /q *.pyo 2>nul

echo Done! All Python cache files cleared.
echo Please restart the game now.
pause
