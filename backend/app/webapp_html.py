HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Antigravity Console</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Fira+Code:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        :root {
            /* Theme Green Matrix (default) */
            --bg-base: #050507;
            --term-bg: #020203;
            --text-color: #39FF14;
            --accent-color: #39FF14;
            --border-color: rgba(57, 255, 20, 0.25);
            --panel-bg: rgba(2, 2, 3, 0.85);
            --btn-bg: rgba(57, 255, 20, 0.05);
            
            --text-secondary: #8E8E9F;
            --accent-red: #FF3366;
            --card-border: rgba(56, 56, 74, 0.5);
        }

        /* Tokyo Night Theme */
        [data-theme="tokyo"] {
            --bg-base: #1a1b26;
            --term-bg: #16161e;
            --text-color: #7aa2f7;
            --accent-color: #bb9af3;
            --border-color: #292e42;
            --panel-bg: rgba(22, 22, 30, 0.85);
            --btn-bg: rgba(187, 154, 243, 0.08);
        }

        /* Solarized Dark Theme */
        [data-theme="solarized"] {
            --bg-base: #002b36;
            --term-bg: #073642;
            --text-color: #93a1a1;
            --accent-color: #2aa198;
            --border-color: #586e75;
            --panel-bg: rgba(7, 54, 66, 0.85);
            --btn-bg: rgba(42, 161, 152, 0.08);
        }

        /* Amber CRT Theme */
        [data-theme="amber"] {
            --bg-base: #0c0700;
            --term-bg: #060300;
            --text-color: #FFB000;
            --accent-color: #FFB000;
            --border-color: #3d2a00;
            --panel-bg: rgba(6, 3, 0, 0.85);
            --btn-bg: rgba(255, 176, 0, 0.05);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            user-select: none;
            -webkit-user-select: none;
        }

        body {
            font-family: 'Outfit', sans-serif;
            background: var(--bg-base);
            color: var(--text-color);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            padding: 12px;
            transition: background 0.3s, color 0.3s;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 4px 16px 4px;
        }

        .logo-section {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .logo-dot {
            width: 10px;
            height: 10px;
            background-color: var(--accent-color);
            border-radius: 50%;
            box-shadow: 0 0 10px var(--accent-color);
            animation: pulse 2s infinite;
        }

        h1 {
            font-size: 1.25rem;
            font-weight: 800;
            letter-spacing: -0.5px;
            color: #FFF;
        }

        .header-actions {
            display: flex;
            gap: 8px;
        }

        .btn-action {
            font-size: 0.75rem;
            font-weight: 600;
            padding: 6px 12px;
            border-radius: 20px;
            background: rgba(255, 255, 255, 0.04);
            color: var(--text-secondary);
            border: 1px solid rgba(255, 255, 255, 0.08);
            cursor: pointer;
            transition: background 0.2s;
        }

        .btn-action:active {
            background: rgba(255, 255, 255, 0.1);
        }

        .status-badge {
            font-size: 0.75rem;
            font-weight: 600;
            padding: 6px 12px;
            border-radius: 20px;
            background: rgba(57, 255, 20, 0.1);
            color: #39FF14;
            border: 1px solid rgba(57, 255, 20, 0.2);
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .status-dot {
            width: 6px;
            height: 6px;
            background-color: #39FF14;
            border-radius: 50%;
        }

        /* Console Container */
        .console-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: var(--panel-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            overflow: hidden;
            position: relative;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
            transition: border-color 0.3s;
        }

        /* CRT Scanline Visual Effect Overlay */
        .scanlines {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%);
            background-size: 100% 4px;
            opacity: 0.04;
            pointer-events: none;
            z-index: 99;
        }

        /* Terminal Window */
        .terminal-window {
            flex: 1;
            background-color: var(--term-bg);
            padding: 14px;
            font-family: 'Fira Code', monospace;
            font-size: 0.85rem;
            line-height: 1.4;
            overflow-y: auto;
            white-space: pre-wrap;
            word-break: break-all;
            border-bottom: 1px solid var(--border-color);
            color: var(--text-color);
            transition: background-color 0.3s, color 0.3s, border-bottom 0.3s;
        }

        /* Blinking Terminal Cursor */
        .cursor {
            display: inline-block;
            width: 8px;
            height: 15px;
            background-color: var(--text-color);
            margin-left: 2px;
            vertical-align: middle;
            animation: blink 1s step-start infinite;
        }

        @keyframes blink {
            50% { opacity: 0; }
        }

        /* Custom Scrollbar */
        .terminal-window::-webkit-scrollbar {
            width: 6px;
        }
        .terminal-window::-webkit-scrollbar-track {
            background: var(--term-bg);
        }
        .terminal-window::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.06);
            border-radius: 3px;
        }

        /* Login Card Layout */
        .login-card {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            padding: 24px;
            text-align: center;
            gap: 16px;
        }

        .login-icon {
            font-size: 3rem;
            animation: bounce 2s infinite;
        }

        .login-title {
            font-size: 1.2rem;
            font-weight: 600;
            color: #FFF;
        }

        .login-desc {
            color: var(--text-secondary);
            font-size: 0.9rem;
            max-width: 280px;
            line-height: 1.4;
        }

        .btn-login {
            display: inline-block;
            background: var(--accent-color);
            color: #000;
            font-weight: 600;
            padding: 12px 28px;
            border-radius: 30px;
            text-decoration: none;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .btn-login:active {
            transform: scale(0.95);
        }

        /* Keyboard Layout */
        .control-panel {
            padding: 14px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            background: rgba(0, 0, 0, 0.25);
        }

        /* Input Area */
        .input-row {
            display: flex;
            gap: 8px;
        }

        .text-input {
            flex: 1;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            color: var(--text-color);
            padding: 12px 16px;
            font-family: inherit;
            font-size: 0.95rem;
            outline: none;
            transition: border-color 0.2s;
        }

        .text-input:focus {
            border-color: var(--accent-color);
        }

        .btn-send {
            background: var(--text-color);
            color: #000;
            border: none;
            border-radius: 10px;
            padding: 0 20px;
            font-weight: 600;
            font-size: 0.95rem;
            cursor: pointer;
            transition: opacity 0.2s;
        }

        .btn-send:active {
            opacity: 0.8;
        }

        /* Keypad Grid */
        .keypad-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
            max-width: 360px;
            margin: 0 auto;
            width: 100%;
        }

        .key-btn {
            background: var(--btn-bg);
            border: 1px solid var(--border-color);
            color: var(--text-color);
            border-radius: 10px;
            padding: 12px;
            font-family: inherit;
            font-size: 0.95rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: background 0.1s, transform 0.1s, border-color 0.3s;
        }

        .key-btn:active {
            background: rgba(255, 255, 255, 0.12);
            transform: scale(0.95);
        }

        .key-btn.accent-blue {
            color: var(--accent-color);
            border-color: var(--border-color);
        }

        .key-btn.accent-red {
            color: var(--accent-red);
            border-color: rgba(255, 51, 102, 0.3);
        }

        @keyframes pulse {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 229, 255, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(0, 229, 255, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 229, 255, 0); }
        }

        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-8px); }
        }
    </style>
