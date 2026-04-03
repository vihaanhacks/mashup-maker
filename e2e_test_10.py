import sys
sys.path.append('.')
from app import app
import json
import time
import traceback

def run_e2e_test():
    print("Starting E2E 10-Song API Test...")
    
    # We will use 10 short YouTube links
    # Mixing between a few known shorts to ensure yt-dlp succeeds quickly
    songs = []
    links = [
        "https://youtube.com/shorts/jfKfPfyJRdk",
        "https://www.youtube.com/watch?v=5Eqb_-j3FDA",
        "https://youtube.com/shorts/jfKfPfyJRdk"
    ]
    
    for i in range(10):
        songs.append({
            "link": links[i % len(links)],
            "startTime": "0:00",
            "endTime": "0:05",  # Just 5 seconds each to speed up yt-dlp and rendering
            "adjustments": {
                "gain": 100,
                "pan": 0,
                "full": False,
                "speed": 100
            }
        })

    payload = {
        "ai_mode": True,
        "removeEffects": False,
        "vibe": "ocean_mist",
        "songs": songs,
        "audioAdjustments": {
            "bass": 0, "mid": 0, "treble": 0, "speed": 1.0, 
            "pitch": 0, "reverb": 0, "delay": 0, "chorus": 0, 
            "phaser": 0, "distortion": 0, "bitcrush": 0, "tremolo": 0, 
            "flanger": 0, "compression": 0, "limiter": 100, "width": 100, 
            "fade_in": 500, "fade_out": 500, "highpass": 0, "lowpass": 100
        },
        "instructions": "E2E Test"
    }

    client = app.test_client()
    
    start_time = time.time()
    try:
        print("Sending POST request to /generate_mashup (this may take 1-3 minutes due to 10 yt-dlp downloads)...")
        response = client.post('/generate_mashup', 
                               data=json.dumps(payload),
                               content_type='application/json')
        
        elapsed = time.time() - start_time
        print(f"Request completed in {elapsed:.1f} seconds. Status code: {response.status_code}")
        
        if response.status_code == 200:
            out_file = "C:\\Vihaan\\mashup-maker\\E2E_10_Song_Mashup.mp3"
            with open(out_file, "wb") as f:
                f.write(response.data)
            import os
            print(f"SUCCESS! File written to: {out_file}")
            print(f"File size: {os.path.getsize(out_file) / 1024.0:.2f} KB")
        else:
            print("FAILURE: API returned non-200 status.")
            print(response.data.decode('utf-8', errors='ignore'))
            
    except Exception as e:
        print("CRASH during API request:")
        traceback.print_exc()

if __name__ == '__main__':
    run_e2e_test()
