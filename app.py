import os
import sys
import uuid
import subprocess
import concurrent.futures
import traceback
import math
import re
import random
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BIN_DIR = os.path.join(PROJECT_ROOT, 'bin')
DOWNLOADS_DIR = os.path.join(PROJECT_ROOT, 'downloads')
TEMP_DIR = os.path.join(PROJECT_ROOT, 'temp_audio')

# FFmpeg path resolution
FFMPEG_PATH = os.environ.get("FFMPEG_PATH")
if not FFMPEG_PATH:
    if os.name == 'nt':  # Windows
        FFMPEG_PATH = os.path.join(BIN_DIR, 'ffmpeg.exe')
        if not os.path.exists(FFMPEG_PATH):
            FFMPEG_PATH = 'ffmpeg'
    else:  # Linux/Mac (Render)
        FFMPEG_PATH = "ffmpeg"

# Ensure binaries are in PATH
if os.path.exists(BIN_DIR):
    os.environ["PATH"] = BIN_DIR + os.pathsep + os.environ.get("PATH", "")

try:
    import yt_dlp
    from pydub import AudioSegment
    AudioSegment.converter = FFMPEG_PATH
except ImportError as e:
    print(f"Warning: Missing dependencies: {e}", flush=True)

# ---------------------------------------------------------
# THE AGENCY SYSTEM (Agentic Workflow)
# ---------------------------------------------------------

class EngineerAgent:
    """
    The Engineer is responsible for the technical extraction of audio.
    He uses multiple 'Strategies' to bypass YouTube's bot detection.
    """
    def __init__(self, session_id):
        self.session_id = session_id
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1'
        ]

    def extract_audio(self, track, idx):
        url = track.get('link', '').strip()
        if not url: return None, "No URL provided"

        adj = track.get('adjustments', {})
        is_full = bool(adj.get('full', False))
        speed = float(adj.get('speed', 1.0))
        
        def parse_to_sec(t):
            try:
                parts = str(t).split(':')
                return int(parts[0]) * 60 + int(parts[1]) if len(parts) == 2 else int(float(parts[0]))
            except: return 0

        start_sec = parse_to_sec(track.get('startTime', '0:00'))
        end_sec = parse_to_sec(track.get('endTime', '0:30'))
        dur = max(5, end_sec - start_sec) if end_sec > start_sec else 30

        out_path = os.path.join(DOWNLOADS_DIR, f"{self.session_id}_{idx}.mp3")

        # Agentic Countermeasures 4.2: 
        # Using specific player clients (iOS/Android) often bypasses desktop bot detection
        strategies = [
            # Strategy 1: iOS Client spoofing (Very effective)
            {'format': 'bestaudio', 'extractor_args': {'youtube': {'player_client': ['ios']}}},
            # Strategy 2: Android Client spoofing
            {'format': 'bestaudio', 'extractor_args': {'youtube': {'player_client': ['android']}}},
            # Strategy 3: Standard Web with Chrome User Agent
            {'format': 'bestaudio', 'user_agent': self.user_agents[0]}
        ]

        for s_idx, strategy_opts in enumerate(strategies):
            try:
                print(f"[Engineer] [{idx}] Applying Countermeasure {s_idx+1}: {strategy_opts.get('extractor_args', 'Web')}", flush=True)
                opts = {
                    'quiet': True, 
                    'nocheckcertificate': True, 
                    'geo_bypass': True,
                    **strategy_opts
                }
                
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    fmts = info.get('formats', [])
                    
                    stream_url = None
                    candidates = [f for f in fmts if f.get('acodec') != 'none' and f.get('url')]
                    if candidates:
                        stream_url = max(candidates, key=lambda f: f.get('abr') or 0)['url']
                    
                    if stream_url:
                        cmd = [FFMPEG_PATH, '-y']
                        if not is_full: cmd += ['-ss', str(start_sec), '-t', str(dur)]
                        cmd += ['-i', stream_url, '-vn', '-acodec', 'libmp3lame', '-ab', '128k', '-ar', '44100']
                        if speed != 1.0: cmd += ['-filter:a', f'atempo={max(0.5, min(2.0, speed))}']
                        cmd.append(out_path)
                        
                        subprocess.run(cmd, capture_output=True, timeout=300)
                        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
                            return out_path, track
            except Exception as e:
                print(f"[Engineer] [{idx}] Countermeasure {s_idx+1} BLOCKED", flush=True)

        return None, "All engineering strategies blocked by YouTube security."

