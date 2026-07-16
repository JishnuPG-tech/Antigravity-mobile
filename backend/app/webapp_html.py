HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Antigravity Web Console</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Fira+Code:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-gradient: radial-gradient(circle at top, #141419, #08080a);
            --card-bg: rgba(22, 22, 28, 0.75);
            --card-border: rgba(56, 56, 74, 0.5);
            --accent-green: #39FF14;
            --accent-blue: #00E5FF;
            --accent-red: #FF3366;
            --text-primary: #E2E2E9;
            --text-secondary: #8E8E9F;
            --term-bg: #09090b;
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
            background: var(--bg-gradient);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            padding: 12px;
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
            background-color: var(--accent-blue);
            border-radius: 50%;
            box-shadow: 0 0 10px var(--accent-blue);
            animation: pulse 2s infinite;
        }

        h1 {
            font-size: 1.25rem;
            font-weight: 800;
            letter-spacing: -0.5px;
            background: linear-gradient(135deg, #FFF, var(--text-secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .status-badge {
            font-size: 0.75rem;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 20px;
            background: rgba(57, 255, 20, 0.15);
            color: var(--accent-green);
            border: 1px solid rgba(57, 255, 20, 0.3);
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .status-dot {
            width: 6px;
            height: 6px;
            background-color: var(--accent-green);
            border-radius: 50%;
        }

        /* Console Container */
        .console-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
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
            border-bottom: 1px solid var(--card-border);
        }

        /* Custom Scrollbar */
        .terminal-window::-webkit-scrollbar {
            width: 6px;
        }
        .terminal-window::-webkit-scrollbar-track {
            background: var(--term-bg);
        }
        .terminal-window::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.1);
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
        }

        .login-desc {
            color: var(--text-secondary);
            font-size: 0.9rem;
            max-width: 280px;
            line-height: 1.4;
        }

        .btn-login {
            display: inline-block;
            background: linear-gradient(135deg, var(--accent-blue), #00A8FF);
            color: #000;
            font-weight: 600;
            padding: 12px 28px;
            border-radius: 30px;
            text-decoration: none;
            box-shadow: 0 4px 15px rgba(0, 229, 255, 0.4);
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .btn-login:active {
            transform: scale(0.95);
            box-shadow: 0 2px 8px rgba(0, 229, 255, 0.2);
        }

        /* Keyboard Layout */
        .control-panel {
            padding: 14px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            background: rgba(10, 10, 12, 0.4);
        }

        /* Input Area */
        .input-row {
            display: flex;
            gap: 8px;
        }

        .text-input {
            flex: 1;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--card-border);
            border-radius: 10px;
            color: var(--text-primary);
            padding: 12px 16px;
            font-family: inherit;
            font-size: 0.95rem;
            outline: none;
            transition: border-color 0.2s;
        }

        .text-input:focus {
            border-color: var(--accent-blue);
        }

        .btn-send {
            background: var(--text-primary);
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
            background: rgba(255, 255, 255, 0.07);
            border: 1px solid var(--card-border);
            color: var(--text-primary);
            border-radius: 10px;
            padding: 12px;
            font-family: inherit;
            font-size: 0.95rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: background 0.1s, transform 0.1s;
        }

        .key-btn:active {
            background: rgba(255, 255, 255, 0.15);
            transform: scale(0.95);
        }

        .key-btn.double {
            grid-column: span 2;
        }

        .key-btn.accent-blue {
            color: var(--accent-blue);
            border-color: rgba(0, 229, 255, 0.3);
        }

        .key-btn.accent-red {
            color: var(--accent-red);
            border-color: rgba(255, 51, 102, 0.3);
        }

        /* Utilities */
        .empty-cell {
            visibility: hidden;
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
        <div class="status-badge" id="status-badge">
            <div class="status-dot"></div>
            <span>Connected</span>
        </div>
    </header>

    <div class="console-container">
        <div class="terminal-window" id="terminal">Initializing connection...</div>
        
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
                <button class="key-btn double" onclick="launchAgy()">🚀 Launch agy</button>
                <button class="key-btn" onclick="sendConfig()">⚙️ Config</button>
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
                
                // Return structured Login Card HTML
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
                
                // Check if it's the login card HTML or raw text
                if (cleaned.includes('class="login-card"')) {
                    terminalEl.innerHTML = cleaned;
                } else {
                    terminalEl.textContent = cleaned || "Console screen is blank.";
                    // Auto scroll to bottom
                    terminalEl.scrollTop = terminalEl.scrollHeight;
                }
                
                // Update badge status
                statusBadge.innerHTML = '<div class="status-dot"></div><span>Connected</span>';
                statusBadge.style.borderColor = 'rgba(57, 255, 20, 0.3)';
                statusBadge.style.color = 'var(--accent-green)';
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
            if (!userId) return;
            try {
                // Ensure session exists
                await fetch('/api/sessions/new', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: parseInt(userId), project: "default" })
                });
                // Send launch key
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

        async function sendConfig() {
            if (!userId) return;
            try {
                await fetch('/api/sessions/send', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: parseInt(userId), text: "/config" })
                });
                setTimeout(refresh, 300);
            } catch (err) {
                console.error(err);
            }
        }

        // Trigger send on enter key
        commandInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendCommand();
            }
        });
        
        btnSend.addEventListener('click', sendCommand);

        // Start polling loop
        if (userId) {
            refresh();
            setInterval(refresh, 2000); // Poll every 2 seconds
        }
    </script>
</body>
</html>
"""
