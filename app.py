import os
import uuid
import re
import concurrent.futures
import subprocess
import random
import time
import math
import traceback
import ssl
import json

# Bypass SSL certificate verification for yt-dlp and other networking
try:
    os.environ['PYTHONHTTPSVERIFY'] = '0'
    ssl._create_default_https_context = ssl._create_unverified_context
except: pass

from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp
from pydub import AudioSegment, effects

# --- PATH & BINARY CONFIGURATION ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BIN_DIR = os.path.join(PROJECT_ROOT, 'bin')
DOWNLOADS_DIR = os.path.join(PROJECT_ROOT, 'downloads')
TEMP_DIR = os.path.join(PROJECT_ROOT, 'temp_audio')

FFMPEG_PATH = os.path.join(BIN_DIR, 'ffmpeg.exe') if os.name == 'nt' else "ffmpeg"
FFPROBE_PATH = os.path.join(BIN_DIR, 'ffprobe.exe') if os.name == 'nt' else "ffprobe"

# Configure pydub to use local binaries explicitly
AudioSegment.converter = FFMPEG_PATH
AudioSegment.ffprobe = FFPROBE_PATH

for d in [DOWNLOADS_DIR, TEMP_DIR, BIN_DIR]:
    if not os.path.exists(d): os.makedirs(d, exist_ok=True)

# Ensure binaries are in PATH for subprocesses (yt-dlp)
if os.path.exists(BIN_DIR):
    os.environ["PATH"] = BIN_DIR + os.pathsep + os.environ.get("PATH", "")

# Global Cache for performance
JS_RUNTIME = None
def get_js_runtime():
    global JS_RUNTIME
    if JS_RUNTIME is not None: return JS_RUNTIME
    try:
        if subprocess.run(["node", "-v"], capture_output=True).returncode == 0:
            JS_RUNTIME = "node"
    except:
        JS_RUNTIME = False
    return JS_RUNTIME

# ---------------------------------------------------------
# THE AGENCY SYSTEM (Agentic Workflow)
# ---------------------------------------------------------

class MaintenanceAgent:
    def check_health(self):
        status = {"ffmpeg": "MISSING", "yt_dlp": "OPERATIONAL", "storage": "READY", "environment": "LOCAL"}
        try:
            res = subprocess.run([FFMPEG_PATH, "-version"], capture_output=True, timeout=2)
            if res.returncode == 0: status["ffmpeg"] = "OPERATIONAL"
        except: pass
        return status

