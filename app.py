import os
import sys
import uuid
import subprocess
import concurrent.futures
import traceback
import math
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BIN_DIR = os.path.join(PROJECT_ROOT, 'bin')
DOWNLOADS_DIR = os.path.join(PROJECT_ROOT, 'downloads')
TEMP_DIR = os.path.join(PROJECT_ROOT, 'temp_audio')

# Explicitly use FFmpeg from environment or default path
FFMPEG_PATH = os.environ.get("FFMPEG_PATH")
if not FFMPEG_PATH:
    if os.name == 'nt': # Windows
        FFMPEG_PATH = os.path.join(BIN_DIR, 'ffmpeg.exe')
    else: # Linux/Mac
        FFMPEG_PATH = "ffmpeg" # Assume in PATH

# Ensure binaries are in PATH
if os.path.exists(BIN_DIR):
    os.environ["PATH"] = BIN_DIR + os.pathsep + os.environ.get("PATH", "")

try:
    import yt_dlp
    from pydub import AudioSegment
    AudioSegment.converter = FFMPEG_PATH
except ImportError:
    print("Warning: Missing dependencies (yt-dlp or pydub)", flush=True)

app = Flask(__name__)
CORS(app)

os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

def parse_time(t_str):
    if not t_str: return 0
    try:
        parts = str(t_str).split(':')
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        return int(float(parts[0]))
    except:
        return 0

def download_track(track, idx, session_id):
    url = track.get('link')
    if not url:
        return None, "No URL provided for track"
        
    adj = track.get('adjustments', {})
    is_full = adj.get('full', False)
    speed = float(adj.get('speed', 1.0))
    
    start_sec = parse_time(track.get('startTime', '0:00'))
    end_sec = parse_time(track.get('endTime', '0:30'))
    dur = 30
    if end_sec > start_sec:
        dur = end_sec - start_sec
    else:
        dur = 30 # Default fallback
    
    out_raw = os.path.join(DOWNLOADS_DIR, f"{session_id}_{idx}.mp3")
    
    try:
        # 1. Extract best audio URL
        ydl_opts = {
            'quiet': True, 
            'no_warnings': True,
            'geo_bypass': True,
            'nocheckcertificate': True,
            'youtube_include_dash_manifest': False,
            'format': 'bestaudio/best'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Find best audio-only format
            formats = info.get('formats', [])
            audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
            if not audio_formats:
                audio_formats = [f for f in formats if f.get('acodec') != 'none']
                
            if not audio_formats:
                raise RuntimeError("No valid audio formats found")
                
            best_audio = max(audio_formats, key=lambda f: f.get('abr') or 0)
            audio_url = best_audio['url']
            
        print(f"Streaming: {url} | Full={is_full} | Speed={speed}", flush=True)
        
        # 2. Manual FFmpeg download for the range
        cmd = [FFMPEG_PATH, '-y']
        if not is_full:
            cmd += ['-ss', str(start_sec), '-t', str(dur)]
        cmd += ['-i', audio_url, '-vn', '-acodec', 'libmp3lame', '-ab', '128k']
        
        if speed != 1.0:
            cmd += ['-filter:a', f"atempo={speed}"]
            
        cmd.append(out_raw)
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            print(f"FFMPEG ERROR for {url}:\n{result.stderr}", flush=True)
            raise RuntimeError(f"FFmpeg failed with exit code {result.returncode}")
            
        if not os.path.exists(out_raw) or os.path.getsize(out_raw) == 0:
            raise RuntimeError("Generated file is empty or missing")
            
        return out_raw, track
        
    except Exception as e:
        traceback.print_exc()
        return None, str(e)

@app.route('/generate_mashup', methods=['POST'])
def generate_mashup():
    try:
        data = request.json
        songs = data.get('songs', [])
        
        if not songs:
            return jsonify({'details': 'No sonic elements curated. Synthesis aborted.'}), 400
            
        session_id = str(uuid.uuid4())
        
        downloaded_files = []
        errors = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(download_track, track, i, session_id) for i, track in enumerate(songs)]
            for future in concurrent.futures.as_completed(futures):
                file_path, res = future.result()
                if file_path:
                    downloaded_files.append((file_path, res))
                else:
                    errors.append(res)
                    
        if not downloaded_files:
            return jsonify({'details': 'Synthesis Engine Failure: Could not process any tracks.', 'errors': errors}), 500
            
        # 3. Assemble Professional Mashup
        master = None
        for i, (path, track_info) in enumerate(downloaded_files):
            try:
                s = AudioSegment.from_mp3(path)
                
                # Apply 1-second fades for smooth transitions
                s = s.fade_in(1000).fade_out(1000)
                
                # Apply gain
                gain_val = float(track_info.get('adjustments', {}).get('gain', 100)) / 100.0
                if gain_val <= 0:
                    db_change = -100
                else:
                    db_change = 10 * math.log10(max(0.01, gain_val))
                s = s + db_change
                
                # Apply pan
                pan_val = float(track_info.get('adjustments', {}).get('pan', 0)) / 100.0
                s = s.pan(max(-1.0, min(1.0, pan_val)))
                
                if master is None:
                    master = s
                else:
                    # 3-second 'Mashup' Overlap
                    cf = min(3000, len(master)//2, len(s)//2)
                    master = master.append(s, crossfade=cf)
            except Exception as e:
                print(f"Mix error for {path}: {e}", flush=True)
                
        if master is None:
            return jsonify({'details': 'Final assembly failed.'}), 500
            
        out_path = os.path.join(TEMP_DIR, f"master_{session_id}.mp3")
        master.export(out_path, format="mp3")
        
        return send_file(out_path, mimetype="audio/mpeg", as_attachment=True, download_name="Masterpiece.mp3")
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'details': f"Systemic failure: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
