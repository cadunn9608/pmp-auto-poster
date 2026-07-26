name: Daily PMP Reel Automation

on:
  schedule:
    - cron: '0 8 * * *'
  workflow_dispatch:

jobs:
  generate-reel:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'

    - name: Install system dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y ffmpeg libmagickwand-dev

    - name: Install Python dependencies
      run: |
        python -m pip install --upgrade pip
        pip install google-generativeai moviepy

    - name: Run Reel Generator Script
      env:
        GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
      run: |
        python daily_reel_generator.py

    - name: Upload generated video artifact
      uses: actions/upload-artifact@v4
      with:
        name: daily-pmp-reel
        path: daily_pmp_reel.mp4
