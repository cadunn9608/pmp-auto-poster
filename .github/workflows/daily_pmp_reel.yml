name: Daily PMP Reel Automation (100% Free)

on:
  schedule:
    - cron: '0 12 * * *'
  workflow_dispatch:

jobs:
  generate-reel:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install System Dependencies
        run: |
          export DEBIAN_FRONTEND=noninteractive
          sudo apt-get update -qq
          sudo apt-get install -y -qq ffmpeg imagemagick
          sudo sed -i 's/none/read,write/g' /etc/ImageMagick-6/policy.xml || true

      - name: Clone Open-Source Wav2Lip & Download Weights
        run: |
          git clone https://github.com/Rudrabha/Wav2Lip.git
          mkdir -p Wav2Lip/checkpoints
          wget -q https://github.com/Rudrabha/Wav2Lip/releases/download/v1.0/wav2lip_gan.pth -O Wav2Lip/checkpoints/wav2lip_gan.pth

      - name: Install Python Packages
        run: |
          python -m pip install --upgrade pip
          pip install google-genai gtts moviepy requests torch torchvision librosa opencv-python

      - name: Run Script
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          FB_PAGE_ID: ${{ secrets.FB_PAGE_ID }}
          FB_ACCESS_TOKEN: ${{ secrets.FB_ACCESS_TOKEN }}
        run: |
          python generate_pmp_reel.py

      - name: Upload Artifact
        uses: actions/upload-artifact@v4
        with:
          name: daily-pmp-reel
          path: daily_pmp_reel.mp4
          retention-days: 7
