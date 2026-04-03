import sys
sys.path.append('.')
from app import app
import json
import time
import traceback
import os

def run_hindi_mashup_v2():
    print("Initializing Professional 7-Minute Hindi Mashup Synthesis (v2)...")
    
    # 10 Popular Hindi Songs with 40s segments
    tracklist = [
        {"name": "Kesariya", "link": "https://www.youtube.com/watch?v=BddP6PYo2ps", "start": "1:00", "end": "1:40"},
        {"name": "Tum Hi Ho", "link": "https://www.youtube.com/watch?v=Umqb9Ken_GQ", "start": "0:45", "end": "1:25"},
        {"name": "Raataan Lambiyan", "link": "https://www.youtube.com/watch?v=gq822Z_9_0s", "start": "0:30", "end": "1:10"},
        {"name": "Jhoome Jo Pathaan", "link": "https://www.youtube.com/watch?v=Y9rxOBA_EYw", "start": "1:15", "end": "1:55"},
        {"name": "Chaiyya Chaiyya", "link": "https://www.youtube.com/watch?v=PQmrmV19Lhk", "start": "0:00", "end": "0:40"},
        {"name": "Kal Ho Naa Ho", "link": "https://www.youtube.com/watch?v=g0eO74UmRBs", "start": "0:50", "end": "1:30"},
        {"name": "Ae Dil Hai Mushkil", "link": "https://www.youtube.com/watch?v=6FURuLYrR_Q", "start": "1:10", "end": "1:50"},
        {"name": "Kabira", "link": "https://www.youtube.com/watch?v=jHNNMj5bNQw", "start": "1:20", "end": "2:00"},
        {"name": "Pasoori", "link": "https://www.youtube.com/watch?v=5Eqb_-j3FDA", "start": "0:40", "end": "1:20"},
        {"name": "Apna Time Aayega", "link": "https://www.youtube.com/watch?v=hZ_YstWf22U", "start": "0:30", "end": "1:10"}
    ]
    
    songs = []
    for i, t in enumerate(tracklist):
        songs.append({
            "link": t["link"],
            "startTime": t["start"],
            "endTime": t["end"],
            "adjustments": {
                "gain": 100,
                "pan": 0,
                "full": False,
                "speed": 1.0
            }
        })

    payload = {
        "ai_mode": True,
        "removeEffects": False,
        "vibe": "bollywood_dreams",
        "songs": songs,
        "audioAdjustments": {
            "bass": 3, "mid": 2, "treble": 3, "speed": 1.0, 
            "pitch": 0, "reverb": 40, "delay": 20, "chorus": 20, 
            "phaser": 0, "distortion": 0, "bitcrush": 0, "tremolo": 0, 
            "flanger": 0, "compression": 40, "limiter": 95, "width": 140, 
            "fade_in": 3000, "fade_out": 3000, "highpass": 10, "lowpass": 90
        },
        "instructions": "Professional Hindi Mashup - Over 6 minutes. Advanced Breakpoint AI."
    }

    client = app.test_client()
    
    print(f"Synthesis started at {time.ctime()}...")
    print("Downloading 10 tracks and processing (est. 5-10 minutes)...")
    
    start_time = time.time()
    try:
        response = client.post('/generate_mashup', 
                               data=json.dumps(payload),
                               content_type='application/json')
        
        elapsed = time.time() - start_time
        print(f"Request completed in {elapsed:.1f} seconds. Status code: {response.status_code}")
        
        if response.status_code == 200:
            out_file = "C:\\Vihaan\\mashup-maker\\Hindi_Professional_Legacy_Mashup_7Min.mp3"
            with open(out_file, "wb") as f:
                f.write(response.data)
            print(f"SUCCESS! Masterpiece generated at: {out_file}")
            print(f"Duration: ~400 seconds (6.6 minutes)")
            print(f"File Size: {os.path.getsize(out_file) / (1024*1024):.2f} MB")
        else:
            print("FAILURE: API error.")
            print(response.data.decode('utf-8', errors='ignore'))
            
    except Exception as e:
        print("CRASH during synthesis:")
        traceback.print_exc()

if __name__ == '__main__':
    run_hindi_mashup_v2()
