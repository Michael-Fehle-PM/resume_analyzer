@echo off
echo.
echo  Resume Analyser
echo  ---------------
echo.

:: Check .env exists
if not exist .env (
    echo  ERROR: .env file not found.
    echo  Copy .env.example to .env and add your Anthropic API key.
    echo.
    pause
    exit /b 1
)

:: Activate virtual environment
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else (
    echo  ERROR: Virtual environment not found.
    echo  Run: python -m venv .venv
    echo  Then: pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo  Starting server...
echo  Open http://localhost:8000 in your browser
echo  Press Ctrl+C to stop
echo.

uvicorn main:app --reload
