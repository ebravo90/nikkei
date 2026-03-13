import threading
import json
import os
import hashlib
import requests
from flask import Flask, request, render_template_string, jsonify, redirect, url_for, session
from google_auth_oauthlib.flow import Flow

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from core.security import set_secret, get_secret, delete_secret
from core.registry import plugin_registry
from core.notifier import send_os_notification

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Polished UI HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html data-theme="dark">
<head>
    <title>Nikkei OS Configuration</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root {
            --bg-color: #ffffff;
            --text-color: #333333;
            --container-bg: #f9f9f9;
            --border-color: #dddddd;
            --primary-color: #0066cc;
            --primary-hover: #0052a3;
            --input-bg: #ffffff;
            --input-border: #cccccc;
            --danger-color: #cc0000;
            --success-bg: #e6ffe6;
            --success-color: #006600;
        }

        [data-theme="dark"] {
            --bg-color: #121212;
            --text-color: #e0e0e0;
            --container-bg: #1e1e1e;
            --border-color: #333333;
            --primary-color: #3b82f6;
            --primary-hover: #2563eb;
            --input-bg: #2d2d2d;
            --input-border: #444444;
            --danger-color: #ef4444;
            --success-bg: #064e3b;
            --success-color: #34d399;
        }

        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
            max-width: 650px; 
            margin: 40px auto; 
            padding: 20px; 
            line-height: 1.6; 
            background-color: var(--bg-color);
            color: var(--text-color);
            transition: background-color 0.3s, color 0.3s;
        }
        
        .container {
            background-color: var(--container-bg);
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        h1, h2, h3 { border-bottom: 1px solid var(--border-color); padding-bottom: 10px; margin-top: 0; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-weight: 600; }
        
        input[type="text"], input[type="password"] { 
            width: 100%; 
            padding: 10px; 
            border: 1px solid var(--input-border); 
            border-radius: 4px; 
            box-sizing: border-box; 
            background-color: var(--input-bg);
            color: var(--text-color);
        }
        
        button { 
            background-color: var(--primary-color); 
            color: white; 
            border: none; 
            padding: 10px 15px; 
            border-radius: 4px; 
            cursor: pointer; 
            font-weight: bold;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: background-color 0.2s;
        }
        button:hover { background-color: var(--primary-hover); }
        
        .btn-danger { background-color: var(--danger-color); }
        .btn-danger:hover { background-color: #b91c1c; }
        
        .message { padding: 12px; margin-bottom: 20px; border-radius: 4px; }
        .success { background-color: var(--success-bg); border: 1px solid var(--success-color); color: var(--success-color); }
        .error { background-color: rgba(239, 68, 68, 0.1); border: 1px solid var(--danger-color); color: var(--danger-color); }
        
        .oauth-btn { background-color: #4285F4; margin-top: 10px; }
        .oauth-btn:hover { background-color: #3367D6; }
        
        hr { border: 0; border-top: 1px solid var(--border-color); margin: 30px 0; }
        
        details {
            background-color: var(--bg-color);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            padding: 15px;
            margin-top: 20px;
        }
        
        summary {
            font-weight: bold;
            cursor: pointer;
            outline: none;
        }
        
        .theme-toggle {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background-color: var(--primary-color);
            color: white;
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            font-size: 20px;
            cursor: pointer;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }
        
        .help-link {
            display: inline-block;
            margin-top: 5px;
            font-size: 0.9em;
            color: var(--primary-color);
            text-decoration: none;
        }
        .help-link:hover { text-decoration: underline; }
        
        .input-group {
            display: flex;
            gap: 10px;
        }
        .input-group input { flex-grow: 1; }
        
        .connected-card {
            background-color: var(--input-bg);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            padding: 10px 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: bold;
        }

        /* Modal Styles */
        .modal {
            display: none;
            position: fixed;
            z-index: 2000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.7);
            align-items: center;
            justify-content: center;
        }
        .modal-content {
            background-color: var(--container-bg);
            padding: 30px;
            border-radius: 8px;
            max-width: 400px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            border: 1px solid var(--border-color);
        }
        .modal-content h3 { color: var(--danger-color); border-bottom: none; margin-bottom: 15px; }
        .modal-buttons { display: flex; gap: 10px; justify-content: center; margin-top: 20px; }
    </style>
</head>
<body>
    <!-- Security Modal -->
    <div id="securityModal" class="modal">
        <div class="modal-content">
            <h3><i class="fas fa-exclamation-triangle"></i> Security Warning</h3>
            <p>You are about to approve quarantined files. These files will be able to execute any command on your host system.</p>
            <p><strong>Are you absolutely sure?</strong></p>
            <div class="modal-buttons">
                <button type="button" class="btn" onclick="closeModal()" style="background-color: #666; color: white;"><i class="fas fa-times"></i> Cancel</button>
                <button type="button" id="confirmApprovalBtn" class="btn-danger" onclick="submitApproval()"><i class="fas fa-check"></i> Confirm (<span id="countdownText">5</span>)</button>
            </div>
        </div>
    </div>

    <!-- Debug Mode Modal -->
    <div id="debugModal" class="modal">
        <div class="modal-content">
            <h3><i class="fas fa-user-secret"></i> Enable Debug Mode</h3>
            <p>You are about to enable native OS notifications for all background actions.</p>
            <p><strong>This will auto-disable after 15 minutes. Proceed?</strong></p>
            <div class="modal-buttons">
                <button type="button" class="btn" onclick="closeDebugModal()" style="background-color: #666; color: white;"><i class="fas fa-times"></i> Cancel</button>
                <button type="button" id="confirmDebugBtn" class="btn-danger" onclick="submitDebugMode()"><i class="fas fa-check"></i> Confirm (<span id="debugCountdownText">5</span>)</button>
            </div>
        </div>
    </div>

    <button class="theme-toggle" onclick="toggleTheme()" id="themeToggleBtn">
        <i class="fas fa-moon"></i>
    </button>

    <div class="container">
        <h1><i class="fas fa-cogs"></i> Nikkei OS Settings</h1>
        
        {% if message %}
        <div class="message success"><i class="fas fa-check-circle"></i> {{ message }}</div>
        {% endif %}
        {% if error_msg %}
        <div class="message error"><i class="fas fa-exclamation-circle"></i> {{ error_msg }}</div>
        {% endif %}

        <form action="/save_token" method="POST">
            <h2><i class="fas fa-sliders-h"></i> Core Settings</h2>
            
            <div class="form-group">
                <label for="GEMINI_API_KEY">Gemini API Key</label>
                {% if gemini_connected %}
                <div class="connected-card">
                    <span style="color: var(--success-color);"><i class="fas fa-circle"></i> Connected</span>
                    <form action="/revoke_secret" method="POST" style="margin:0; display:inline;">
                        <input type="hidden" name="secret_key" value="GEMINI_API_KEY">
                        <button type="submit" class="btn-danger" style="padding: 5px 10px; font-size: 0.8em;"><i class="fas fa-unlink"></i> Disconnect</button>
                    </form>
                </div>
                {% else %}
                <input type="password" id="GEMINI_API_KEY" name="GEMINI_API_KEY" placeholder="AIzaSy...">
                {% endif %}
            </div>

            <div class="form-group">
                <label for="TELEGRAM_BOT_TOKEN">Telegram Bot Token</label>
                {% if telegram_connected %}
                <div class="connected-card">
                    <span style="color: var(--success-color);"><i class="fas fa-circle"></i> Connected</span>
                    <form action="/revoke_secret" method="POST" style="margin:0; display:inline;">
                        <input type="hidden" name="secret_key" value="TELEGRAM_BOT_TOKEN">
                        <button type="submit" class="btn-danger" style="padding: 5px 10px; font-size: 0.8em;"><i class="fas fa-unlink"></i> Disconnect</button>
                    </form>
                </div>
                {% else %}
                <input type="password" id="TELEGRAM_BOT_TOKEN" name="TELEGRAM_BOT_TOKEN" placeholder="123456789:ABCdefGHIjklMNOpqrSTUvwxYZ">
                {% endif %}
                <a class="help-link" href="https://github.com/your-org/project-nikkei#how-to-create-the-telegram-bot-for-beginners" target="_blank">
                    <i class="fas fa-question-circle"></i> How to get this token?
                </a>
            </div>
            
            <div class="form-group">
                <label for="TELEGRAM_ADMIN_CHAT_ID">Telegram Admin Chat ID (Whitelist)</label>
                <div class="input-group">
                    <input type="text" id="TELEGRAM_ADMIN_CHAT_ID" name="TELEGRAM_ADMIN_CHAT_ID" placeholder="Auto-detected read-only ID" readonly>
                    <button type="button" onclick="autoDetectTelegramId()" id="detectBtn">
                        <i class="fas fa-magic"></i> Auto-Detect My ID
                    </button>
                </div>
                <small id="detectStatus" style="display:block; margin-top:5px;"></small>
            </div>
            
            <button type="submit"><i class="fas fa-save"></i> Save Core Settings</button>
        </form>

        <hr>

        <h2><i class="fas fa-shield-virus"></i> Quarantined Tentacles</h2>
        <p>The following tentacles were flagged by the AST Scanner. Review and approve them if they are safe.</p>
        {% if quarantined_files %}
            <form action="/approve_quarantine" method="POST" id="quarantineForm">
                {% for filename, reason in quarantined_files.items() %}
                <div class="form-group" style="padding: 15px; border: 1px solid var(--danger-color); background-color: rgba(239, 68, 68, 0.1); border-radius: 4px;">
                    <label>
                        <input type="checkbox" name="approved_files" value="{{ filename }}">
                        <strong><i class="fas fa-file-code"></i> {{ filename }}</strong>
                    </label>
                    <div style="margin-left: 24px; font-size: 0.9em; color: var(--danger-color);">{{ reason }}</div>
                </div>
                {% endfor %}
                <button type="button" class="btn-danger" onclick="showModal()"><i class="fas fa-unlock-alt"></i> Approve Selected</button>
            </form>
        {% else %}
            <p style="color: var(--success-color); font-style: italic;"><i class="fas fa-check"></i> No items currently in quarantine.</p>
        {% endif %}

        <hr>

        <h2><i class="fas fa-check-circle"></i> Active Whitelist (Approved)</h2>
        {% if whitelisted_files %}
            <ul style="list-style: none; padding: 0;">
            {% for filename, hash_val in whitelisted_files.items() %}
                <li style="display: flex; justify-content: space-between; align-items: center; padding: 10px; border-bottom: 1px solid var(--border-color);">
                    <div>
                        <strong><i class="fas fa-file-code"></i> {{ filename }}</strong>
                        <div style="font-size: 0.8em; color: gray; font-family: monospace;">{{ hash_val[:16] }}...</div>
                    </div>
                    <form action="/revoke" method="POST" style="margin: 0;">
                        <input type="hidden" name="filename" value="{{ filename }}">
                        <button class="btn-danger" type="submit" style="padding: 5px 10px; font-size: 0.9em;"><i class="fas fa-trash-alt"></i> Revoke Access</button>
                    </form>
                </li>
            {% endfor %}
            </ul>
        {% else %}
            <p style="color: gray; font-style: italic;"><i class="fas fa-info-circle"></i> No items currently whitelisted.</p>
        {% endif %}

        <hr>

        <h2><i class="fas fa-user-secret"></i> Zero-Trust Debug Mode</h2>
        <p>Enable cross-platform native OS notifications for every agent action. Provides strict execution transparency.</p>
        {% if debug_mode_active %}
        <div class="connected-card" style="border-color: var(--success-color);">
            <span style="color: var(--success-color);"><i class="fas fa-eye"></i> Ghost Mode Active (Auto-revokes after 15m)</span>
            <form action="/disable_debug_mode" method="POST" style="margin:0; display:inline;">
                <button type="submit" class="btn-danger" style="padding: 5px 10px; font-size: 0.8em;"><i class="fas fa-eye-slash"></i> Disable Now</button>
            </form>
        </div>
        {% else %}
        <form action="/enable_debug_mode" method="POST" id="debugForm">
            <button type="button" class="btn-danger" onclick="showDebugModal()"><i class="fas fa-eye"></i> Enable Ghost/Debug Mode</button>
        </form>
        {% endif %}

        <details>
            <summary><i class="fas fa-flask"></i> Advanced / Geek Settings</summary>
            
            <div style="margin-top: 20px;">
                <form action="/save_token" method="POST">
                    <h3><i class="fas fa-hdd"></i> Drive-as-a-Queue (DaaQ)</h3>
                    <p style="font-size: 0.9em; line-height: 1.5;"><strong>What is this?</strong> DaaQ (Drive-as-a-Queue) allows Nikkei to bypass strict corporate firewalls by using a Google Drive folder as a secure, offline message queue.<br><strong>Benefits:</strong> Control your home PC from work without opening network ports.<br><strong>Risks:</strong> Nikkei will have access to create and read files in your Drive (restricted only to files it creates).</p>
                    <div class="form-group">
                        <label for="DAAQ_SECRET_KEY">DaaQ Secret Key (HMAC)</label>
                        <input type="password" id="DAAQ_SECRET_KEY" name="DAAQ_SECRET_KEY" placeholder="Local symmetric key for Drive-as-a-Queue">
                    </div>
                    {% if gdrive_connected %}
                    <div class="connected-card" style="margin-top: 10px; font-size: 0.9em;">
                        <span style="color: var(--success-color);"><i class="fas fa-circle"></i> Connected to Drive</span>
                        <form action="/revoke_secret" method="POST" style="margin:0; display:inline;">
                            <input type="hidden" name="secret_key" value="GOOGLE_DRIVE_CREDS">
                            <button type="submit" class="btn-danger" style="padding: 5px 10px; font-size: 0.8em;"><i class="fas fa-unlink"></i> Revoke</button>
                        </form>
                    </div>
                    {% else %}
                    <a href="/login_drive" class="oauth-btn" style="color: white; padding: 10px 15px; border-radius: 4px; text-decoration: none; display: inline-flex; align-items: center; gap: 8px; font-weight: bold; margin-top: 10px;"><i class="fab fa-google-drive"></i> Connect Google Drive</a>
                    {% endif %}
                    <button type="submit" style="margin-top: 10px;"><i class="fas fa-save"></i> Save DaaQ Settings</button>
                </form>

                <hr>

                <form action="/save_token" method="POST">
                    <h3><i class="fas fa-heartbeat"></i> High Availability (Centinela Watchdog)</h3>
                    <p style="font-size: 0.9em;">For users with multiple jobs (OE) or frequent travelers. Connect an external Serverless endpoint.</p>
                    <div class="form-group">
                        <label for="CENTINELA_ENDPOINT_URL">Centinela Endpoint URL</label>
                        <input type="text" id="CENTINELA_ENDPOINT_URL" name="CENTINELA_ENDPOINT_URL" placeholder="https://your-worker.workers.dev/heartbeat">
                    </div>
                    <button type="submit"><i class="fas fa-save"></i> Save Watchdog Configuration</button>
                </form>
            </div>
        </details>
    </div>

    <script>
        // Dark Mode Logic
        function toggleTheme() {
            const html = document.documentElement;
            const btn = document.getElementById('themeToggleBtn');
            const icon = btn.querySelector('i');
            
            if (html.getAttribute('data-theme') === 'dark') {
                html.setAttribute('data-theme', 'light');
                localStorage.setItem('theme', 'light');
                icon.className = 'fas fa-sun';
            } else {
                html.setAttribute('data-theme', 'dark');
                localStorage.setItem('theme', 'dark');
                icon.className = 'fas fa-moon';
            }
        }

        // Initialize theme on load
        document.addEventListener('DOMContentLoaded', () => {
            const savedTheme = localStorage.getItem('theme') || 'dark';
            document.documentElement.setAttribute('data-theme', savedTheme);
            const icon = document.querySelector('#themeToggleBtn i');
            icon.className = savedTheme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
            
            // Populate current Telegram ID if available
            const currentChatId = '{{ current_chat_id }}';
            if(currentChatId && currentChatId !== 'None') {
                document.getElementById('TELEGRAM_ADMIN_CHAT_ID').value = currentChatId;
            }
        });

        // The Xiaomi Delay Modal
        let countdownInterval;
        
        function showModal() {
            // Check if any files are selected
            const checkboxes = document.querySelectorAll('input[name="approved_files"]:checked');
            if (checkboxes.length === 0) {
                alert("Please select at least one file to approve.");
                return;
            }
            
            const modal = document.getElementById('securityModal');
            const btn = document.getElementById('confirmApprovalBtn');
            const countdownSpan = document.getElementById('countdownText');
            
            modal.style.display = 'flex';
            btn.disabled = true;
            let count = 5;
            btn.innerHTML = `<i class="fas fa-check"></i> Confirm (<span id="countdownText">${count}</span>)`;
            
            countdownInterval = setInterval(() => {
                count--;
                if (count <= 0) {
                    clearInterval(countdownInterval);
                    btn.disabled = false;
                    btn.innerHTML = `<i class="fas fa-check"></i> Confirm Approval`;
                } else {
                    btn.innerHTML = `<i class="fas fa-check"></i> Confirm (<span id="countdownText">${count}</span>)`;
                }
            }, 1000);
        }
        
        function closeModal() {
            document.getElementById('securityModal').style.display = 'none';
            clearInterval(countdownInterval);
        }
        
        function submitApproval() {
            document.getElementById('quarantineForm').submit();
        }

        // Debug Mode Modal
        let debugCountdownInterval;
        
        function showDebugModal() {
            const modal = document.getElementById('debugModal');
            const btn = document.getElementById('confirmDebugBtn');
            const countdownSpan = document.getElementById('debugCountdownText');
            
            modal.style.display = 'flex';
            btn.disabled = true;
            let count = 5;
            btn.innerHTML = `<i class="fas fa-check"></i> Confirm (<span id="debugCountdownText">${count}</span>)`;
            
            debugCountdownInterval = setInterval(() => {
                count--;
                if (count <= 0) {
                    clearInterval(debugCountdownInterval);
                    btn.disabled = false;
                    btn.innerHTML = `<i class="fas fa-check"></i> Confirm Enable`;
                } else {
                    btn.innerHTML = `<i class="fas fa-check"></i> Confirm (<span id="debugCountdownText">${count}</span>)`;
                }
            }, 1000);
        }
        
        function closeDebugModal() {
            document.getElementById('debugModal').style.display = 'none';
            clearInterval(debugCountdownInterval);
        }
        
        function submitDebugMode() {
            document.getElementById('debugForm').submit();
        }

        // Auto-Detect Telegram ID
        function autoDetectTelegramId() {
            const btn = document.getElementById('detectBtn');
            const status = document.getElementById('detectStatus');
            let tokenInput = document.getElementById('TELEGRAM_BOT_TOKEN').value.trim();
            
            if (!tokenInput) {
                status.style.color = 'var(--danger-color)';
                status.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Please enter your Bot Token first, click Save Core Settings, then message your bot before detecting.';
                return;
            }
            
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Detecting...';
            status.style.color = 'var(--text-color)';
            status.innerText = "Send any message to your bot right now...";
            
            fetch('/auto_telegram_id', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ token: tokenInput })
            })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    document.getElementById('TELEGRAM_ADMIN_CHAT_ID').value = data.chat_id;
                    status.style.color = 'var(--success-color)';
                    status.innerHTML = '<i class="fas fa-check"></i> Found ID: ' + data.chat_id + ' & Saved!';
                } else {
                    status.style.color = 'var(--danger-color)';
                    status.innerHTML = '<i class="fas fa-times"></i> Error: ' + data.error;
                }
            })
            .catch(err => {
                status.style.color = 'var(--danger-color)';
                status.innerHTML = '<i class="fas fa-times"></i> Request failed. Check internet connection.';
            })
            .finally(() => {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-magic"></i> Auto-Detect My ID';
            });
        }
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    """Serve the configuration dashboard form."""
    message = request.args.get("message")
    error_msg = request.args.get("error_msg")
    current_chat_id = get_secret("TELEGRAM_ADMIN_CHAT_ID")
    
    gemini_connected = bool(get_secret("GEMINI_API_KEY"))
    telegram_connected = bool(get_secret("TELEGRAM_BOT_TOKEN"))
    gdrive_connected = bool(get_secret("GOOGLE_DRIVE_CREDS"))
    debug_mode_active = get_secret("DEBUG_MODE") == "True"
    
    whitelist_str = get_secret("WHITELISTED_TENTACLES") or "{}"
    try:
        whitelisted_files = json.loads(whitelist_str)
    except json.JSONDecodeError:
        whitelisted_files = {}
        
    return render_template_string(
        HTML_TEMPLATE, 
        message=message, 
        error_msg=error_msg,
        quarantined_files=plugin_registry.quarantined, 
        current_chat_id=current_chat_id,
        whitelisted_files=whitelisted_files,
        gemini_connected=gemini_connected,
        telegram_connected=telegram_connected,
        gdrive_connected=gdrive_connected,
        debug_mode_active=debug_mode_active
    )

