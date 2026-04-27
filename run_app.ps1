param(
    [string]$VenvDir = ".venv"
)

if (-not (Test-Path "$VenvDir\Scripts\Activate.ps1")) {
    Write-Host "Virtual environment not found. Creating $VenvDir..."
    python -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to create virtual environment. Ensure Python is in PATH."
        Read-Host "Press Enter to exit"
        exit 1
    }
    & "$VenvDir\Scripts\python.exe" -m pip install --upgrade pip
    & "$VenvDir\Scripts\python.exe" -m pip install -r requirements.txt
}

Write-Host "Starting Streamlit app (app.py)..."
& "$VenvDir\Scripts\python.exe" -m streamlit run app.py

Write-Host "Streamlit process exited."
Read-Host "Press Enter to exit"
