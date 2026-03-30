import requests
import json
import time

url = "http://127.0.0.1:5000/generate_mashup"

# 1. Test 5-songs reliability
data_5 = {
    "songs": [
        {"link": "https://www.youtube.com/watch?v=piW4gHWy8z8", "startTime": "0:00", "endTime": "0:05", "adjustments": {"gain": 100, "pan": 0, "speed": 1.0}},
        {"link": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "startTime": "0:05", "endTime": "0:10", "adjustments": {"gain": 100, "pan": 0, "speed": 1.0}},
        {"link": "https://www.youtube.com/watch?v=9bZkp7q19f0", "startTime": "0:10", "endTime": "0:15", "adjustments": {"gain": 100, "pan": 0, "speed": 1.0}},
        {"link": "https://www.youtube.com/watch?v=kJQP7kiw5Fk", "startTime": "0:15", "endTime": "0:20", "adjustments": {"gain": 100, "pan": 0, "speed": 1.0}},
        {"link": "https://www.youtube.com/watch?v=JGwWNGJdvx8", "startTime": "0:20", "endTime": "0:25", "adjustments": {"gain": 100, "pan": 0, "speed": 1.0}}
    ],
    "vibe": "ocean_mist",
    "audioAdjustments": {"fade_in": 1000, "fade_out": 1000, "limiter": 100}
}

# 2. Test 1-song reliability
data_1 = {
    "songs": [
        {"link": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "startTime": "0:00", "endTime": "0:15", "adjustments": {"gain": 100, "pan": 0, "speed": 1.0}}
    ],
    "vibe": "ocean_mist",
    "audioAdjustments": {"fade_in": 1000, "fade_out": 1000, "limiter": 100}
}

def run_test(name, data):
    print(f"Running test: {name}...")
    try:
        res = requests.post(url, json=data, timeout=300)
        if res.status_code == 200:
            filename = f"test_{name}.mp3"
            with open(filename, "wb") as f:
                f.write(res.content)
            print(f"SUCCESS: {filename}")
        else:
            print(f"FAILED: {res.status_code}")
            print(res.json())
    except Exception as e:
        print(f"ERROR: {e}")

run_test("5_songs", data_5)
run_test("1_song", data_1)
