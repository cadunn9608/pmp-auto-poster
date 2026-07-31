def get_daily_pmp_question():
    prompt = "Your prompt here for generating the PMP question..."
    
    models_to_try = [
        "gemini-3.5-flash",
        "gemini-3.1-flash",
        "gemini-3.6-flash",
        "gemini-3-flash-preview",
        "gemini-3.1-flash-lite"
    ]
    
    response = None
    for model_name in models_to_try:
        print(f"Attempting PMP content generation using model: {model_name}")
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            if response and response.text:
                print(f"Successfully generated PMP content using {model_name}!")
                break
        except Exception as e:
            print(f"Model {model_name} failed with error: {e}. Trying next...")
            time.sleep(3)
            
    if not response or not response.text:
        raise Exception("All models failed to generate PMP content.")
        
    return response.text
