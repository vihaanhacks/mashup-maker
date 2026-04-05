import sys
sys.path.append('.')
from app import app
import json
import time
import os

def run_user_curated_mashup():
    print("Initializing User-Curated 7-Minute Bollywood Masterpiece...")
    
    # User Provided Links (8)
    user_links = [
        "https://www.youtube.com/watch?v=oafxkMv4xnc",
        "https://www.youtube.com/watch?v=F2m4HPLvj-4",
        "https://www.youtube.com/watch?v=jMNllny2noo",
        "https://www.youtube.com/watch?v=ODu7OyAqK-Q",
        "https://www.youtube.com/watch?v=9T-Zbxg9X_4",
        "https://www.youtube.com/watch?v=czgm5uaO3gI",
        "https://www.youtube.com/watch?v=YyepU5ztLf4",
        "https://www.youtube.com/watch?v=x5Oag4hISgU"
    ]
    
    # 2 Additional Reliable Indian Hits to reach 10 tracks
    extra_links = [
        "https://www.youtube.com/watch?v=Umqb9Ken_GQ", # Tum Hi Ho (T-Series)
        "https://www.youtube.com/watch?v=gq822Z_9_0s"  # Raataan Lambiyan
    ]
    
    all_links = user_links + extra_links
    
    songs = []
    # 55 seconds per song * 10 songs = 550s (9 minutes raw, ~8 minutes after crossfades)
    for i, link in enumerate(all_links):
        songs.append({
            "link": link,
            "startTime": "0:30", # Skip intro
            "endTime": "1:25", 
            "adjustments": {"gain": 100, "pan": 0, "full": False, "speed": 1.0}
        })

    payload = {
        "ai_mode": True,
        "songs": songs,
        "audioAdjustments": {
            "fade_in": 3000, "fade_out": 3000, "limiter": 100,
            "compression": 40, "reverb": 30
        },
        "instructions": "Professional 7-Minute Bollywood Mashup. Multi-track high-fidelity."
    }

    client = app.test_client()
    start_time = time.time()
    try:
        print(f"Synthesis started at {time.ctime()} (10 songs, 55s segments)...")
        response = client.post('/generate_mashup', data=json.dumps(payload), content_type='application/json')
        if response.status_code == 200:
            out_file = "C:\\Vihaan\\mashup-maker\\Bollywood_7Min_Masterpiece.mp3"
            with open(out_file, "wb") as f:
                f.write(response.data)
            print(f"SUCCESS! Created: {out_file} ({time.time()-start_time:.1f}s)")
            import os
            # Verify duration with ffprobe if path exists
            ff_p = r"C:\Vihaan\mashup-maker\bin\ffprobe.exe"
            if os.path.exists(ff_p):
                import subprocess
                res = subprocess.run([ff_p, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", out_file], capture_output=True, text=True)
                print(f"Verified Duration: {res.stdout.strip()} seconds")
        else:
            print(f"FAILED: {response.data.decode()}")
    except:
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    run_user_curated_mashup()
