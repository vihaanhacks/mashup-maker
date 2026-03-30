import requests
import json
import time

url = "http://127.0.0.1:5000/generate_mashup"
data = {
    "ai_mode": True,
    "songs": [
        {"link": "https://www.youtube.com/watch?v=piW4gHWy8z8", "startTime": "0:00", "endTime": "0:05", "adjustments": {"gain": 100, "pan": 0, "speed": 1.0}},
        {"link": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "startTime": "0:00", "endTime": "0:10", "adjustments": {"gain": 100, "pan": 0, "speed": 1.0}}
    ],
    "vibe": "ocean_mist",
    "audioAdjustments": {"fade_in": 1000, "fade_out": 1000, "limiter": 100},
    "instructions": "Test 5 songs synthesis"
}

print("Starting synthesis test with 5 songs...")
start_time = time.time()
try:
    response = requests.post(url, json=data, timeout=300)
    if response.status_code == 200:
        with open("test_5songs_result.mp3", "wb") as f:
            f.write(response.content)
        print(f"Success! Mashup generated in {time.time() - start_time:.2f} seconds.")
    else:
        print(f"Failed: {response.status_code}")
        print(response.json())
except Exception as e:
    print(f"Error: {e}")
