import sys
sys.path.append('.')
from app import PMAgent, MixingAgent, TEMP_DIR
import os
import uuid

def test_mix():
    print("Testing 10-track mixing logic...")
    # Mock data
    data = {
        'removeEffects': True,
        'ai_mode': True,
        'songs': [
            {'link': 'https://youtube.com/shorts/jfKfPfyJRdk', 'startTime': '0:00', 'endTime': '0:02'} for _ in range(10)
        ]
    }
    pm = PMAgent(data)
    out, err = pm.run_synthesis()
    if err:
        print(f"Error: {err}")
    else:
        print(f"Success! Output at: {out}")
        print(f"Size: {os.path.getsize(out)} bytes")

if __name__ == '__main__':
    test_mix()
