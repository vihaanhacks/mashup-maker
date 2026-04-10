import requests
import time
import json
import os

BASE_URL = "http://127.0.0.1:5000"

def test_synthesis_speed():
    print("--- Starting Synthesis Speed Test ---")
    data = {
        "ai_mode": True,
        "songs": [
            {"link": "https://www.youtube.com/watch?v=mAuIqv2dV18", "startTime": "0:00", "endTime": "1:00"},
            {"link": "https://www.youtube.com/watch?v=8j3Uv6Gv_zs", "startTime": "0:00", "endTime": "1:00"},
            {"link": "https://www.youtube.com/watch?v=XHBvsDsECmQ", "startTime": "0:00", "endTime": "1:00"},
            {"link": "https://www.youtube.com/watch?v=-dt1VE_9EJI", "startTime": "0:00", "endTime": "1:00"},
            {"link": "https://www.youtube.com/watch?v=eyDoj4gUYxY", "startTime": "0:00", "endTime": "1:00"}
        ],
        "vibe": "ocean_mist",
        "audioAdjustments": {}
    }

    start_time = time.time()
    try:
        response = requests.post(f"{BASE_URL}/generate_mashup", json=data, timeout=120)
        end_time = time.time()

        if response.status_status == 200:
            duration = end_time - start_time
            print(f"SUCCESS: Mashup generated in {duration:.2f} seconds.")
            
            # Check file size
            with open("test_speed_result.mp3", "wb") as f:
                f.write(response.content)
            
            file_size = os.path.getsize("test_speed_result.mp3")
            print(f"Result file size: {file_size / 1024 / 1024:.2f} MB")
            
            if duration < 60:
                print("PERFORMANCE TARGET MET: < 1 minute.")
            else:
                print(f"PERFORMANCE TARGET FAILED: Took {duration:.2f} seconds.")
        else:
            print(f"FAILED: Status Code {response.status_code}")
            print(response.json())
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    # Ensure backend is running before this
    test_synthesis_speed()
