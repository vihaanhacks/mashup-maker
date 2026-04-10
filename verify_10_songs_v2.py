import requests
import time
import os

BASE_URL = "http://127.0.0.1:5000"

def run_test(name, lofi=False):
    print(f"\n--- Starting {name} Speed Test (10 Songs) ---")
    data = {
        "ai_mode": True,
        "lofi_mode": lofi,
        "songs": [
            {"link": "https://www.youtube.com/watch?v=mAuIqv2dV18", "startTime": "0:00", "endTime": "0:30"},
            {"link": "https://www.youtube.com/watch?v=8j3Uv6Gv_zs", "startTime": "0:00", "endTime": "0:30"},
            {"link": "https://www.youtube.com/watch?v=XHBvsDsECmQ", "startTime": "0:00", "endTime": "0:30"},
            {"link": "https://www.youtube.com/watch?v=-dt1VE_9EJI", "startTime": "0:00", "endTime": "0:30"},
            {"link": "https://www.youtube.com/watch?v=eyDoj4gUYxY", "startTime": "0:00", "endTime": "0:30"},
            {"link": "https://www.youtube.com/watch?v=piW4gHWy8z8", "startTime": "0:00", "endTime": "0:30"},
            {"link": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "startTime": "0:00", "endTime": "0:30"},
            {"link": "https://www.youtube.com/watch?v=kJQP7kiw5Fk", "startTime": "0:00", "endTime": "0:30"},
            {"link": "https://www.youtube.com/watch?v=JGwWNGJdvx8", "startTime": "0:00", "endTime": "0:30"},
            {"link": "https://www.youtube.com/watch?v=L0MK7qz13bU", "startTime": "0:00", "endTime": "0:30"}
        ],
        "vibe": "ocean_mist",
        "audioAdjustments": {}
    }

    start_time = time.time()
    try:
        # 10 songs might take a while, 5 mins timeout
        response = requests.post(f"{BASE_URL}/generate_mashup", json=data, timeout=300)
        end_time = time.time()

        if response.status_code == 200:
            duration = end_time - start_time
            print(f"SUCCESS: {name} generated in {duration:.2f} seconds.")
            
            with open(f"verify_10_{name.lower().replace(' ', '_')}.mp3", "wb") as f:
                f.write(response.content)
            
            if duration < 180:
                print(f"PERFORMANCE TARGET MET: {duration:.2f}s < 180s (3m)")
            else:
                print(f"PERFORMANCE TARGET FAILED: Took {duration:.2f} seconds.")
        else:
            print(f"FAILED: Status Code {response.status_code}")
            try:
                print(response.json())
            except:
                print(response.text[:200])
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    print("WARNING: Ensure app.py is running on http://127.0.0.1:5000")
    run_test("Standard Pro Mashup", lofi=False)
    run_test("Lofi Pro Mashup", lofi=True)
