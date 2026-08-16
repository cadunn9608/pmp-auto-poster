# ==============================================================================
# STEP 2: GEMINI GENERATES PMP CONTENT (WITH ROBUST MODEL FALLBACK)
# ==============================================================================
def get_daily_pmp_content():
    print("2️⃣ Fetching PMP question and expressive script from Gemini...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = """
    Generate a PMP exam situational question and a lively, highly expressive spoken script for a charismatic 3D animated dog host.
    Use exclamation points, question marks, and natural pauses (using ellipses) so the speech engine sounds dynamic and engaging.
    Output strictly as a valid JSON object with the following keys:
    {
        "topic": "Risk Management",
        "question": "A project team discovers a new risk that could delay the project by two weeks...",
        "option_a": "A) Update the risk register",
        "option_b": "B) Crash the schedule immediately",
        "option_c": "C) Inform the sponsor first",
        "option_d": "D) Perform qualitative risk analysis",
        "correct_answer": "A) Update the risk register",
        "explanation": "The first step when identifying a new risk is to document it in the risk register.",
        "spoken_script": "Alright PMP hopefuls, here is a tricky one! A new risk is discovered that might cause a two-week delay. What is the immediate first action you must take? Option A... update the risk register. Option B... crash the schedule. Option C... inform the sponsor. Or Option D... perform qualitative risk analysis. Think like a Project Manager!"
    }
    """
    
    # --- SYNCHRONIZED ROBUST FALLBACK LIST ---
    # This is the same list used in your static tip script
    models_to_try = [
        "gemini-3.5-flash",       # Top priority (when available)
        "gemini-3.1-flash",       # Recent stable flash
        "gemini-1.5-flash",       # Dependable 1.5 flash
        "gemini-3-flash-preview", # Latest preview
        "gemini-3.6-flash",       # Newest version
        "gemini-1.5-pro",         # Pro fallback (higher capacity, sometimes slower)
        "gemini-3.1-flash-lite"   # Absolute last resort
    ]
    
    last_exception = None
    
    # --- SYNCHRONIZED EXPONENTIAL BACKOFF RETRY LOGIC ---
    # Try the whole list up to 3 times
    for attempt in range(1, 4):
        print(f"--- Starting content generation attempt {attempt}/3 ---")
        for model_name in models_to_try:
            try:
                print(f"Attempting generation with model: {model_name}...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config={"response_mime_type": "application/json"}
                )
                
                raw_text = response.text.strip()
                # Robust JSON cleaning
                if "```json" in raw_text:
                    raw_text = raw_text.split("```json")[1].split("```")[0]
                elif "```" in raw_text:
                    raw_text = raw_text.split("```")[1].split("```")[0]
                
                return json.loads(raw_text.strip()) # Success!
                
            except Exception as e:
                last_exception = e
                print(f"⚠️ Model {model_name} failed: {e}")
                
                # If it's a 503 (Overloaded), wait 10s before trying the NEXT model
                if "503" in str(e):
                    print("Server overloaded (503). Pausing briefly before next model...")
                    time.sleep(10)
                    
                continue # Continue to the next model in the list
        
        # If we completed the full model list and still haven't succeeded,
        # wait significantly longer before starting the next retry attempt (Attempt 2 or 3)
        wait_time = attempt * 15 # Wait 15s, then 30s, then 45s
        print(f"All models failed on attempt {attempt}. Waiting {wait_time} seconds before retrying the list...")
        time.sleep(wait_time)
            
    # If all models fail across all attempts, raise the last error
    raise Exception(f"All models and retries failed. Final error: {last_exception}")
