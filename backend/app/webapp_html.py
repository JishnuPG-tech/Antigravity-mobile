HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Antigravity Web Console</title>
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=block" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {
            /* Theme Green Matrix (default) */
            --bg-base: #000000;
            --term-bg: #020402;
            --text-color: #39FF14;
            --accent-color: #00ff9c;
            --border-color: rgba(57, 255, 20, 0.2);
            --panel-bg: #0e1418;
            --btn-bg: rgba(57, 255, 20, 0.05);
            --glow-color: rgba(0, 255, 156, 0.3);
            --on-surface: #dde3e9;
            --text-secondary: #8e8e9f;
        }

        /* Tokyo Night Theme */
        [data-theme="tokyo"] {
            --bg-base: #1a1b26;
            --term-bg: #16161e;
            --text-color: #7aa2f7;
            --accent-color: #bb9af3;
            --border-color: #292e42;
            --panel-bg: #16161e;
            --btn-bg: rgba(187, 154, 243, 0.08);
            --glow-color: rgba(187, 154, 243, 0.3);
            --on-surface: #a9b1d6;
            --text-secondary: #565f89;
        }

        /* Solarized Dark Theme */
        [data-theme="solarized"] {
            --bg-base: #00212b;
            --term-bg: #073642;
            --text-color: #93a1a1;
            --accent-color: #2aa198;
            --border-color: #586e75;
            --panel-bg: #073642;
            --btn-bg: rgba(42, 161, 152, 0.08);
            --glow-color: rgba(42, 161, 152, 0.3);
            --on-surface: #93a1a1;
            --text-secondary: #586e75;
        }

        /* Amber CRT Theme */
        [data-theme="amber"] {
            --bg-base: #000000;
            --term-bg: #080500;
            --text-color: #FFB000;
            --accent-color: #FFB000;
            --border-color: #3d2a00;
            --panel-bg: #0f0a00;
            --btn-bg: rgba(255, 176, 0, 0.05);
            --glow-color: rgba(255, 176, 0, 0.3);
            --on-surface: #ffda79;
            --text-secondary: #845e00;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            user-select: none;
            -webkit-user-select: none;
        }

        body {
            font-family: 'Geist', sans-serif;
            background: var(--bg-base);
            color: var(--on-surface);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            transition: background 0.3s, color 0.3s;
        }

        /* CRT Scanline Overlay */
        .scanline {
            width: 100%;
            height: 100%;
            z-index: 100;
            background: linear-gradient(0deg, rgba(0, 0, 0, 0) 50%, rgba(255, 255, 255, 0.02) 50%);
            background-size: 100% 4px;
            pointer-events: none;
            position: fixed;
            top: 0;
            left: 0;
        }

        /* System Dashboard Header */
        .dashboard-header {
            background-color: rgba(14, 20, 24, 0.7);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border-bottom: 1px solid var(--border-color);
            padding: 10px 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 10;
        }

        .dashboard-metrics {
            display: flex;
            gap: 20px;
            overflow-x: auto;
        }

        .metric-col {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .metric-label {
            font-size: 10px;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .metric-value {
            font-size: 12px;
            font-weight: bold;
            color: var(--accent-color);
            display: flex;
            align-items: center;
            gap: 4px;
            font-family: 'JetBrains Mono', monospace;
        }

        .load-bar-bg {
            width: 50px;
            height: 6px;
            background-color: rgba(255, 255, 255, 0.05);
            border-radius: 3px;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .load-bar-fill {
            height: 100%;
            background-color: var(--accent-color);
            box-shadow: 0 0 6px var(--accent-color);
            width: 42%;
            transition: width 0.5s ease;
        }

        .status-badge {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 4px 8px;
            background-color: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            font-size: 10px;
            font-weight: bold;
            text-transform: uppercase;
        }

        .status-dot {
            width: 6px;
            height: 6px;
            background-color: var(--text-color);
            border-radius: 50%;
            box-shadow: 0 0 8px var(--text-color);
            animation: pulse-glow 1.5s infinite;
        }

        @keyframes pulse-glow {
            0% { transform: scale(0.9); opacity: 0.6; }
            50% { transform: scale(1.1); opacity: 1; }
            100% { transform: scale(0.9); opacity: 0.6; }
        }

        /* Console View Container */
        .console-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            position: relative;
        }

        /* Terminal Window */
        .terminal-window {
            flex: 1;
            background-color: var(--bg-base);
            padding: 16px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
            line-height: 1.5;
            overflow-y: auto;
            white-space: pre-wrap;
            word-break: break-all;
            color: var(--text-color);
        }

        .cursor {
            display: inline-block;
            width: 8px;
            height: 15px;
            background-color: var(--text-color);
            margin-left: 2px;
            vertical-align: middle;
            box-shadow: 0 0 6px var(--text-color);
            animation: blink 1s step-start infinite;
        }

        @keyframes blink {
            50% { opacity: 0; }
        }

        /* Control Panel */
        .control-panel {
            padding: 12px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            background-color: var(--panel-bg);
            border-t: 1px solid var(--border-color);
        }

        .input-row {
            display: flex;
            gap: 8px;
        }

        .text-input {
            flex: 1;
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: var(--text-color);
            padding: 10px 14px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 14px;
            outline: none;
        }

        .text-input:focus {
            border-color: var(--accent-color);
            box-shadow: 0 0 8px var(--glow-color);
        }

        .btn-send {
            background: var(--accent-color);
            color: #000;
            border: none;
            border-radius: 8px;
            padding: 0 20px;
            font-weight: bold;
            cursor: pointer;
        }

        /* Keypad Accessory Bar */
        .keypad-row {
            display: flex;
            gap: 6px;
            overflow-x: auto;
            padding-bottom: 4px;
        }

        .key-btn {
            background-color: var(--btn-bg);
            border: 1px solid var(--border-color);
            color: var(--text-color);
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 11px;
            font-weight: bold;
            cursor: pointer;
            min-width: 50px;
            text-align: center;
        }

        .key-btn:active {
            background-color: var(--accent-color);
            color: #000;
        }

        /* Navigation Bar */
        nav {
            height: 56px;
            border-top: 1px solid var(--border-color);
            background-color: rgba(14, 20, 24, 0.9);
            display: flex;
            justify-content: space-around;
            align-items: center;
            padding-bottom: env(safe-area-inset-bottom);
        }

        .nav-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 9px;
            text-transform: uppercase;
            gap: 2px;
            cursor: pointer;
        }

        .nav-item.active {
            color: var(--accent-color);
            text-shadow: 0 0 6px var(--glow-color);
        }

        .nav-item .material-symbols-outlined {
            font-size: 20px;
        }

        /* Settings view overlay */
        .config-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: var(--panel-bg);
            z-index: 50;
            padding: 24px;
            display: none;
            flex-direction: column;
            gap: 16px;
        }

        .config-title {
            font-size: 20px;
            font-weight: bold;
            color: #FFF;
            margin-bottom: 12px;
        }

        .config-group {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .config-label {
            font-size: 12px;
            color: var(--text-secondary);
        }

        .config-input {
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: #FFF;
            padding: 10px;
            outline: none;
        }

        .theme-select {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .theme-btn {
            border: 1px solid var(--border-color);
            background-color: transparent;
            color: var(--text-secondary);
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 11px;
            cursor: pointer;
        }

        .theme-btn.active {
            border-color: var(--accent-color);
            background-color: var(--btn-bg);
            color: var(--accent-color);
        }

        .btn-save {
            background-color: var(--accent-color);
            color: #000;
            font-weight: bold;
            border: none;
            padding: 12px;
            border-radius: 8px;
            cursor: pointer;
            margin-top: 12px;
        }
    </style>
</head>
<body>
    <!-- CRT Scanline Effect -->
    <div class="scanline"></div>

    <!-- Top System Dashboard -->
    <section class="dashboard-header">
        <div class="dashboard-metrics">
            <div class="metric-col">
                <span class="metric-label">Active Model</span>
                <span class="metric-value">
                    <span class="material-symbols-outlined" style="font-size:12px;">neurology</span>
                    ANTIGRAVITY-1.5-PRO
                </span>
            </div>
            <div class="metric-col">
                <span class="metric-label">System Load</span>
                <div style="display:flex; align-items:center; gap:6px;">
                    <div class="load-bar-bg"><div class="load-bar-fill" id="load-fill"></div></div>
                    <span class="metric-value" style="font-size:10px;" id="load-text">42.8%</span>
                </div>
            </div>
            <div class="metric-col">
                <span class="metric-label">AI Latency</span>
                <span class="metric-value" id="latency-text">284ms</span>
            </div>
        </div>
        <div class="status-badge">
            <div class="status-dot"></div>
            <span>Stable</span>
        </div>
    </section>

    <!-- Main Views -->
    <div class="console-container">
        <!-- Terminal Window View -->
        <div class="terminal-window" id="terminal">Initializing tunnel connection...<span class="cursor"></span></div>

        <!-- Setup Profile View (Config Overlay) -->
        <div class="config-overlay" id="config-view">
            <div class="config-title">Profile Configuration</div>
            
            <div class="config-group">
                <label class="config-label">Telegram User ID</label>
                <input type="text" class="config-input" id="userid-input" value="1769298522">
            </div>

            <div class="config-group">
                <label class="config-label">Active Theme Color Mode</label>
                <div class="theme-select">
                    <button class="theme-btn active" onclick="setTheme('matrix', this)">Matrix Green</button>
                    <button class="theme-btn" onclick="setTheme('tokyo', this)">Tokyo Night</button>
                    <button class="theme-btn" onclick="setTheme('solarized', this)">Solarized Dark</button>
                    <button class="theme-btn" onclick="setTheme('amber', this)">Amber CRT</button>
                </div>
            </div>

            <button class="btn-save" onclick="applyProfileSettings()">Apply Configuration</button>
        </div>
    </div>

    <!-- Accessory Keypad Panel -->
    <div class="control-panel" id="control-panel">
        <div class="keypad-row">
            <button class="key-btn" onclick="sendKey('Tab')">TAB</button>
            <button class="key-btn" onclick="sendKey('Up')">UP (↑)</button>
            <button class="key-btn" onclick="sendKey('Down')">DOWN (↓)</button>
            <button class="key-btn" onclick="sendKey('Left')">LEFT (←)</button>
            <button class="key-btn" onclick="sendKey('Right')">RIGHT (→)</button>
            <button class="key-btn" onclick="sendKey('BSpace')">BKSP</button>
            <button class="key-btn" onclick="sendKey('Enter')">ENTER</button>
            <button class="key-btn" onclick="sendInterrupt()">CTRL+C</button>
            <button class="key-btn" onclick="launchAgy()">LAUNCH AGY</button>
        </div>
        <div class="input-row">
            <input type="text" id="command-input" class="text-input" placeholder="Type prompt or command here..." autocomplete="off">
            <button class="btn-send" onclick="sendCommand()">Send</button>
        </div>
    </div>

    <!-- Bottom Nav Bar -->
    <nav>
        <div class="nav-item active" id="nav-shell" onclick="switchView('shell')">
            <span class="material-symbols-outlined">terminal</span>
            <span>Shell</span>
        </div>
        <div class="nav-item" id="nav-config" onclick="switchView('config')">
            <span class="material-symbols-outlined">settings</span>
            <span>Config</span>
        </div>
    </nav>

    <script>
        const urlParams = new URLSearchParams(window.location.search);
        const userId = urlParams.get('user_id') || '1769298522';
        document.getElementById('userid-input').value = userId;

        const terminalEl = document.getElementById('terminal');
        const commandInput = document.getElementById('command-input');
        const configOverlay = document.getElementById('config-view');
        const controlPanel = document.getElementById('control-panel');

        let currentTheme = 'matrix';

        function setTheme(themeKey, btn) {
            currentTheme = themeKey;
            document.querySelectorAll('.theme-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        }

        function applyProfileSettings() {
            const id = document.getElementById('userid-input').value;
            // Set global theme element
            if (currentTheme === 'matrix') {
                document.documentElement.removeAttribute('data-theme');
            } else {
                document.documentElement.setAttribute('data-theme', currentTheme);
            }
            // Navigate back to shell
            switchView('shell');
        }

        function switchView(viewName) {
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            if (viewName === 'shell') {
                document.getElementById('nav-shell').classList.add('active');
                configOverlay.style.display = 'none';
                controlPanel.style.display = 'flex';
            } else if (viewName === 'config') {
                document.getElementById('nav-config').classList.add('active');
                configOverlay.style.display = 'flex';
                controlPanel.style.display = 'none';
            }
        }

        function cleanTerminal(text) {
            if (!text) return "";
            
            // Check for Google Login URL
            const match = text.match(/https:\/\/accounts\.google\.com\/o\/oauth2\/auth\?[^\s'"\\<>]+/);
            if (match) {
                let authUrl = match[0];
                authUrl = authUrl.split(/[\\\[\]\s]/)[0];
                authUrl = authUrl.replace(/\]8;;$/, '').replace(/\\$/, '').replace(/\]8$/, '');
                
                return `
<div class="login-card" style="display:flex; flex-direction:column; align-items:center; justify-content:center; padding:30px; text-align:center; gap:16px;">
    <div style="font-size:3rem;">🔑</div>
    <div style="font-size:1.2rem; font-weight:bold; color:#FFF;">Authentication Required</div>
    <div style="color:var(--text-secondary); font-size:0.9rem;">Please authorize your Google account to enable the Antigravity AI Agent to run.</div>
    <a href="${authUrl}" target="_blank" style="background:var(--accent-color); color:#000; font-weight:bold; padding:12px 28px; border-radius:30px; text-decoration:none;">🔗 Log In (Google)</a>
    <div style="color:var(--text-secondary); font-size:0.8rem;">After logging in, copy the code and paste it into the console input field below.</div>
</div>`;
            }

            let cleaned = text.replace(/\\x1b\\]8;[^\\x1b\\x07]*(?:\\x1b\\\\|\\x07)/g, '');
            cleaned = cleaned.replace(/\\x1b\\[[0-9;?]*[a-zA-Z]/g, '');
            cleaned = cleaned.replace(/\\x1b./g, '');
            cleaned = cleaned.replace(/[\\x00-\\x08\\x0b\\x0c\\x0e-\\x1f\\x7f]/g, '');
            
            cleaned = cleaned.replace(/\\[\\?2004[lh]/g, '');
            cleaned = cleaned.replace(/\\[[0-9;?]*[mJKhHdDL]/g, '');
            
            return cleaned.trim();
        }

        async function refresh() {
            try {
                const response = await fetch(`/api/sessions/${userId}/output?lines=50`);
                if (!response.ok) throw new Error("Connection error");
                
                const data = await response.json();
                const cleaned = cleanTerminal(data.output);
                
                if (cleaned.includes('Authentication Required')) {
                    terminalEl.innerHTML = cleaned;
                } else {
                    terminalEl.textContent = cleaned || "Console screen is blank.";
                    const cursor = document.createElement('span');
                    cursor.className = 'cursor';
                    terminalEl.appendChild(cursor);
                    terminalEl.scrollTop = terminalEl.scrollHeight;
                }
            } catch (err) {
                console.error(err);
            }
        }

        async function sendCommand() {
            const text = commandInput.value.trim();
            if (!text) return;
            commandInput.value = "";
            try {
                await fetch('/api/sessions/send', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: parseInt(userId), text: text })
                });
                setTimeout(refresh, 200);
            } catch (err) {
                console.error(err);
            }
        }

        async function sendKey(key) {
            try {
                await fetch('/api/sessions/key', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: parseInt(userId), key: key })
                });
                setTimeout(refresh, 150);
            } catch (err) {
                console.error(err);
            }
        }

        async function sendInterrupt() {
            try {
                await fetch('/api/sessions/interrupt', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: parseInt(userId) })
                });
                setTimeout(refresh, 150);
            } catch (err) {
                console.error(err);
            }
        }

        async function launchAgy() {
            try {
                await fetch('/api/sessions/new', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: parseInt(userId), project: "default" })
                });
                await fetch('/api/sessions/send', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: parseInt(userId), text: "agy" })
                });
                setTimeout(refresh, 300);
            } catch (err) {
                console.error(err);
            }
        }

        // Simulate dashboard metrics adjustments
        setInterval(() => {
            const load = (35 + Math.random() * 15).toFixed(1);
            document.getElementById('load-fill').style.width = `${load}%`;
            document.getElementById('load-text').textContent = `${load}%`;
            
            const lat = Math.floor(250 + Math.random() * 80);
            document.getElementById('latency-text').textContent = `${lat}ms`;
        }, 3000);

        commandInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendCommand();
            }
        });

        refresh();
        setInterval(refresh, 2000);
    </script>
</body>
</html>
"""