@app.route("/approve_quarantine", methods=["POST"])
def approve_quarantine():
    """Compute hashes and save selected files to the whitelist JSON secret."""
    approved = request.form.getlist("approved_files")
    if not approved:
        return redirect(url_for('index', message="No items selected for approval."))
        
    whitelist_str = get_secret("WHITELISTED_TENTACLES") or "{}"
    try:
        whitelist = json.loads(whitelist_str)
    except json.JSONDecodeError:
        whitelist = {}
        
    for filename in approved:
        filepath = os.path.join(os.path.dirname(__file__), '..', 'tentacles', filename)
        if os.path.exists(filepath):
            hasher = hashlib.sha256()
            with open(filepath, 'rb') as f:
                hasher.update(f.read())
            whitelist[filename] = hasher.hexdigest()
            # Remove from quarantine
            if filename in plugin_registry.quarantined:
                del plugin_registry.quarantined[filename]
                
    set_secret("WHITELISTED_TENTACLES", json.dumps(whitelist))
    
    return redirect(url_for('index', message=f"Successfully whitelisted {len(approved)} tentacles."))

@app.route("/revoke", methods=["POST"])
def revoke_access():
    """Revoke a previously whitelisted file."""
    filename = request.form.get("filename")
    whitelist_str = get_secret("WHITELISTED_TENTACLES") or "{}"
    try:
        whitelist = json.loads(whitelist_str)
    except json.JSONDecodeError:
        whitelist = {}
        
    if filename and filename in whitelist:
        del whitelist[filename]
        set_secret("WHITELISTED_TENTACLES", json.dumps(whitelist))
        return redirect(url_for('index', message=f"Successfully revoked access for {filename}."))
        
    return redirect(url_for('index', message=f"Could not find {filename} in whitelist."))

