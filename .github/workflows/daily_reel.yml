name: Daily PMP Reel Automation

on:
  schedule:
    - cron: '0 12 * * *' # Runs daily at 12:00 PM UTC
  workflow_dispatch: # Allows manual trigger from GitHub Actions tab

jobs:
  build-and-post:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install google-genai moviepy requests

      - name: Run Reel Generator Script
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          FB_PAGE_ID: ${{ secrets.FACEBOOK_PAGE_ID }}
          FB_ACCESS_TOKEN: ${{ secrets.FACEBOOK_ACCESS_TOKEN }}
          FB_APP_ID: ${{ secrets.FACEBOOK_APP_ID }}
          FB_APP_SECRET: ${{ secrets.FACEBOOK_APP_SECRET }}
        run: |
          python daily_reel_generator.py

      - name: Upload Video Artifact (Backup)
        uses: actions/upload-artifact@v4
        with:
          name: daily-pmp-reel
          path: daily_pmp_reel.mp4
