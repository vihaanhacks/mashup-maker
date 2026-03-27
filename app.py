import os
import sys
import uuid
import subprocess
import concurrent.futures
import traceback
import math
import re
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

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)


@app.route('/')
def index():
    return jsonify({'status': 'System Operational', 'version': '3.0'})


def parse_time(t_str):
    if not t_str:
        return 0
    try:
        t_str = str(t_str).strip()
        parts = t_str.split(':')
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        return int(float(parts[0]))
    except Exception:
        return 0


def download_track(track, idx, session_id):
    url = track.get('link', '').strip()
    if not url:
        return None, "No URL provided"

    adj = track.get('adjustments', {})
    is_full = bool(adj.get('full', False))
    speed = float(adj.get('speed', 1.0))
    # Gain comes as 0-200 (percent), convert to 0-2.0
    gain_raw = adj.get('gain', 100)
    try:
        gain_val = float(gain_raw) / 100.0
    except Exception:
        gain_val = 1.0

    start_sec = parse_time(track.get('startTime', '0:00'))
    end_sec = parse_time(track.get('endTime', '0:30'))
    dur = max(5, end_sec - start_sec) if end_sec > start_sec else 30

    out_path = os.path.join(DOWNLOADS_DIR, f"{session_id}_{idx}.mp3")

    # yt-dlp options - multiple format strategies to handle YouTube blocking
    ydl_opts_list = [
        # Strategy 1: audio-only formats
        {
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'format': 'bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio/best',
            'youtube_include_dash_manifest': False,
        },
        # Strategy 2: best overall with video (ffmpeg strips video)
        {
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'format': 'best[height<=480]/best',
            'youtube_include_dash_manifest': False,
        },
    ]

    audio_url = None
    info = None

    for ydl_opts in ydl_opts_list:
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                # Pick the best audio stream URL
                chosen_fmt = None
                fmts = info.get('formats', [])
                # Prefer audio-only
                audio_only = [f for f in fmts if f.get('acodec') not in (None, 'none') and f.get('vcodec') in (None, 'none')]
                if audio_only:
                    chosen_fmt = max(audio_only, key=lambda f: f.get('abr') or f.get('tbr') or 0)
                else:
                    valid = [f for f in fmts if f.get('url') and f.get('acodec') not in (None, 'none')]
                    if valid:
                        chosen_fmt = max(valid, key=lambda f: f.get('abr') or f.get('tbr') or 0)

                if chosen_fmt and chosen_fmt.get('url'):
                    audio_url = chosen_fmt['url']
                    print(f"[{idx}] Got stream URL via strategy, format: {chosen_fmt.get('ext', '?')}", flush=True)
                    break
        except Exception as e:
            print(f"[{idx}] yt-dlp strategy failed: {e}", flush=True)
            continue

    if not audio_url:
        # Last resort: try full download with yt-dlp directly to file
        try:
            out_raw = os.path.join(DOWNLOADS_DIR, f"{session_id}_{idx}_raw")
            ydl_download_opts = {
                'quiet': False,
                'no_warnings': False,
                'nocheckcertificate': True,
                'format': 'bestaudio/best',
                'outtmpl': out_raw + '.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '128',
                }],
                'postprocessor_args': ['-ss', str(start_sec), '-t', str(dur)] if not is_full else [],
            }
            with yt_dlp.YoutubeDL(ydl_download_opts) as ydl:
                ydl.download([url])
            # Find the output file
            for ext in ['mp3', 'webm', 'm4a', 'opus']:
                candidate = out_raw + '.' + ext
                if os.path.exists(candidate) and os.path.getsize(candidate) > 0:
                    os.rename(candidate, out_path)
                    print(f"[{idx}] Downloaded directly to file: {out_path}", flush=True)
                    return out_path, track
            return None, "Direct download produced no output file"
        except Exception as e:
            traceback.print_exc()
            return None, f"All download strategies failed: {str(e)}"

    # Build FFmpeg command using streamed URL
    try:
        cmd = [FFMPEG_PATH, '-y']
        if not is_full:
            cmd += ['-ss', str(start_sec), '-t', str(dur)]
        cmd += [
            '-i', audio_url,
            '-vn',
            '-acodec', 'libmp3lame',
            '-ab', '128k',
            '-ar', '44100',
        ]
        if speed != 1.0:
            # Clamp speed to valid atempo range
            clamped = max(0.5, min(2.0, speed))
            cmd += ['-filter:a', f'atempo={clamped}']
        cmd.append(out_path)

        print(f"[{idx}] Running FFmpeg: {' '.join(cmd[:6])}...", flush=True)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            print(f"[{idx}] FFmpeg stderr:\n{result.stderr[-1000:]}", flush=True)
            raise RuntimeError(f"FFmpeg exit {result.returncode}")

        if not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
            raise RuntimeError("FFmpeg output is empty or missing")

        print(f"[{idx}] OK: {os.path.getsize(out_path)} bytes", flush=True)
        return out_path, track

    except subprocess.TimeoutExpired:
        return None, f"FFmpeg timed out for track {idx}"
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
        print(f"[SESSION {session_id}] Starting mashup for {len(songs)} tracks", flush=True)

        downloaded = []
        errors = []

        # Download all tracks in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(download_track, t, i, session_id): i
                       for i, t in enumerate(songs)}
            for future in concurrent.futures.as_completed(futures):
                path, res = future.result()
                if path:
                    downloaded.append((path, res))
                    print(f"Track downloaded: {path}", flush=True)
                else:
                    errors.append(str(res))
                    print(f"Track failed: {res}", flush=True)

        if not downloaded:
            return jsonify({
                'details': 'Synthesis Engine Failure: Could not process any tracks.',
                'errors': errors
            }), 500

        print(f"[SESSION {session_id}] Assembling {len(downloaded)} tracks", flush=True)

        # Sort downloaded by original order (path contains idx)
        def get_idx(item):
            name = os.path.basename(item[0])
            m = re.search(r'_(\d+)\.mp3$', name)
            return int(m.group(1)) if m else 999
        downloaded.sort(key=get_idx)

        # Assemble the mashup
        master = None
        for path, track_info in downloaded:
            try:
                s = AudioSegment.from_mp3(path)
                print(f"Loaded segment: {len(s)}ms", flush=True)

                # Smooth fades
                fade_ms = min(1000, len(s) // 4)
                s = s.fade_in(fade_ms).fade_out(fade_ms)

                # Apply gain
                adj = track_info.get('adjustments', {})
                gain_raw = adj.get('gain', 100)
                try:
                    gain_val = float(gain_raw) / 100.0
                except Exception:
                    gain_val = 1.0

                if gain_val <= 0:
                    db_change = -100
                else:
                    db_change = 10 * math.log10(max(0.001, gain_val))
                s = s + db_change

                # Apply pan
                try:
                    pan_val = float(adj.get('pan', 0)) / 100.0
                    pan_val = max(-1.0, min(1.0, pan_val))
                    s = s.pan(pan_val)
                except Exception:
                    pass

                if master is None:
                    print(f"[{path}] Initializing master track", flush=True)
                    master = s
                else:
                    cf = min(3000, len(master) // 4, len(s) // 4)
                    print(f"[{path}] Appending to master with {cf}ms crossfade", flush=True)
                    master = master.append(s, crossfade=max(0, cf))
                    print(f"[{path}] Master now: {len(master)}ms", flush=True)

            except Exception as e:
                print(f"Mix error for {path}: {e}", flush=True)
                traceback.print_exc()

        if master is None:
            return jsonify({'details': 'Final assembly failed: no segments could be loaded.'}), 500

        out_path = os.path.join(TEMP_DIR, f"master_{session_id}.mp3")
        print(f"Exporting master ({len(master)}ms) to {out_path}", flush=True)
        master.export(out_path, format="mp3", bitrate="192k")

        print(f"[SESSION {session_id}] Done! File size: {os.path.getsize(out_path)} bytes", flush=True)
        return send_file(out_path, mimetype="audio/mpeg", as_attachment=True, download_name="Masterpiece.mp3")

    except Exception as e:
        traceback.print_exc()
        return jsonify({'details': f"Systemic failure: {str(e)}"}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0' if os.environ.get('RENDER') else '127.0.0.1'
    app.run(host=host, port=port, debug=False)