@app.route("/revoke_secret", methods=["POST"])
def revoke_secret():
    """Revoke a generic credential from the keyring."""
    secret_key = request.form.get("secret_key")
    if secret_key:
        try:
            delete_secret(secret_key)
        except Exception:
            # Fallback in case keyring delete fails for non-existent key natively
            set_secret(secret_key, "")
        return redirect(url_for('index', message=f"Successfully disconnected credential {secret_key}."))
    return redirect(url_for('index', error_msg="No secret key provided to revoke."))

def send_telegram_alert(message: str):
    bot_token = get_secret("TELEGRAM_BOT_TOKEN")
    admin_id = get_secret("TELEGRAM_ADMIN_CHAT_ID")
    if bot_token and admin_id:
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            requests.post(url, json={"chat_id": admin_id, "text": message, "parse_mode": "HTML"}, timeout=5)
        except Exception as e:
            print(f"[UI Telegram Alert Failed]: {e}")

@app.route("/enable_debug_mode", methods=["POST"])
def enable_debug_mode():
    """Enable zero-trust debug mode for 15 minutes with a 4-minute heartbeat."""
    set_secret("DEBUG_MODE", "True")
    
    send_os_notification("🚨 Ghost/Debug Mode ENABLED", "System transparency activated.")
    send_telegram_alert("🚨 <b>SECURITY ALERT:</b> Ghost/Debug Mode was manually enabled on the host machine.")
    
    def _ttl_worker():
        import time
        for _ in range(3):
            time.sleep(240)  # 4 minutes
            if get_secret("DEBUG_MODE") != "True":
                return
            send_os_notification("⚠️ Ghost/Debug Mode ACTIVE", "Transparency heartbeat.")
            send_telegram_alert("⚠️ <b>Reminder:</b> Debug Mode is still ACTIVE.")
            
        time.sleep(180) # Remaining 3 minutes
        if get_secret("DEBUG_MODE") == "True":
            set_secret("DEBUG_MODE", "False")
            send_os_notification("✅ Ghost/Debug Mode DISABLED", "TTL expired.")
            send_telegram_alert("✅ Ghost/Debug Mode has been disabled. System returned to stealth.")
        
    threading.Thread(target=_ttl_worker, daemon=True).start()
    return redirect(url_for('index', message="Ghost/Debug Mode enabled. It will automatically disable after 15 minutes to preserve battery and sanity."))