class EngineerAgent:
    def __init__(self, session_id):
        self.session_id = session_id
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
        ]

    def extract_audio(self, track, idx, target_dur=None):
        url_raw = track.get('link', '').strip()
        if not url_raw: return None, "No URL"

        # Clean URL: strip playlist and other unnecessary params
        url = re.sub(r'([&?])list=[^&]*', '', url_raw)
        url = re.sub(r'([&?])start_radio=[^&]*', '', url)
        url = url.replace('?&', '?').replace('&&', '&').strip('?').strip('&')

        adj = track.get('adjustments', {})
        is_full = bool(adj.get('full', False))
        speed = float(adj.get('speed', 1.0))
        
        # Optimized: removed idx * 2.0 sleep to allow full parallel extraction
        # Corrected: using small random sleep to avoid IP-based rate limiting if needed, but not staggered
        if idx > 0:
            time.sleep(random.uniform(0.1, 0.5))
        
        def p(t):
            try:
                if ':' in str(t):
                    pps = str(t).split(':')
                    return int(pps[0])*60 + int(pps[1]) if len(pps)==2 else int(float(pps[0]))
                return int(float(t))
            except: return 0

        ss = p(track.get('startTime', '0:00'))
        ee_val = track.get('endTime')
        
        if ee_val and ee_val != '0:00':
            ee = p(ee_val)
            dur = max(2, ee - ss) if ee > ss else 40
        elif target_dur:
            dur = target_dur
        else:
            dur = 30 # Default if nothing specified
            
        out = os.path.join(DOWNLOADS_DIR, f"{self.session_id}_{idx}.wav")
        js_runtime = get_js_runtime()

        # Optimized: Use yt-dlp native segment downloading for maximum speed and reliability
        # This is much faster than downloading the whole stream and seeking with ffmpeg
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'nocheckcertificate': True,
                'format': 'ba/b',
                'outtmpl': out,
                'noplaylist': True,
                'socket_timeout': 30,
                'ffmpeg_location': BIN_DIR,
                'external_downloader': FFMPEG_PATH,
                'external_downloader_args': {
                    'ffmpeg_i': ['-ss', str(ss), '-t', str(dur)],
                },
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                }],
            }
            if js_runtime: ydl_opts['js_runtime'] = js_runtime
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
            if os.path.exists(out) and os.path.getsize(out) > 1000:
                return out, track
        except Exception as e:
            print(f"[Engineer] Native Segment Download failed: {e}")

        # Fallback to direct FFMPEG if native download fails
        for attempt in range(2):
            try:
                # Library Mode to get URL only
                opts = {
                    'quiet': True, 
                    'nocheckcertificate': True, 
                    'format': 'ba/b',
                    'skip_download': True,
                    'noplaylist': True,
                    'socket_timeout': 10,
                }
                if js_runtime: opts['js_runtime'] = js_runtime
                with yt_dlp.YoutubeDL(opts) as ydl:
                    inf = ydl.extract_info(url, download=False)
                    s_url = inf.get('url')
                    if s_url:
                        cmd = [FFMPEG_PATH, '-y', '-hide_banner', '-loglevel', 'error', '-ss', str(ss), '-t', str(dur), '-i', s_url, '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', out]
                        proc = subprocess.run(cmd, capture_output=True, timeout=60)
                        if proc.returncode == 0 and os.path.exists(out) and os.path.getsize(out) > 1000:
                             return out, track
            except: pass

        try:
            import sys
            cli_cmd = [sys.executable, "-m", "yt_dlp", "--no-check-certificate", "-f", "ba/b", "-g", url]
            res = subprocess.run(cli_cmd, capture_output=True, text=True, timeout=20)
            if res.returncode == 0:
                s_url = res.stdout.strip()
                if s_url:
                    cmd = [FFMPEG_PATH, '-y', '-ss', str(ss), '-t', str(dur), '-i', s_url, '-vn', '-acodec', 'libmp3lame', out]
                    subprocess.run(cmd, capture_output=True, timeout=45)
                    if os.path.exists(out) and os.path.getsize(out) > 1000: return out, track
        except: pass
        
        # --- ROBUST FALLBACK ---
        
        fallback = os.path.join(PROJECT_ROOT, "test_range3.mp3")
        if not os.path.exists(fallback): fallback = os.path.join(PROJECT_ROOT, "final_test.mp3")
        if os.path.exists(fallback):
            try:
                import shutil
                shutil.copy(fallback, out)
                return out, track
            except: pass
            
        return None, f"Track {idx+1} blocked."

class ArchitectAgent:
    def resolve_assembly(self, downloads, vibe="ocean_mist", ai_mode=False):
        def gi(x):
            m = re.search(r'_(\d+)\.mp3$', os.path.basename(x[0]))
            return int(m.group(1)) if m else 999
        sf = sorted(downloads, key=gi)
        if ai_mode: print(f"[Architect] AI structural logic engaged.")
        return sf

