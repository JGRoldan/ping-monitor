@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "VENV_DIR=.venv"

if not exist "%VENV_DIR%\Scripts\activate.bat" (
  echo Virtual environment not found. Creating %VENV_DIR%...
  python -m venv "%VENV_DIR%" || (
    echo Failed to create virtual environment. Ensure Python is in PATH.
    pause
    exit /b 1
  )
  echo Installing dependencies from requirements.txt...
  "%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip
  "%VENV_DIR%\Scripts\python.exe" -m pip install -r requirements.txt
)

call "%VENV_DIR%\Scripts\activate.bat"

echo Starting Streamlit app (app.py)...
"%VENV_DIR%\Scripts\python.exe" -m streamlit run app.py

echo Streamlit process exited.
pause
