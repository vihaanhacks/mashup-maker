import sys
import os
import uuid
import uuid
sys.path.append('.')
from pydub import AudioSegment
from app import MixingAgent, TEMP_DIR

def run_verification():
    print("Initializing 10-Track Verification Pipeline...")
    
    # Check for a local source file to act as our audio base
    source_file = "user_mashup_test.mp3"
    if not os.path.exists(source_file):
        print(f"Test source {source_file} not found. Trying another...")
        source_file = "final_test.mp3"
        if not os.path.exists(source_file):
             print("Please run this where a valid mp3 exists.")
             return
             
    try:
        print(f"Loading '{source_file}' as root material...")
        root_audio = AudioSegment.from_mp3(source_file)
    except Exception as e:
        print(f"Could not load audio: {e}")
        return

    # Generate 10 dummy slices from the root audio to emulate yt-dlp downloads
    sf = []
    chunk_length = 3000 # 3 seconds per simulated track
    
    # We create an array formatted identically to ArchitectureAgent output
    for i in range(10):
        start = (i * chunk_length) % len(root_audio)
        slice_audio = root_audio[start : start + chunk_length]
        
        tmp_path = os.path.join(TEMP_DIR, f"mock_track_{i}.mp3")
        slice_audio.export(tmp_path, format="mp3")
        
        info = {'adjustments': {'gain': 100, 'pan': 0, 'speed': 1.0}}
        sf.append((tmp_path, info))
        print(f"[Verification] Emulated download for node {i+1} completed -> {tmp_path}")

    print("\n[Verification] Commencing Assembly via MixingAgent...")
    mixer = MixingAgent()
    sid = str(uuid.uuid4())
    
    # Passing ai_mode=True and remove_effects=False to trigger dynamic per-track logic
    master = mixer.mix(sf, sid, sparams={'fade_in': 500, 'fade_out': 500}, ai_mode=True, remove_effects=False)
    
    if master:
        out_path = os.path.join(TEMP_DIR, "10_song_master_verified.mp3")
        master.export(out_path, format="mp3", bitrate="192k")
        print(f"\n[Verification] SUCCESS! Master compiled to {out_path}")
        print(f"Master Duration: {len(master) / 1000.0} seconds")
        print(f"Master Size: {os.path.getsize(out_path) / 1024.0:.2f} KB")
    else:
        print("\n[Verification] FAILURE: Master output is null.")

if __name__ == '__main__':
    run_verification()
