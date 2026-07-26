def post_reel_to_facebook(video_path, caption_text):
    """Automatically publishes an official Facebook Reel using proper binary file streaming."""
    page_id = os.environ.get("FB_PAGE_ID")
    access_token = get_long_lived_token()
    
    if not page_id or not access_token:
        print("[DEBUG ERROR] Facebook credentials are missing. Page ID or Access Token not found.")
        return

    url = f"https://graph.facebook.com/v19.0/{page_id}/video_reels"
    
    try:
        # Step 1: Initialize the Reel container
        print(f"[DEBUG] Initializing Facebook Reel container for Page ID: {page_id}...")
        init_payload = {
            "upload_phase": "start",
            "access_token": access_token
        }
        init_response = requests.post(url, data=init_payload)
        print(f"[DEBUG] Init HTTP Status Code: {init_response.status_code}")
        print(f"[DEBUG] Init Raw Response: {init_response.text}")
        
        init_data = init_response.json()
        if "video_id" not in init_data:
            print("[DEBUG ERROR] 'video_id' missing from Meta init response.")
            return
            
        video_id = init_data["video_id"]
        upload_url = init_data["upload_url"]
        
        # Step 2: Stream the local video file binary directly to Meta's upload URL
        print(f"[DEBUG] Container created successfully (ID: {video_id}). Streaming local video binary...")
        with open(video_path, "rb") as video_file:
            # Note: Do NOT use the 'file_url' header here; stream the file directly via 'files' parameter
            files = {"source": video_file}
            upload_response = requests.post(upload_url, files=files)
            
        print(f"[DEBUG] Binary Upload HTTP Status Code: {upload_response.status_code}")
        print(f"[DEBUG] Binary Upload Response Text: {upload_response.text}")
        
        if upload_response.status_code != 200:
            print("[DEBUG ERROR] Binary upload failed.")
            return

        print("[DEBUG] Video binary uploaded successfully. Waiting 20 seconds for Meta processing...")
        time.sleep(20)

        # Step 3: Publish the container
        print("[DEBUG] Publishing Reel container...")
        publish_payload = {
            "upload_phase": "finish",
            "video_id": video_id,
            "video_state": "PUBLISHED",
            "description": caption_text,
            "access_token": access_token
        }
        publish_response = requests.post(url, data=publish_payload)
        print(f"[DEBUG] Publish HTTP Status Code: {publish_response.status_code}")
        print(f"[DEBUG] Publish Raw Response: {publish_response.text}")

    except Exception as e:
        print(f"[DEBUG EXCEPTION] Exception occurred during Facebook upload: {str(e)}")
