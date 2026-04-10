import os
import json
from app import PMAgent

def test_local():
    print("--- Starting Local Synthesis Test (Bypassing Flask) ---")
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

    pm = PMAgent(data)
    import time
    start_time = time.time()
    
    out, err = pm.run_synthesis()
    
    end_time = time.time()
    
    if err:
        print(f"FAILED: {err}")
    else:
        print(f"SUCCESS: Generated {out} in {end_time - start_time:.2f} seconds.")
        if os.path.exists(out):
            print(f"File size: {os.path.getsize(out) / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    test_local()