class ArchitectAgent:
    """
    The Architect organizes the structural layout of the mashup.
    """
    def resolve_assembly(self, downloaded_files):
        def get_idx(item):
            m = re.search(r'_(\d+)\.mp3$', os.path.basename(item[0]))
            return int(m.group(1)) if m else 999
        return sorted(downloaded_files, key=get_idx)

class MixingAgent:
    """
    The Mixer applies final audio processing and merges tracks.
    """
    def mix(self, sorted_files):
        master = None
        for path, info in sorted_files:
            try:
                print(f"[Mixer] Processing: {os.path.basename(path)}", flush=True)
                s = AudioSegment.from_mp3(path)
                fade = min(1000, len(s)//4)
                s = s.fade_in(fade).fade_out(fade)

                adj = info.get('adjustments', {})
                gain_val = float(adj.get('gain', 100)) / 100.0
                db_change = 10 * math.log10(max(0.001, gain_val))
                s = s + db_change
                
                pan = float(adj.get('pan', 0)) / 100.0
                s = s.pan(max(-1.0, min(1.0, pan)))

                if master is None:
                    master = s
                else:
                    cf = min(3000, len(master)//4, len(s)//4)
                    print(f"[Mixer] Appending with {cf}ms crossfade", flush=True)
                    master = master.append(s, crossfade=max(0, cf))
            except Exception as e:
                print(f"[Mixer] Error on {path}: {e}", flush=True)
        return master

class PMAgent:
    """
    The Project Manager coordinates the entire Agency workflow.
    """
    def __init__(self, request_data):
        self.data = request_data
        self.session_id = str(uuid.uuid4())
        self.engineer = EngineerAgent(self.session_id)
        self.architect = ArchitectAgent()
        self.mixer = MixingAgent()

    def run_synthesis(self):
        songs = self.data.get('songs', [])
        if not songs: return None, "No curation received."

        print(f"[PM] Session {self.session_id} initiated.", flush=True)

        downloaded = []
        errors = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self.engineer.extract_audio, s, i) for i, s in enumerate(songs)]
            for f in concurrent.futures.as_completed(futures):
                path, meta = f.result()
                if path: downloaded.append((path, meta))
                else: errors.append(meta)

        if not downloaded:
            return None, f"All tracks blocked by YouTube: {errors[0] if errors else 'Unknown'}"

        if len(downloaded) < len(songs):
            print(f"[PM] Warning: Proceeding with {len(downloaded)}/{len(songs)} tracks.", flush=True)

        sorted_files = self.architect.resolve_assembly(downloaded)
        master = self.mixer.mix(sorted_files)

        if not master: return None, "Mixing failed."

        out_path = os.path.join(TEMP_DIR, f"master_{self.session_id}.mp3")
        master.export(out_path, format="mp3", bitrate="192k")
        print(f"[PM] SUCCESS. Session {self.session_id} finalized.", flush=True)
        return out_path, None

# ---------------------------------------------------------
# WEB INTERFACE
# ---------------------------------------------------------

app = Flask(__name__)
CORS(app)

@app.route('/')
def status():
    return jsonify({'status': 'AGENCY SYSTEM OPERATIONAL', 'version': '4.3.Agentic'})

@app.route('/generate_mashup', methods=['POST'])
def generate_mashup():
    try:
        pm = PMAgent(request.json)
        file_path, error = pm.run_synthesis()
        if error: return jsonify({'details': error}), 500
        return send_file(file_path, mimetype="audio/mpeg", as_attachment=True, download_name="Masterpiece.mp3")
    except Exception as e:
        traceback.print_exc()
        return jsonify({'details': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0' if os.environ.get('RENDER') else '127.0.0.1'
    app.run(host=host, port=port, debug=False)
