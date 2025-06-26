#!/bin/bash

# Path ke folder proyek dan venv
PROJECT_DIR="/Users/h-laptop-336/Documents/app/crypto-bot"
VENV_DIR="$PROJECT_DIR/venv"

# Aktifkan virtual environment
source "$VENV_DIR/bin/activate"

# Jalankan bot
python "$PROJECT_DIR/main.py"