@app.route("/disable_debug_mode", methods=["POST"])
def disable_debug_mode():
    """Manually disable debug mode."""
    if get_secret("DEBUG_MODE") == "True":
        set_secret("DEBUG_MODE", "False")
        send_os_notification("✅ Ghost/Debug Mode DISABLED", "Manual override.")
        send_telegram_alert("✅ Ghost/Debug Mode has been disabled. System returned to stealth.")
    return redirect(url_for('index', message="Ghost/Debug Mode disabled."))

@app.route("/save_token", methods=["POST"])
def save_token():
    """Receive form data and save to keyring."""
    for key, value in request.form.items():
        if value and value.strip():
            set_secret(key, value.strip())
            
    return redirect(url_for('index', message="Tokens saved securely to the system keyring!"))

@app.route("/auto_telegram_id", methods=["POST"])
def auto_telegram_id():
    """Use the Telegram getUpdates API to automatically find the user's chat ID."""
    data = request.json
    token = data.get("token")
    if not token:
        token = get_secret("TELEGRAM_BOT_TOKEN")
        
    if not token:
        return jsonify({"success": False, "error": "No Bot Token provided or saved."})
        
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=10)
        json_resp = response.json()
        
        if not json_resp.get("ok"):
            return jsonify({"success": False, "error": json_resp.get("description", "Unknown Telegram API error")})
            
        results = json_resp.get("result", [])
        if not results:
            return jsonify({"success": False, "error": "No messages found. Send a message to the bot first and try again."})
        
        # Get the latest message's chat ID
        latest_update = results[-1]
        if "message" in latest_update:
            chat_id = str(latest_update["message"]["chat"]["id"])
            set_secret("TELEGRAM_ADMIN_CHAT_ID", chat_id)
            return jsonify({"success": True, "chat_id": chat_id})
        else:
            return jsonify({"success": False, "error": "Latest update was not a standard message."})
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/login_drive", methods=["GET"])
def login_drive():
    """Initiate Google Drive OAuth2 flow."""
    client_secret_path = os.path.join(os.path.dirname(__file__), '..', 'client_secrets.json')
    if not os.path.exists(client_secret_path):
        return redirect(url_for('index', error_msg="Error: client_secrets.json missing in root directory. Please download it from Google Cloud Console."))
        
    flow = Flow.from_client_secrets_file(
        client_secret_path, 
        scopes=['https://www.googleapis.com/auth/drive.file']
    )
    flow.redirect_uri = 'http://localhost:5000/callback'
    auth_url, state = flow.authorization_url(prompt='consent')
    session['state'] = state
    session['code_verifier'] = flow.code_verifier
    return redirect(auth_url)

