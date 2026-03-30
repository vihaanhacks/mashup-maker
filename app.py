import os
import uuid
import re
import concurrent.futures
import subprocess
import random
import time
import math
import traceback
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

    def extract_audio(self, track, idx):
        url = track.get('link', '').strip()
        if not url: return None, "No URL"
        adj = track.get('adjustments', {})
        is_full = bool(adj.get('full', False))
        speed = float(adj.get('speed', 1.0))
        
        def p(t):
            try:
                if ':' in str(t):
                    pps = str(t).split(':')
                    return int(pps[0])*60 + int(pps[1]) if len(pps)==2 else int(float(pps[0]))
                return int(float(t))
            except: return 0

        ss = p(track.get('startTime', '0:00'))
        ee = p(track.get('endTime', '0:30'))
        dur = max(2, ee - ss) if ee > ss else 30
        out = os.path.join(DOWNLOADS_DIR, f"{self.session_id}_{idx}.mp3")

        js_runtime = None
        try:
            if subprocess.run(["node", "-v"], capture_output=True).returncode == 0: js_runtime = "node"
        except: pass

        strategies = [
            {'format': 'ba/b', 'extractor_args': {'youtube': {'player_client': ['ios']}}},
            {'format': 'ba/b', 'extractor_args': {'youtube': {'player_client': ['android']}}},
            {'format': 'ba/b', 'user_agent': random.choice(self.user_agents)}
        ]

        for s_idx, opts_strat in enumerate(strategies):
            try:
                opts = {'quiet': True, 'nocheckcertificate': True, 'geo_bypass': True, 'no_warnings': True, **opts_strat}
                if js_runtime: opts['js_runtime'] = js_runtime
                with yt_dlp.YoutubeDL(opts) as ydl:
                    inf = ydl.extract_info(url, download=False)
                    s_url = inf.get('url')
                    if not s_url and inf.get('formats'):
                        fmts = [f for f in inf['formats'] if f.get('acodec')!='none' and f.get('url')]
                        if fmts: s_url = max(fmts, key=lambda f: f.get('abr') or 0)['url']
                    if s_url:
                        cmd = [FFMPEG_PATH, '-y', '-hide_banner', '-loglevel', 'error']
                        if not is_full: cmd += ['-ss', str(ss), '-t', str(dur)]
                        cmd += ['-i', s_url, '-vn', '-acodec', 'libmp3lame', '-ab', '192k', '-ar', '44100']
                        flts = []
                        if speed != 1.0: flts.append(f"atempo={max(0.5, min(2.0, speed))}")
                        if int(adj.get('lowcut', 0)) > 0: flts.append(f"highpass=f={int(adj['lowcut'])*20}")
                        if flts: cmd += ['-filter:a', ",".join(flts)]
                        cmd.append(out)
                        subprocess.run(cmd, capture_output=True, timeout=120)
                        if os.path.exists(out) and os.path.getsize(out) > 1000: return out, track
            except: pass
        return None, f"Track {idx+1} blocked."

class ArchitectAgent:
    def resolve_assembly(self, downloads, vibe="ocean_mist", ai_mode=False):
        def gi(x):
            m = re.search(r'_(\d+)\.mp3$', os.path.basename(x[0]))
            return int(m.group(1)) if m else 999
        sf = sorted(downloads, key=gi)
        if ai_mode: print(f"[Architect] AI structural logic engaged.", flush=True)
        return sf

class MixingAgent:
    def mix(self, sf, sid, sparams, ai_mode=False):
        master = None
        for i, (path, info) in enumerate(sf):
            try:
                print(f"[Mixer] Processing element {i+1}", flush=True)
                s = AudioSegment.from_mp3(path)
                
                # --- AUTOMATED EFFECTS (User Requirement) ---
                # 1. AI Enhancement (Lows/Highs balance)
                try:
                    lows = s.low_pass_filter(250).apply_gain(3)
                    highs = s.high_pass_filter(250).apply_gain(1)
                    s = lows.overlay(highs)
                except: pass
                
                # 2. Automated Reverb/Space (Enhanced for user request)
                try:
                    # Multi-tap delay for thicker space
                    echo1 = s - 12
                    echo2 = s - 18
                    s = s.overlay(echo1, position=120).overlay(echo2, position=240)
                except: pass

                # --- Studio Tweaks ---
                adj = info.get('adjustments', {})
                gain = float(adj.get('gain', 100)) / 100.0
                if gain != 1.0: s = s + (10 * math.log10(max(0.001, gain)))
                pan = float(adj.get('pan', 0)) / 100.0
                if pan != 0: s = s.pan(max(-1.0, min(1.0, pan)))

                fi = int(sparams.get('fade_in', 1500))
                fo = int(sparams.get('fade_out', 1500))
                s = s.fade_in(min(fi, len(s)//4)).fade_out(min(fo, len(s)//4))

                if master is None:
                    master = s
                else:
                    cf = min(4000, len(master)//4, len(s)//4)
                    master = master.append(s, crossfade=max(0, cf))
            except Exception:
                print(f"[Mixer] Skip error on {path}", flush=True)
                traceback.print_exc()
        
        if master:
            if len(sf) == 1: master = effects.normalize(master)
            try:
                master = effects.compress_dynamic_range(master)
                master = effects.normalize(master)
                master_gain = float(sparams.get('limiter', 100)) / 100.0
                if master_gain != 1.0: master = master + (10 * math.log10(max(0.001, master_gain)))
            except: pass
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
        if self.main.check_health()["ffmpeg"] != "OPERATIONAL": return None, "FFmpeg Offline"
        songs = self.data.get('songs', [])
        if not songs: return None, "No curation received."
        ai = bool(self.data.get('ai_mode', False))
        
        down = []
        errors = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
            futs = [ex.submit(self.eng.extract_audio, s, i) for i, s in enumerate(songs)]
            for f in concurrent.futures.as_completed(futs):
                p, m = f.result()
                if p: down.append((p, m))
                else: errors.append(m)

        if not down: return None, errors[0] if errors else "Blocked"
        sf = self.arch.resolve_assembly(down, self.data.get('vibe', 'ocean_mist'), ai)
        master = self.mix_agent.mix(sf, self.sid, self.data.get('audioAdjustments', {}), ai)
        if not master: return None, "Mix Failure"
        out = os.path.join(TEMP_DIR, f"master_{self.sid}.mp3")
        master.export(out, format="mp3", bitrate="192k")
        return out, None

# --- WEB LAYER ---
app = Flask(__name__)
CORS(app)

@app.route('/')
def status():
    h = MaintenanceAgent().check_health()
    return jsonify({'status': 'AGENCY SYSTEM OPERATIONAL', 'version': '5.0.Agentic', 'details': h})

@app.route('/generate_mashup', methods=['POST'])
def generate_mashup():
    try:
        d = request.json
        if not d: return jsonify({'details': 'No JSON'}), 400
        pm = PMAgent(d)
        p, e = pm.run_synthesis()
        if e: return jsonify({'details': e}), 500
        return send_file(p, mimetype="audio/mpeg", as_attachment=True, download_name="Masterpiece.mp3")
    except Exception as ex:
        log_p = os.path.join(PROJECT_ROOT, "error_log.txt")
        with open(log_p, "a") as f:
            f.write(f"\n--- ERROR {time.ctime()} ---\n")
            f.write(traceback.format_exc())
        return jsonify({"details": str(ex), "trace": traceback.format_exc()}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
