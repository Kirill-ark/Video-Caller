#!/bin/bash
set -e

echo "==> Installing PortAudio..."
brew install portaudio

echo "==> Installing Python dependencies..."
pip install -r requirements.txt

echo "==> Done! Run with: python3 main.py"
