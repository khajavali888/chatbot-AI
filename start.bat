@echo off
echo Starting Human-Like Chatbot...
echo Using model: mistral (fastest)

REM Check if Ollama is running
curl -s http://localhost:11434/api/tags > nul 2>&1
if errorlevel 1 (
    echo Ollama is not running. Please start Ollama first.
    echo Starting Ollama in the background...
    start /B ollama serve
    timeout /t 5 /nobreak
)

REM Create data directory if it doesn't exist
if not exist data mkdir data

REM Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Start the chatbot
echo Starting chatbot server...
python app.py

pause