import sys
sys.path.append('.')
from app import app
import json
import time
import os

def run_fast_hindi():
    print("Fast-Tracking Professional Hindi Mashup...")
    
    # 10 Popular Hindi Songs (Reliable Links)
    tracklist = [
        {"link": "https://www.youtube.com/watch?v=BddP6PYo2ps", "start": "1:00", "end": "1:35"},
        {"link": "https://www.youtube.com/watch?v=Umqb9Ken_GQ", "start": "0:45", "end": "1:20"},
        {"link": "https://www.youtube.com/watch?v=gq822Z_9_0s", "start": "0:30", "end": "1:05"},
        {"link": "https://youtube.com/shorts/jfKfPfyJRdk", "start": "0:00", "end": "0:30"},
        {"link": "https://www.youtube.com/watch?v=PQmrmV19Lhk", "start": "0:00", "end": "0:35"},
        {"link": "https://www.youtube.com/watch?v=g0eO74UmRBs", "start": "0:50", "end": "1:25"},
        {"link": "https://www.youtube.com/watch?v=6FURuLYrR_Q", "start": "1:10", "end": "1:45"},
        {"link": "https://www.youtube.com/watch?v=jHNNMj5bNQw", "start": "1:20", "end": "1:55"},
        {"link": "https://www.youtube.com/watch?v=5Eqb_-j3FDA", "start": "0:40", "end": "1:15"},
        {"link": "https://youtube.com/shorts/jfKfPfyJRdk", "start": "0:00", "end": "0:30"}
    ]
    
    songs = []
    for t in tracklist:
        songs.append({
            "link": t["link"],
            "startTime": t["start"],
            "endTime": t["end"],
            "adjustments": {"gain": 100, "pan": 0, "full": False, "speed": 1.0}
        })

    payload = {
        "ai_mode": True,
        "songs": songs,
        "audioAdjustments": {"fade_in": 2000, "fade_out": 2000, "limiter": 100}
    }

    client = app.test_client()
    start_time = time.time()
    try:
        response = client.post('/generate_mashup', data=json.dumps(payload), content_type='application/json')
        if response.status_code == 200:
            out_file = "C:\\Vihaan\\mashup-maker\\Hindi_Fast_Masterpiece_5Min.mp3"
            with open(out_file, "wb") as f:
                f.write(response.data)
            print(f"SUCCESS! Created: {out_file} ({time.time()-start_time:.1f}s)")
        else:
            print(f"FAILED: {response.data.decode()}")
    except:
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    run_fast_hindi()
