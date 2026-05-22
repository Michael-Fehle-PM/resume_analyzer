#!/bin/bash

echo ""
echo " Resume Analyser"
echo " ---------------"
echo ""

# Check .env exists
if [ ! -f .env ]; then
    echo " ERROR: .env file not found."
    echo " Copy .env.example to .env and add your Anthropic API key."
    echo ""
    exit 1
fi

# Activate virtual environment
if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
else
    echo " ERROR: Virtual environment not found."
    echo " Run: python -m venv .venv"
    echo " Then: pip install -r requirements.txt"
    echo ""
    exit 1
fi

echo " Starting server..."
echo " Open http://localhost:8000 in your browser"
echo " Press Ctrl+C to stop"
echo ""

uvicorn main:app --reload
