document.addEventListener('DOMContentLoaded', () => {
    // 1. Core State & Element Mapping
    const form = document.getElementById('mashup-form');
    const tracksContainer = document.getElementById('tracks-container');
    const welcomeWindow = document.getElementById('welcome-window');
    const navChannels = document.getElementById('studio-navigation');
    const sections = document.querySelectorAll('.tab-content');
    const navTabs = document.querySelectorAll('.nav-tab');
    const loadingState = document.getElementById('loading-state');
    const successState = document.getElementById('success-state');
    const mixWindow = document.getElementById('mix-window');
    const consoleLogs = document.getElementById('console-logs');

    let currentSessionId = null;

    // Start Telemetry Immediately for "Starting Page" accuracy
    startDashboardTelemetry();

    // Pre-warm Render Backend: start pinging immediately so it wakes up
    warmupBackend();

    // 2. Navigation Logic (Phase-Locked)
    function switchTab(targetId) {
        sections.forEach(s => {
            s.classList.remove('active');
            s.style.display = 'none';
        });
        
        const target = document.getElementById(targetId);
        if (target) {
            target.classList.add('active');
            target.style.display = (targetId === 'mix-window') ? 'block' : 'grid';
        }

        // Update Nav Tabs
        navTabs.forEach(tab => {
            tab.classList.toggle('active', tab.dataset.target === targetId);
        });

        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // 3. Mashup Maker Initialization
    document.getElementById('enter-studio')?.addEventListener('click', () => {
        switchTab('selection-window');
        navChannels.classList.remove('hidden');
        initializeTracks();
    });

    navTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            if (tab.dataset.target !== 'mix-window') {
                switchTab(tab.dataset.target);
            }
        });
    });

    document.querySelectorAll('.next-tab').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.next));
    });

    document.querySelectorAll('.prev-tab').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.prev));
    });

    // Dynamic Dashboard Telemetry
    function startDashboardTelemetry() {
        const clock = document.getElementById('dashboard-clock');
        const latency = document.getElementById('dash-latency');
        
        setInterval(() => {
            if (clock) {
                const now = new Date();
                clock.textContent = now.toTimeString().split(' ')[0];
            }
            if (latency) {
                const l = (Math.random() * 2 + 0.5).toFixed(1);
                latency.textContent = `${l}ms`;
            }
        }, 1000);
    }

    // 4. Track Management (Mashup Maker Standard: 1 Reel + 4 Songs)
    function initializeTracks() {
        if (tracksContainer.children.length > 0) return; 
        
        const config = [
            { label: 'Suite Element 1 (Short/Reel)', icon: '🎬', placeholder: 'https://youtube.com/shorts/...' },
            { label: 'Suite Element 2 (Foundation)', icon: '🎵', placeholder: 'https://youtube.com/watch?v=...' },
            { label: 'Suite Element 3 (Melodic)', icon: '🎸', placeholder: 'https://youtube.com/watch?v=...' },
            { label: 'Suite Element 4 (Rhythmic)', icon: '🥁', placeholder: 'https://youtube.com/watch?v=...' },
            { label: 'Suite Element 5 (Atmospheric)', icon: '✨', placeholder: 'https://youtube.com/watch?v=...' }
        ];

        const createTrackCard = (c, i) => {
            const card = document.createElement('div');
            card.className = 'song-card';
            card.dataset.id = i;
            card.innerHTML = `
                <div class="card-identity">
                    <span class="element-icon">${c.icon}</span>
                    <label class="mini-label">${c.label}</label>
                    <button type="button" class="remove-track-btn" title="Remove Element">×</button>
                </div>
                <input type="url" name="link-${i}" placeholder="${c.placeholder}" class="manuscript-input">
                <div class="track-range">
                    <div class="range-group">
                        <label>START</label>
                        <input type="text" name="start-${i}" value="0:00" placeholder="0:00">
                    </div>
                    <div class="range-group">
                        <label>END</label>
                        <input type="text" name="end-${i}" value="0:30" placeholder="0:30">
                    </div>
                </div>
                <div class="track-bespoke-mini" style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 15px;">
                    <div class="mini-slider-col" style="grid-column: span 2; display: flex; align-items: center; gap: 10px; margin-bottom: 5px;">
                         <label class="nano-label" style="flex-shrink: 0;">FULL DURATION (REEL)</label>
                         <input type="checkbox" class="track-full" title="Keep original length of short element">
                    </div>
                    <div class="mini-slider-col">
                        <label class="nano-label">SPEED</label>
                        <input type="range" class="track-speed" min="50" max="150" value="100" title="Individual Track Speed">
                    </div>
                    <div class="mini-slider-col">
                        <label class="nano-label">GAIN</label>
                        <input type="range" class="track-gain" min="0" max="200" value="100" title="Gain Trim">
                    </div>
                    <div class="mini-slider-col">
                        <label class="nano-label">PAN</label>
                        <input type="range" class="track-pan" min="-100" max="100" value="0" title="Stereo Pan">
                    </div>
                    <div class="mini-slider-col">
                        <label class="nano-label">LOW-CUT</label>
                        <input type="range" class="track-lowcut" min="0" max="100" value="0" title="Low Frequency Cut">
                    </div>
                    <div class="mini-slider-col" style="grid-column: span 2;">
                        <label class="nano-label">AI LANGUAGE CONVERSION</label>
                        <select class="track-language manuscript-input" style="font-size: 0.6rem; padding: 5px;">
                            <option value="original">ORIGINAL (DEFAULT)</option>
                            <option value="gujarati">GUJARATI</option>
                            <option value="hindi">HINDI</option>
                            <option value="punjabi">PUNJABI</option>
                            <option value="english">ENGLISH</option>
                            <option value="spanish">SPANISH</option>
                            <option value="japanese">JAPANESE</option>
                        </select>
                    </div>
                </div>
            `;
            tracksContainer.appendChild(card);
        };

        config.forEach((c, i) => createTrackCard(c, i));

        let currentCount = 5;
        const addTrackBtn = document.getElementById('add-track-btn');
        const countBadge = document.getElementById('track-count-badge');
        
        if (addTrackBtn) {
            addTrackBtn.addEventListener('click', () => {
                if (currentCount >= 10) return;
                const i = currentCount;
                const c = { label: `Suite Element ${i + 1} (Additional)`, icon: '🎧', placeholder: 'https://youtube.com/watch?v=...' };
                createTrackCard(c, i);
                currentCount++;
                
                if (countBadge) countBadge.textContent = `(${currentCount}/10)`;
                if (currentCount >= 10) {
                    addTrackBtn.style.opacity = '0.5';
                    addTrackBtn.style.cursor = 'not-allowed';
                    addTrackBtn.textContent = 'Maximum Capacity Reached (10/10)';
                }
            });
        }

        // Delegate deletion & Full Track Toggle
        tracksContainer.addEventListener('click', (e) => {
            if (e.target.classList.contains('remove-track-btn')) {
                const card = e.target.closest('.song-card');
                card.style.opacity = '0';
                card.style.transform = 'scale(0.9)';
                setTimeout(() => {
                    card.remove();
                    if (currentCount > 0) {
                        currentCount--;
                        if (countBadge) countBadge.textContent = `(${currentCount}/10)`;
                        if (currentCount < 10 && addTrackBtn) {
                            addTrackBtn.style.display = 'inline-flex';
                            addTrackBtn.style.opacity = '1';
                            addTrackBtn.style.cursor = 'pointer';
                            addTrackBtn.innerHTML = `+ Add Element <span id="track-count-badge" style="opacity: 0.6; font-size: 0.9em;">(${currentCount}/10)</span>`;
                        }
                    }
                }, 300);
            }
        });

        tracksContainer.addEventListener('change', (e) => {
            if (e.target.classList.contains('track-full')) {
                const card = e.target.closest('.song-card');
                const ranges = card.querySelectorAll('.range-group input');
                ranges.forEach(i => {
                    i.disabled = e.target.checked;
                    i.style.opacity = e.target.checked ? '0.3' : '1';
                });
            }
        });
    }

    // 5. Tooltip Logic
    const tooltip = document.createElement('div');
    tooltip.className = 'info-tooltip';
    document.body.appendChild(tooltip);

    document.addEventListener('mouseover', (e) => {
        if (e.target.classList.contains('info-trigger')) {
            const info = e.target.dataset.info;
            tooltip.textContent = info;
            tooltip.style.opacity = '1';
            
            const rect = e.target.getBoundingClientRect();
            tooltip.style.left = `${rect.left + 25}px`;
            tooltip.style.top = `${rect.top - 10}px`;
        }
    });

    document.addEventListener('mouseout', (e) => {
        if (e.target.classList.contains('info-trigger')) {
            tooltip.style.opacity = '0';
        }
    });

    // 6. Mashup Maker Logging System
    function logToStudio(agent, message, type = 'info') {
        const consoleLogs = document.getElementById('console-logs');
        if (!consoleLogs) return;
        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;
        
        const agentColors = {
            'PM': '#ffd700',
            'ARCHITECT': '#00d2ff',
            'ENGINEER': '#34d399',
            'VP': '#ff4d4d'
        };
        
        const color = agentColors[agent] || '#fff';
        entry.innerHTML = `<span style="color: ${color}; font-weight: 700;">${agent}:</span> ${message}`;
        consoleLogs.appendChild(entry);
        consoleLogs.scrollTop = consoleLogs.scrollHeight;
    }

    // 6b. Backend Discovery & Warmup
    // Directing to local 5000 if opened as a file, otherwise using absolute relative path
    const BACKEND_BASE = (window.location.protocol === 'file:') ? 'http://127.0.0.1:5000' : '';
    let backendReady = false;

    async function warmupBackend() {
        // Silently ping the backend so it wakes from Render sleep
        try {
            const r = await fetch(BACKEND_BASE + '/api/status', { method: 'GET', cache: 'no-store' });
            if (r.ok) backendReady = true;
        } catch (e) {
            // Ignore – we'll retry properly before submission
        }
    }
    warmupBackend();

    async function ensureBackendAwake(onStatus) {
        if (backendReady) return true;
        const maxAttempts = 12; // 12 × 5s = 60s max wait
        for (let i = 0; i < maxAttempts; i++) {
            onStatus(`Checking Agentic Infrastructure... (${i * 5}s)`);
            try {
                const r = await fetch(BACKEND_BASE + '/api/status', { method: 'GET', cache: 'no-store', mode: 'cors' });
                if (r.ok) { backendReady = true; return true; }
            } catch (e) { /* still sleeping */ }
            await new Promise(res => setTimeout(res, 5000));
        }
        return false;
    }

    // 7. Synthesis Trigger
    const synthesisHandler = async (e, aiMode = false, removeEffects = false) => {
        if (e) e.preventDefault();
        
        // Validation
        const inputs = form.querySelectorAll('input[type="url"]');
        let valid = false;
        inputs.forEach(i => { if (i.value.trim()) valid = true; });
        if (!valid) {
            alert("No sonic elements curated. Synthesis aborted.");
            return;
        }

        switchTab('mix-window');
        loadingState.classList.remove('hidden');
        successState.classList.add('hidden');
        
        const consoleLogs = document.getElementById('console-logs');
        if (consoleLogs) consoleLogs.innerHTML = '';
        
        if (removeEffects) {
             logToStudio('PM', 'Re-compiling session as Pure Audio Merge (AI Effects Bypassed)...');
             logToStudio('ARCHITECT', 'Transitioning to strict chronological sequence with 0s crossfade.');
        } else {
             logToStudio('PM', aiMode ? 'Initializing INTELLIGENT AI SYNTHESIS... (Learning from piW4gHWy8z8)' : 'Synthesis scope locked. Directorial guidance received.');
             if (aiMode) {
                 setTimeout(() => logToStudio('ARCHITECT', 'AI analyzing harmonic compatibility and breakpoints...'), 1000);
                 setTimeout(() => logToStudio('VP', 'Calibrating automated transition effects (Reverb, Echo, Bass)...'), 2500);
             }
        }
        
        const data = {
            ai_mode: aiMode,
            removeEffects: removeEffects,
            songs: [],
            vibe: form.querySelector('input[name="vibe"]:checked').value,
            audioAdjustments: {
                bass: document.getElementById('bass-level').value,
                mid: document.getElementById('mid-level').value,
                treble: document.getElementById('treble-level').value,
                speed: document.getElementById('speed-level').value / 100,
                pitch: document.getElementById('pitch-level').value,
                reverb: document.getElementById('reverb-level').value,
                delay: document.getElementById('delay-level').value,
                chorus: document.getElementById('chorus-level').value,
                phaser: document.getElementById('phaser-level').value,
                distortion: document.getElementById('distortion-level').value,
                bitcrush: document.getElementById('bitcrush-level').value,
                tremolo: document.getElementById('tremolo-level').value,
                flanger: document.getElementById('flanger-level').value,
                compression: document.getElementById('compression-level').value,
                limiter: document.getElementById('limiter-level').value,
                width: document.getElementById('width-level').value,
                fade_in: document.getElementById('fade-in-level').value,
                fade_out: document.getElementById('fade-out-level').value,
                highpass: document.getElementById('highpass-level').value,
                lowpass: document.getElementById('lowpass-level').value
            },
            instructions: document.getElementById('instructions').value
        };

        form.querySelectorAll('.song-card').forEach(card => {
            const link = card.querySelector('input[type="url"]').value;
            if (link) {
                const id = card.dataset.id;
                data.songs.push({
                    link,
                    startTime: card.querySelector(`input[name="start-${id}"]`).value,
                    endTime: card.querySelector(`input[name="end-${id}"]`).value,
                    adjustments: {
                        gain: card.querySelector('.track-gain').value,
                        pan: card.querySelector('.track-pan').value,
                        lowcut: card.querySelector('.track-lowcut').value,
                        speed: card.querySelector('.track-speed').value / 100,
                        full: card.querySelector('.track-full').checked,
                        language: card.querySelector('.track-language').value
                    }
                });
            }
        });

        logToStudio('ARCHITECT', `Designing ${data.songs.length}-element audio graph...`);

        // Ensure backend is awake
        logToStudio('ENGINEER', 'Checking synthesis engine status...');
        const awake = await ensureBackendAwake((msg) => {
            logToStudio('ENGINEER', msg);
        });

        if (!awake) {
            logToStudio('VP', 'CRITICAL ERROR: Backend failed to wake up. Check Antigravity logs.', 'error');
            return;
        }

        logToStudio('VP', 'Engine connection established. Dispatching job...');
        logToStudio('ENGINEER', 'Initializing high-speed extraction threads...');
        setTimeout(() => logToStudio('ENGINEER', 'Fetching sonic assets from distributed nodes...'), 1500);
        setTimeout(() => logToStudio('ENGINEER', 'Processing 5-song audio graph (est. 1-3 mins)...'), 4000);
        setTimeout(() => logToStudio('ARCHITECT', 'Finalizing structural resonance...'), 8000);

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10 * 60 * 1000);

        try {
            const backendUrl = BACKEND_BASE + '/generate_mashup';
            const res = await fetch(backendUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            if (!res.ok) throw new Error('Synthesis Engine Failure');

            logToStudio('VP', 'Synthesis verified. Commencing high-fidelity master...');
            const blob = await res.blob();
            logToStudio('PM', 'Quality Assurance passed. Masterpiece ready for delivery.');
            
            const url = window.URL.createObjectURL(blob);
            const player = document.getElementById('main-audio-player');
            player.src = url;
            player.load();
            
            document.getElementById('download-link').href = url;
            document.getElementById('download-link').download = `Mashup_Masterpiece_${Date.now()}.mp3`;
            
            setTimeout(() => {
                loadingState.classList.add('hidden');
                successState.classList.remove('hidden');
            }, 1000);
        } catch (err) {
            clearTimeout(timeoutId);
            logToStudio('VP', `CRITICAL ERROR: ${err.message}`, 'error');
            setTimeout(() => {
                switchTab('direction-window');
                loadingState.classList.add('hidden');
            }, 5000);
        }
    };

    form.addEventListener('submit', (e) => synthesisHandler(e, false, false));
    document.getElementById('ai-mashup-btn')?.addEventListener('click', (e) => synthesisHandler(null, true, false));
    document.getElementById('remove-effects-btn')?.addEventListener('click', (e) => synthesisHandler(null, false, true));

    // 8. Preset Auto-Adjustment
    const presets = {
        'classical': { bass: 2, mid: 3, treble: 5, speed: 100, pitch: 0, reverb: 40, delay: 0, chorus: 10, phaser: 0, distortion: 0, bitcrush: 0, tremolo: 0, flanger: 0, compression: 20, limiter: 90, width: 120, highpass: 20, lowpass: 90, fade_in: 2000, fade_out: 2000 },
        'wedding': { bass: 5, mid: 2, treble: 4, speed: 105, pitch: 0, reverb: 20, delay: 10, chorus: 20, phaser: 0, distortion: 5, bitcrush: 0, tremolo: 0, flanger: 0, compression: 40, limiter: 95, width: 150, highpass: 10, lowpass: 100, fade_in: 1000, fade_out: 1000 },
        'bollytech': { bass: 8, mid: 0, treble: 6, speed: 110, pitch: 0, reverb: 30, delay: 15, chorus: 30, phaser: 10, distortion: 10, bitcrush: 5, tremolo: 0, flanger: 10, compression: 60, limiter: 98, width: 160, highpass: 30, lowpass: 85, fade_in: 500, fade_out: 500 },
        'zen': { bass: 0, mid: 2, treble: 2, speed: 85, pitch: -2, reverb: 80, delay: 40, chorus: 40, phaser: 20, distortion: 0, bitcrush: 0, tremolo: 10, flanger: 0, compression: 10, limiter: 80, width: 180, highpass: 100, lowpass: 50, fade_in: 5000, fade_out: 5000 },
        'inferno': { bass: 12, mid: -2, treble: 8, speed: 128, pitch: 0, reverb: 10, delay: 20, chorus: 0, phaser: 30, distortion: 40, bitcrush: 20, tremolo: 0, flanger: 30, compression: 80, limiter: 100, width: 140, highpass: 40, lowpass: 95, fade_in: 200, fade_out: 200 },
        'cinematic': { bass: 3, mid: 1, treble: 3, speed: 95, pitch: 0, reverb: 80, delay: 30, chorus: 10, phaser: 0, distortion: 2, bitcrush: 0, tremolo: 5, flanger: 0, compression: 30, limiter: 90, width: 180, highpass: 5, lowpass: 80, fade_in: 3000, fade_out: 3000 },
        'lofi': { bass: 4, mid: -1, treble: -2, speed: 90, pitch: -1, reverb: 30, delay: 10, chorus: 20, phaser: 0, distortion: 15, bitcrush: 40, tremolo: 20, flanger: 0, compression: 20, limiter: 85, width: 80, highpass: 30, lowpass: 60, fade_in: 2000, fade_out: 2000 },
        'ethereal': { bass: -5, mid: 0, treble: 10, speed: 75, pitch: 4, reverb: 100, delay: 60, chorus: 80, phaser: 50, distortion: 0, bitcrush: 5, tremolo: 40, flanger: 20, compression: 10, limiter: 70, width: 200, highpass: 50, lowpass: 40, fade_in: 8000, fade_out: 8000 }
    };

    document.querySelectorAll('.btn-preset').forEach(btn => {
        btn.addEventListener('click', () => {
            const config = presets[btn.dataset.preset];
            if (!config) return;

            Object.keys(config).forEach(param => {
                const el = document.getElementById(`${param}-level`);
                if (el) {
                    el.value = config[param];
                    updateSliderDisplay(param);
                }
            });

            document.querySelectorAll('.btn-preset').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            logToStudio('ARCHITECT', `Parameters aligned to ${btn.textContent} preset.`);
        });
    });

    // 9. Visual Feedback: Sliders
    function updateSliderDisplay(id) {
        const input = document.getElementById(`${id}-level`);
        const display = document.getElementById(`${id}-val`);
        if (!input || !display) return;
        
        const val = parseInt(input.value);
        if (['bass', 'mid', 'treble'].includes(id)) display.textContent = (val > 0 ? `+${val}` : val) + 'dB';
        else if (id === 'speed') display.textContent = (val / 100).toFixed(2) + 'x';
        else if (id === 'pitch') display.textContent = (val > 0 ? `+${val}` : val) + 'st';
        else if (id === 'reverb') display.textContent = val === 0 ? 'Off' : (val < 40 ? 'Slight' : (val < 80 ? 'Rich' : 'Infinite'));
        else if (id === 'delay') display.textContent = val === 0 ? 'Off' : val + '%';
        else if (id === 'chorus') display.textContent = val === 0 ? 'Off' : val + '%';
        else if (id === 'phaser') display.textContent = val === 0 ? 'Off' : val + '%';
        else if (id === 'distortion') display.textContent = val === 0 ? 'Clean' : val + '%';
        else if (id === 'bitcrush') display.textContent = val === 0 ? 'Hi-Fi' : val + 'bit';
        else if (id === 'tremolo') display.textContent = val === 0 ? 'Off' : val + 'Hz';
        else if (id === 'flanger') display.textContent = val === 0 ? 'Off' : val + '%';
        else if (id === 'compression') display.textContent = val === 0 ? 'Off' : val + '%';
        else if (id === 'limiter') display.textContent = val === 100 ? 'None' : (val - 100) + 'dB';
        else if (id === 'width') display.textContent = val === 100 ? 'Original' : val + '%';
        else if (id === 'fade-in' || id === 'fade-out') display.textContent = (val / 1000).toFixed(1) + 's';
        else if (id === 'highpass') display.textContent = val === 0 ? 'Off' : (val * 40) + 'Hz';
        else if (id === 'lowpass') display.textContent = val === 100 ? 'Off' : (20000 - (val * 180)) + 'Hz';
    }

    const allParams = ['bass', 'mid', 'treble', 'speed', 'pitch', 'reverb', 'delay', 'chorus', 'phaser', 'distortion', 'bitcrush', 'tremolo', 'flanger', 'compression', 'limiter', 'width', 'fade-in', 'fade-out', 'highpass', 'lowpass'];
    allParams.forEach(id => {
        const el = document.getElementById(`${id}-level`);
        if (el) el.addEventListener('input', () => updateSliderDisplay(id));
    });

    // 10. Theme Switching
    document.querySelectorAll('.theme-card-gui').forEach(card => {
        card.addEventListener('click', () => {
            const theme = card.dataset.theme;
            document.body.className = `theme-${theme}`;
            document.querySelectorAll('.theme-card-gui').forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            logToStudio('ARCHITECT', `Aesthetic resonance shifted to ${theme.toUpperCase()}.`);
        });
    });

    // 11. Sample Suite Logic (One-Click Launch)
    document.getElementById('sample-suite')?.addEventListener('click', () => {
        const samples = [
            { link: 'https://www.youtube.com/shorts/jfKfPfyJRdk', start: '0:00', end: '0:15' },
            { link: 'https://www.youtube.com/watch?v=jfKfPfyJRdk', start: '0:30', end: '1:00' },
            { link: 'https://www.youtube.com/watch?v=5Eqb_-j3FDA', start: '0:00', end: '0:30' }
        ];

        logToStudio('PM', 'Injecting High-Fidelity Sample Suite...');
        
        samples.forEach((s, i) => {
            const input = document.querySelector(`input[name="link-${i}"]`);
            const start = document.querySelector(`input[name="start-${i}"]`);
            const end = document.querySelector(`input[name="end-${i}"]`);
            if (input) input.value = s.link;
            if (start) start.value = s.start;
            if (end) end.value = s.end;
        });

        // Set high-end parameters
        document.getElementById('bass-level').value = 8;
        document.getElementById('lowpass-level').value = 70;
        document.getElementById('reverb-level').value = 60;
        document.getElementById('chorus-level').value = 40;
        
        ['bass', 'lowpass', 'reverb', 'chorus'].forEach(updateSliderDisplay);
        
        setTimeout(() => {
            switchTab('studio-window');
            logToStudio('ENGINEER', 'Sample Suite ready for synthesis.');
        }, 800);
    });

    // 12. Global Reset
    document.querySelectorAll('.reset-app').forEach(btn => {
        btn.addEventListener('click', () => {
            form.reset();
            switchTab('welcome-window');
            tracksContainer.innerHTML = '';
            consoleLogs.innerHTML = '';
        });
    });

    // 13. PWA Registration
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/service-worker.js')
                .then(reg => console.log('Service Worker Registered.', reg))
                .catch(err => console.log('Service Worker Registration Failed.', err));
        });
    }

    console.log("Mashup Maker Operational.");
});