@app.route("/callback", methods=["GET"])
def oauth_callback():
    """OAuth redirect endpoint to catch the code and save credentials."""
    client_secret_path = os.path.join(os.path.dirname(__file__), '..', 'client_secrets.json')
    if not os.path.exists(client_secret_path):
        return redirect(url_for('index', error_msg="Error: client_secrets.json missing."))
        
    state = session.get('state')
    
    try:
        flow = Flow.from_client_secrets_file(
            client_secret_path, 
            scopes=['https://www.googleapis.com/auth/drive.file'],
            state=state
        )
        flow.redirect_uri = 'http://localhost:5000/callback'
        
        # Restore the PKCE code verifier
        flow.code_verifier = session.get('code_verifier')
        
        flow.fetch_token(authorization_response=request.url)
        creds = flow.credentials
        
        # Save to keyring
        set_secret("GOOGLE_DRIVE_CREDS", creds.to_json())
        return redirect(url_for('index', message="Google Drive connected successfully! (Credentials securely saved)"))
    except Exception as e:
        return redirect(url_for('index', error_msg=f"OAuth Failed: {str(e)}"))

def start_server(port=5000):
    """Run Flask in a daemon thread so it doesn't block the main application."""
    def run():
        # Running with use_reloader=False is crucial for threading
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR) # Silence normal flask logging for cleaner CLI
        app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)
        
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread
