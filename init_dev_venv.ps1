#Enable script execution if not already enabled on your system (Copy the command): 
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Stop script immediately on any error
$ErrorActionPreference = 'Stop'
$VENV_NAME = ".aurora_tts_venv"
$PYTHON_VERSION = "-3.12"

try {
    # Setup python venv
    Write-Host "======== Creating python virtual environment ========" -ForegroundColor Cyan
    py $PYTHON_VERSION -m venv $VENV_NAME
    if ($LASTEXITCODE -ne 0) { throw "Failed to create virtual environment." }

    & ".\$VENV_NAME\Scripts\Activate.ps1"
    if ($LASTEXITCODE -ne 0) { throw "Failed to activate virtual environment." }
    
    Write-Host "Virtual environment created and activated successfully!" -ForegroundColor Green

    # Install project dependencies
    Write-Host "======== Installing dependencies ========" -ForegroundColor Cyan
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw "Failed to install requirements" }

    Write-Host "Installed project dependencies successfully!" -ForegroundColor Green
}
catch {
    Write-Host "Environment setup failed!" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}