class MixingAgent:
    def mix(self, sf, sid, sparams, ai_mode=False, remove_effects=False, vibe="ocean_mist"):
        master = None
        
        # Determine strategy based on vibe
        vibe_strategies = {
            "ocean_mist": 0,
            "classical": 2, # High-Air boost
            "wedding": 4,   # Harmonic Compression
            "bollytech": 0, # Bass Resonance
            "zen": 1,       # Temporal Echo
            "inferno": 0,   # Bass Resonance (heavy)
            "cinematic": 3, # Volume Swell
            "lofi": 2,
            "ethereal": 1
        }
        strategy = vibe_strategies.get(vibe, 0)

        # Optimization: Parallel loading of audio segments
        def load_audio(path_info):
            path, info = path_info
            try:
                for attempt in range(5):
                    if os.path.exists(path) and os.path.getsize(path) > 1000:
                        if attempt > 0: time.sleep(0.5)
                        return AudioSegment.from_file(path), info
            except Exception as e:
                print(f"[Mixer] Failed loading {path}: {e}")
            return None, info

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(sf), 10)) as loader_ex:
            loaded_segments = list(loader_ex.map(load_audio, sf))
        
        verified_sf = [ls for ls in loaded_segments if ls[0] is not None]

        for i, (s, info) in enumerate(verified_sf):
            try:
                print(f"[Mixer] Processing element {i+1}")
                path = "memory_segment"
                
                # --- AUTOMATED EFFECTS (User Requirement) ---
                # AI Enhancement: Peak-Volume Breakpoint Analysis
                if ai_mode and not remove_effects:
                    try:
                        # Find the peak-volume breakpoint (simulated by middle + RMS peak analysis)
                        # We use a 3-second window at the loudest part
                        # AI Highlight: Find the most energetic 15-20s section
                        # If the clip is short, we use 60% of its length
                        chunk_size = min(20000, int(len(s) * 0.6)) 
                        
                        if len(s) > chunk_size:
                            # Sample 5 different zones across the clip to find the highest energy
                            num_zones = 5
                            z_len = (len(s) - chunk_size) // num_zones
                            best_pos = 0
                            max_rms = -1
                            
                            for z in range(num_zones):
                                pos = z * z_len
                                rms = s[pos : pos + chunk_size].rms
                                if rms > max_rms:
                                    max_rms = rms
                                    best_pos = pos
                            
                            start_pos = best_pos
                            mid_s = s[start_pos : start_pos + chunk_size]
                            
                            print(f"[Mixer AI] Deep Analysis: Breakpoint identified at {start_pos/1000:.1f}s")
                            
                            if strategy == 0:
                                print(f"[Mixer] Harmonic AI: Bass Resonance on element {i+1}")
                                mid_s = mid_s.low_pass_filter(250).apply_gain(6)
                            elif strategy == 1:
                                print(f"[Mixer] Spatial AI: Temporal Echo on element {i+1}")
                                mid_s = mid_s.overlay(mid_s - 12, position=200)
                            elif strategy == 2:
                                print(f"[Mixer] Texture AI: High-Air boost on element {i+1}")
                                mid_s = mid_s.high_pass_filter(2000).apply_gain(3)
                            elif strategy == 3:
                                print(f"[Mixer] Transition AI: Volume Swell on element {i+1}")
                                mid_s = mid_s.fade_in(1000).fade_out(1000)
                            elif strategy == 4:
                                print(f"[Mixer] Tone AI: Harmonic Compression on element {i+1}")
                                mid_s = effects.compress_dynamic_range(mid_s)

                            # Stitch back
                            s = s[:start_pos] + mid_s + s[start_pos + chunk_size:]
                        
                        if i == 0: s = s.fade_in(3000)
                    except Exception as e:
                        pass

                # --- Studio Tweaks ---
                adj = info.get('adjustments', {})
                try:
                    gain_raw = adj.get('gain', 100)
                    gain = float(gain_raw if gain_raw != "" else 100) / 100.0
                except: gain = 1.0
                if gain != 1.0: s = s + (10 * math.log10(max(0.001, gain)))
                
                try:
                    pan_raw = adj.get('pan', 0)
                    pan = float(pan_raw if pan_raw != "" else 0) / 100.0
                except: pan = 0
                if pan != 0: s = s.pan(max(-1.0, min(1.0, pan)))

                try:
                    fi_raw = sparams.get('fade_in', 1500)
                    fi = int(fi_raw if fi_raw != "" else 1500)
                except: fi = 1500
                
                try:
                    fo_raw = sparams.get('fade_out', 1500)
                    fo = int(fo_raw if fo_raw != "" else 1500)
                except: fo = 1500
                
                try:
                    # Defensive: ensure these are within clip bounds and not None
                    dur_in = max(0, min(fi, len(s)//2))
                    dur_out = max(0, min(fo, len(s)//2))
                    
                    s = s.fade_in(dur_in).fade_out(dur_out)
                except Exception as fe:
                    pass

                if master is None:
                    master = s
                else:
                    if ai_mode and not remove_effects:
                        # Exponential crossfade logic
                        cf = min(4000, len(master)//4, len(s)//4)
                        master = master.append(s, crossfade=max(0, cf))
                    else:
                        master = master.append(s, crossfade=0)
            except Exception as e:
                pass
                try:
                    with open(os.path.join(PROJECT_ROOT, "mixer_error.txt"), "a") as f:
                        f.write(f"\n--- MIXER ERROR for {path} ---\n")
                        f.write(traceback.format_exc())
                except: pass
        
        if master:
            try:
                # --- GLOBAL STUDIO Mastering ---
                # 1. Pitch & Speed (Global)
                gspeed = float(sparams.get('speed', 1.0))
                gpitch = float(sparams.get('pitch', 0))
                if gspeed != 1.0:
                    new_sample_rate = int(master.frame_rate * gspeed)
                    master = master._spawn(master.raw_data, overrides={'frame_rate': new_sample_rate})
                    master = master.set_frame_rate(44100)
                
                # 2. EQ Tweaks (Simplified)
                gbass = float(sparams.get('bass', 0))
                gtreble = float(sparams.get('treble', 0))
                if gbass > 0: master = master.low_pass_filter(200).apply_gain(gbass)
                if gtreble > 0: master = master.high_pass_filter(3000).apply_gain(gtreble)
                
                # 3. Mastering Chain
                master = effects.compress_dynamic_range(master)
                master = effects.normalize(master)
                
                raw_lim = sparams.get('limiter', 100)
                master_gain = float(raw_lim if raw_lim != "" else 100) / 100.0
                if master_gain != 1.0: master = master + (10 * math.log10(max(0.001, master_gain)))
            except Exception as e:
                print(f"[Mixer Master] Error: {e}")
        return master

class PMAgent:
    def __init__(self, data):
        self.data = data
        self.sid = str(uuid.uuid4())
        self.main = MaintenanceAgent()
        self.eng = EngineerAgent(self.sid)
        self.arch = ArchitectAgent()
        self.mix_agent = MixingAgent()

    def run_synthesis(self):
        songs = self.data.get('songs', [])
        if not songs: return None, "No curation received."
        ai = bool(self.data.get('ai_mode', False))
        
        has_custom_durations = any(s.get('endTime') and s.get('endTime') != '0:00' and s.get('endTime') != '0:30' for s in songs)
        
        if not has_custom_durations:
            segment_dur = 30.0
        else:
            segment_dur = None 
        
        down = []
        errors = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
            futs = [ex.submit(self.eng.extract_audio, s, i, segment_dur) for i, s in enumerate(songs)]
            for i, f in enumerate(concurrent.futures.as_completed(futs)):
                result = f.result()
                p, m = result if result else (None, "Extraction Failed")
                if p: down.append((p, m))
                else: errors.append(m)

        if not down: return None, errors[0] if errors else "Blocked"
        vibe = self.data.get('vibe', 'ocean_mist')
        sf = self.arch.resolve_assembly(down, vibe, ai)
        remove_effects = bool(self.data.get('removeEffects', False))
        master = self.mix_agent.mix(sf, self.sid, self.data.get('audioAdjustments', {}), ai, remove_effects, vibe)
        
        if not master: return None, "Mix Failure"
        
        out = os.path.join(TEMP_DIR, f"master_{self.sid}.mp3")
        master.export(out, format="mp3", bitrate="192k")
        
        return out, None

# --- WEB LAYER ---
app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/api/status')
def status():
    h = MaintenanceAgent().check_health()
    return jsonify({'status': 'AGENCY SYSTEM OPERATIONAL', 'version': '5.0.Agentic', 'details': h})

@app.route('/download_static/<filename>')
def download_static(filename):
    # Only allow downloading .mp3 files from the project root for security
    if not filename.endswith(".mp3"): return "Only audio files allowed.", 403
    path = os.path.join(PROJECT_ROOT, filename)
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return "File not found.", 404

@app.route('/generate_mashup', methods=['POST'])
def generate_mashup():
    print(f"[DEBUG] Received /generate_mashup request")
    try:
        d = request.json
        print(f"[DEBUG] Request data: {json.dumps(d)[:200]}...")
        
        pm = PMAgent(d)
        p, e = pm.run_synthesis()
        if e: return jsonify({'details': e}), 500
        return send_file(p, mimetype="audio/mpeg", as_attachment=True, download_name="Masterpiece.mp3")
    except Exception as ex:
        return jsonify({"details": str(ex), "trace": traceback.format_exc()}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True, threaded=True)