</head>
<body>
    <header>
        <div class="logo-section">
            <div class="logo-dot"></div>
            <h1>Antigravity Console</h1>
        </div>
        <div class="header-actions">
            <button class="btn-action" onclick="cycleTheme()">🎨 Theme</button>
            <div class="status-badge" id="status-badge">
                <div class="status-dot"></div>
                <span>Connected</span>
            </div>
        </div>
    </header>

    <div class="console-container">
        <!-- CRT scanline effect element -->
        <div class="scanlines"></div>
        
        <div class="terminal-window" id="terminal">Initializing connection...<span class="cursor"></span></div>
        
        <div class="control-panel">
            <div class="input-row">
                <input type="text" id="command-input" class="text-input" placeholder="Type prompt or command here..." autocomplete="off">
                <button id="btn-send" class="btn-send">Send</button>
            </div>
            
            <div class="keypad-grid">
                <!-- Row 1 -->
                <button class="key-btn" onclick="sendKey('Tab')">⇥ Tab</button>
                <button class="key-btn" onclick="sendKey('Up')">⬆️ Up</button>
                <button class="key-btn" onclick="sendKey('BSpace')">⌫ Back</button>
                
                <!-- Row 2 -->
                <button class="key-btn" onclick="sendKey('Left')">⬅️ Left</button>
                <button class="key-btn" onclick="sendKey('Enter')">🆗 Enter</button>
                <button class="key-btn" onclick="sendKey('Right')">➡️ Right</button>
                
                <!-- Row 3 -->
                <button class="key-btn accent-red" onclick="interrupt()">🛑 Ctrl+C</button>
                <button class="key-btn" onclick="sendKey('Down')">⬇️ Down</button>
                <button class="key-btn accent-blue" onclick="refresh()">🔄 Refresh</button>
                
                <!-- Row 4 -->
                <button class="key-btn" onclick="navigateHistory(1)">⏮️ Prev Hist</button>
                <button class="key-btn" onclick="navigateHistory(-1)">⏭️ Next Hist</button>
                <button class="key-btn accent-blue" onclick="launchAgy()">🚀 Launch agy</button>
            </div>
        </div>
    </div>

    <script>
        const urlParams = new URLSearchParams(window.location.search);
        const userId = urlParams.get('user_id');
        const terminalEl = document.getElementById('terminal');
        const statusBadge = document.getElementById('status-badge');
        const commandInput = document.getElementById('command-input');
        const btnSend = document.getElementById('btn-send');

        // Command History Navigation
        let history = [];
        let historyIndex = -1;

        // Dynamic Themes
        const THEME_KEYS = ['matrix', 'tokyo', 'solarized', 'amber'];
        let currentThemeIndex = 0;

        function cycleTheme() {
            triggerHaptic();
            currentThemeIndex = (currentThemeIndex + 1) % THEME_KEYS.length;
            const themeKey = THEME_KEYS[currentThemeIndex];
            if (themeKey === 'matrix') {
                document.documentElement.removeAttribute('data-theme');
            } else {
                document.documentElement.setAttribute('data-theme', themeKey);
            }
        }

        // Haptic Feedback trigger
        function triggerHaptic() {
            if (navigator.vibrate) {
                navigator.vibrate(12);
            }
        }

        if (!userId) {
            terminalEl.innerHTML = '<div class="login-card"><div class="login-icon">⚠️</div><div class="login-title">Missing User ID</div><div class="login-desc">Please open this console directly from the link sent by your Telegram bot.</div></div>';
            statusBadge.style.display = 'none';
        }

        // Clean Terminal escape codes
        function cleanTerminal(text) {
            if (!text) return "";
            
            // Check for Google Login URL
            const match = text.match(/https:\/\/accounts\.google\.com\/o\/oauth2\/auth\?[^\s'"\\<>]+/);
            if (match) {
                let authUrl = match[0];
                authUrl = authUrl.split(/[\\\[\]\s]/)[0]; // strip trailing codes
                authUrl = authUrl.replace(/\]8;;$/, '').replace(/\\$/, '').replace(/\]8$/, '');
                
                return `
<div class="login-card">
    <div class="login-icon">🔑</div>
    <div class="login-title">Authentication Required</div>
    <div class="login-desc">Please authorize your Google account to enable the Antigravity AI Agent to run.</div>
    <a href="${authUrl}" target="_blank" class="btn-login">🔗 Log In (Google)</a>
    <div class="login-desc" style="margin-top: 10px; font-size: 0.8rem;">After logging in, copy the code and paste it into the console input field below.</div>
</div>`;
            }

            // Strip ANSI codes
            let cleaned = text.replace(/\\x1b\\]8;[^\\x1b\\x07]*(?:\\x1b\\\\|\\x07)/g, ''); // OSC 8
            cleaned = cleaned.replace(/\\x1b\\[[0-9;?]*[a-zA-Z]/g, ''); // CSI
            cleaned = cleaned.replace(/\\x1b./g, ''); // ESC
            cleaned = cleaned.replace(/[\\x00-\\x08\\x0b\\x0c\\x0e-\\x1f\\x7f]/g, ''); // control chars
            
            // Leftovers
            cleaned = cleaned.replace(/\\[\\?2004[lh]/g, '');
            cleaned = cleaned.replace(/\\[[0-9;?]*[mJKhHdDL]/g, '');
            
            return cleaned.trim();
        }

        async function refresh() {
            if (!userId) return;
            try {
                const response = await fetch(`/api/sessions/${userId}/output?lines=50`);
                if (!response.ok) throw new Error("Connection error");
                
                const data = await response.json();
                const cleaned = cleanTerminal(data.output);
                
                if (cleaned.includes('class="login-card"')) {
                    terminalEl.innerHTML = cleaned;
                } else {
                    terminalEl.textContent = cleaned || "Console screen is blank.";
                    // Re-append the cursor element
                    const cursor = document.createElement('span');
                    cursor.className = 'cursor';
                    terminalEl.appendChild(cursor);
                    
                    // Auto scroll to bottom
                    terminalEl.scrollTop = terminalEl.scrollHeight;
                }
                
                statusBadge.innerHTML = '<div class="status-dot"></div><span>Connected</span>';
                statusBadge.style.borderColor = 'rgba(57, 255, 20, 0.2)';
                statusBadge.style.color = '#39FF14';
            } catch (err) {
                console.error(err);
                statusBadge.innerHTML = '<div class="status-dot" style="background-color: var(--accent-red)"></div><span>Offline</span>';
                statusBadge.style.borderColor = 'rgba(255, 51, 102, 0.3)';
                statusBadge.style.color = 'var(--accent-red)';
            }
        }

        async function sendCommand() {
            const text = commandInput.value.trim();
            if (!text || !userId) return;
            
            // History management
            history.unshift(text);
            if (history.length > 50) history.pop();
            historyIndex = -1;

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
            triggerHaptic();
            if (!userId) return;
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

        async function interrupt() {
            triggerHaptic();
            if (!userId) return;
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
            triggerHaptic();
            if (!userId) return;
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

        function navigateHistory(direction) {
            triggerHaptic();
            if (history.length === 0) return;
            
            historyIndex += direction;
            if (historyIndex < -1) historyIndex = history.length - 1;
            if (historyIndex >= history.length) historyIndex = -1;

            if (historyIndex === -1) {
                commandInput.value = "";
            } else {
                commandInput.value = history[historyIndex];
            }
        }

        // Trigger send on enter key
        commandInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendCommand();
            }
        });
        
        btnSend.addEventListener('click', sendCommand);

        if (userId) {
            refresh();
            setInterval(refresh, 2000);
        }
    </script>
</body>
</html>
"""
