name: Daily PMP Reel Automation

on:
  schedule:
    - cron: '0 12 * * *' # Runs automatically every day at 12:00 PM UTC
  workflow_dispatch:      # Allows manual trigger anytime from the GitHub Actions tab

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
          cache: 'pip'

      - name: Install System Dependencies (ImageMagick)
        run: |
          export DEBIAN_FRONTEND=noninteractive
          sudo apt-get update -qq
          sudo apt-get install -y -qq imagemagick
          sudo sed -i 's/none/read,write/g' /etc/ImageMagick-6/policy.xml || true

      - name: Install Python Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install google-genai moviepy requests

      - name: Run Daily PMP Reel Script
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          FB_PAGE_ID: ${{ secrets.FB_PAGE_ID }}
          FB_ACCESS_TOKEN: ${{ secrets.FB_ACCESS_TOKEN }}
        run: |
          python generate_pmp_reel.py

      - name: Upload Generated Reel Artifact
        uses: actions/upload-artifact@v4
        with:
          name: daily-pmp-reel
          path: daily_pmp_reel.mp4
          retention-days: 7
