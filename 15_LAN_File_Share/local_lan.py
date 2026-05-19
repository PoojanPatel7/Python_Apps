import os
import sys
import socket
import threading
import uuid
import tempfile
import shutil
import zipfile
import queue
import time
import json
import random
import platform
import subprocess
import webbrowser
import mimetypes
import tkinter as tk
from tkinter import filedialog, messagebox

# Third-party libraries
try:
    import customtkinter as ctk
    from flask import Flask, render_template_string, request, redirect, url_for, session, Response, stream_with_context, abort, jsonify, make_response, send_file
    from werkzeug.serving import make_server
    import qrcode
    from PIL import Image
except ImportError:
    print("Missing required libraries. Please install them using:")
    print("pip install customtkinter flask qrcode pillow")
    exit(1)

# --- GLOBAL STATE & QUEUES ---
system_logs = queue.Queue()
gui_command_queue = queue.Queue() 

SERVER_STATE = {
    "host_name": "Admin", 
    "is_secure": False, 
    "pin": "0000",      
    "users": {},              # Maps IP -> {'name': str, 'os': str, 'last_seen': float, 'can_upload': bool}
    "pending_kicks": set(),   # IPs that have been removed and need to be forced to disconnect
    "chat_enabled": False
}

UPLOAD_DIR = os.path.join(os.getcwd(), "LAN_Shared_Uploads")
CHAT_DIR = os.path.join(UPLOAD_DIR, "Chat_Media")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CHAT_DIR, exist_ok=True)

# --- FLASK BACKEND SETUP ---
app = Flask(__name__)
app.secret_key = os.urandom(24) 

shared_files = {}
CHAT_MESSAGES = [] # [{'id': 1, 'from': 'ip|Host', 'from_name': 'str', 'to': 'ip|Host|None', 'type': 'text|image|video|file|lan_file', 'content': '...', 'url': '...', 'filename': '...', 'time': float}]
chat_msg_id_counter = 1

# Chat Deletion Tracking
DELETED_EVERYONE = set()
DELETED_FOR_ME = {} # Maps IP -> set of msg_ids

def get_actual_size(path):
    if os.path.isfile(path):
        return os.path.getsize(path)
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total += os.path.getsize(fp)
    return total

def format_size(size_in_bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.1f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.1f} PB"

def resolve_ip_details(ip, user_agent=""):
    network_name = ""
    try:
        name = socket.gethostbyaddr(ip)[0]
        if name != ip and "unknown" not in name.lower():
            network_name = name.split('.')[0] 
    except Exception:
        pass
    
    ua = user_agent.lower()
    os_type = "Unknown Device"
    if 'iphone' in ua: os_type = "iPhone"
    elif 'ipad' in ua: os_type = "iPad"
    elif 'android' in ua: os_type = "Android"
    elif 'macintosh' in ua or 'mac os' in ua: os_type = "Mac"
    elif 'windows' in ua: os_type = "Windows PC"
    elif 'linux' in ua: os_type = "Linux PC"

    return os_type, network_name

def log_system_event(ip, action, user_agent="", client_name=""):
    if ip == "System":
        system_logs.put(f"[System] {action}")
        return

    now = time.time()
    
    if ip not in SERVER_STATE['users']:
        os_type, net_name = resolve_ip_details(ip, user_agent)
        default_name = client_name or net_name or os_type or ip
        
        SERVER_STATE['users'][ip] = {
            'name': default_name,
            'os': os_type,
            'last_seen': now,
            'can_upload': True 
        }
        gui_command_queue.put("refresh_users")
    else:
        SERVER_STATE['users'][ip]['last_seen'] = now
        if client_name and SERVER_STATE['users'][ip]['name'] != client_name:
            SERVER_STATE['users'][ip]['name'] = client_name
            gui_command_queue.put("refresh_users")
            gui_command_queue.put("refresh_chat_ui") # Update names in chat

    display_name = SERVER_STATE['users'][ip]['name']
    system_logs.put(f"[{ip} | {display_name}] {action}")

# Embedded HTML templates
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Secure Server Access</title>
    <style>
        :root { --bg: #09090b; --card: #18181b; --text: #fafafa; --accent: #6366f1; --accent-hover: #4f46e5; --error: #ef4444; }
        body { font-family: 'Inter', system-ui, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .container { background: var(--card); max-width: 420px; width: 100%; padding: 40px 30px; border-radius: 24px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); text-align: center; border: 1px solid #27272a; }
        .badge { background: linear-gradient(135deg, #fbbf24, #d97706); color: #fff; padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: bold; letter-spacing: 1px; vertical-align: middle; margin-left: 10px; }
        h2 { margin-top: 0; margin-bottom: 25px; font-weight: 700; font-size: 1.8rem; display: flex; justify-content: center; align-items: center; gap: 8px;}
        input[type="text"] { width: 100%; padding: 18px; margin-bottom: 20px; border-radius: 14px; border: 2px solid #27272a; background: #09090b; color: white; font-size: 1.8rem; text-align: center; box-sizing: border-box; letter-spacing: 8px; transition: border 0.3s, box-shadow 0.3s; }
        input[type="text"]:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.15); }
        button { background: var(--accent); color: white; border: none; padding: 18px 20px; width: 100%; border-radius: 14px; font-weight: 600; font-size: 1.15rem; cursor: pointer; transition: all 0.3s; }
        button:hover { background: var(--accent-hover); transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.3); }
        .error { color: var(--error); margin-bottom: 20px; font-weight: 500; background: rgba(239, 68, 68, 0.1); padding: 12px; border-radius: 10px; border: 1px solid rgba(239, 68, 68, 0.2);}
    </style>
</head>
<body>
    <div class="container">
        <h2>👑 {{ host_name }}'s Server <span class="badge">PRO</span></h2>
        <p style="color: #a1a1aa; margin-bottom: 30px; font-size: 1rem; line-height: 1.5;">This premium server is secured. Please enter the 4-digit PIN.</p>
        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}
        <form method="POST">
            <input type="text" name="pin" placeholder="••••" required autocomplete="off" maxlength="4">
            <button type="submit">Unlock Access</button>
        </form>
    </div>
</body>
</html>
"""

UNLOCK_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Unlock File</title>
    <style>
        :root { --bg: #09090b; --card: #18181b; --text: #fafafa; --accent: #f59e0b; --accent-hover: #d97706; --error: #ef4444; }
        body { font-family: 'Inter', system-ui, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .container { background: var(--card); max-width: 420px; width: 100%; padding: 40px 30px; border-radius: 24px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); text-align: center; border: 1px solid #27272a; }
        h2 { margin-top: 0; margin-bottom: 10px; font-size: 1.8rem; font-weight: 700; }
        .filename { color: #a1a1aa; margin-bottom: 30px; word-break: break-all; background: #27272a; padding: 12px; border-radius: 12px; font-size: 0.95rem; font-family: monospace; }
        input[type="text"] { width: 100%; padding: 16px; margin-bottom: 20px; border-radius: 14px; border: 2px solid #3f3f46; background: #09090b; color: white; font-size: 1.3rem; text-align: center; box-sizing: border-box; transition: all 0.3s;}
        input[type="text"]:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 4px rgba(245, 158, 11, 0.15); }
        button { background: var(--accent); color: white; border: none; padding: 16px 20px; width: 100%; border-radius: 14px; font-weight: 600; font-size: 1.15rem; cursor: pointer; transition: all 0.3s; }
        button:hover { background: var(--accent-hover); transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(245, 158, 11, 0.3); }
        .error { color: var(--error); margin-bottom: 20px; font-weight: 500; background: rgba(239, 68, 68, 0.1); padding: 12px; border-radius: 10px; border: 1px solid rgba(239, 68, 68, 0.2);}
        .back-link { display: inline-block; margin-top: 25px; color: #a1a1aa; text-decoration: none; font-weight: 500; transition: color 0.2s;}
        .back-link:hover { color: #fafafa; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🔒 Locked Content</h2>
        <div class="filename">{{ file_name }}</div>
        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}
        <form method="POST">
            <input type="text" name="pin" placeholder="Enter PIN (Min 4 digits)" required autocomplete="off">
            <button type="submit">Decrypt File</button>
        </form>
        <a href="/" class="back-link">← Back to Dashboard</a>
    </div>
</body>
</html>
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{{ host_name }}'s Premium Server</title>
    <style>
        :root { --bg: #09090b; --card: #18181b; --card-hover: #27272a; --text: #fafafa; --text-muted: #a1a1aa; --accent: #6366f1; --accent-hover: #4f46e5; --success: #10b981; --success-hover: #059669; --locked: #f59e0b; --border: #27272a; --chat-bg: #0f172a; --chat-my: #4f46e5; --chat-other: #334155;}
        body { font-family: 'Inter', system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; display: flex; justify-content: center; min-height: 100vh; overflow-x: hidden; }
        .container { background: var(--card); max-width: 900px; width: 100%; padding: 40px; border-radius: 24px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); align-self: start; margin-top: 20px; border: 1px solid var(--border); transition: filter 0.3s;}
        
        .header-container { display: flex; flex-direction: column; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 25px; margin-bottom: 30px; }
        h1 { text-align: center; margin: 0; font-size: 2.2rem; font-weight: 800; display: flex; align-items: center; gap: 12px; flex-wrap: wrap; justify-content: center;}
        .premium-badge { background: linear-gradient(135deg, #fbbf24, #d97706); color: #fff; padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 800; letter-spacing: 1px; box-shadow: 0 4px 10px rgba(245, 158, 11, 0.3); text-transform: uppercase;}
        .subtitle { color: var(--text-muted); margin-top: 10px; font-size: 1rem; }
        
        .change-name-btn { margin-top: 15px; background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: var(--text-muted); padding: 8px 16px; border-radius: 10px; cursor: pointer; font-size: 0.95rem; font-weight: 500; transition: all 0.2s; }
        .change-name-btn:hover { background: rgba(255,255,255,0.1); color: #fafafa; border-color: #52525b; }

        .upload-card { background: linear-gradient(to right, rgba(99, 102, 241, 0.05), rgba(99, 102, 241, 0.1)); border: 2px dashed #4f46e5; padding: 30px; border-radius: 20px; margin-bottom: 35px; transition: all 0.3s; }
        .upload-card:hover { border-color: #818cf8; background: linear-gradient(to right, rgba(99, 102, 241, 0.08), rgba(99, 102, 241, 0.15)); }
        .upload-row { display: flex; gap: 15px; margin-bottom: 20px; }
        
        .search-bar { width: 100%; padding: 16px 24px; border-radius: 16px; border: 1px solid var(--border); background: #09090b; color: white; font-size: 1.1rem; box-sizing: border-box; transition: all 0.3s; box-shadow: inset 0 2px 4px rgba(0,0,0,0.2); }
        .search-bar:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.15); }
        
        ul { list-style: none; padding: 0; margin: 0; display: grid; gap: 12px;}
        li { display: flex; justify-content: space-between; align-items: center; padding: 20px; border: 1px solid var(--border); background: var(--bg); border-radius: 16px; transition: all 0.2s; }
        li:hover { background: var(--card-hover); transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.3); border-color: #3f3f46; }
        
        .file-info { display: flex; align-items: center; gap: 20px; overflow: hidden; padding-right: 20px; flex: 1; }
        .filename { font-weight: 600; font-size: 1.15rem; word-break: break-word; margin-bottom: 8px; line-height: 1.4; color: #f4f4f5;}
        .file-meta-container { display: flex; flex-wrap: wrap; gap: 10px; }
        .file-meta { font-size: 0.85rem; color: var(--text-muted); background: rgba(255,255,255,0.05); padding: 5px 12px; border-radius: 20px; display: inline-flex; align-items: center; font-weight: 500;}
        
        .checkbox-custom { width: 22px; height: 22px; cursor: pointer; accent-color: var(--accent); flex-shrink: 0; }
        
        .download-btn { background: var(--accent); color: white; text-decoration: none; padding: 14px 28px; border-radius: 14px; font-weight: 600; transition: all 0.2s; white-space: nowrap; border: none; cursor: pointer; font-size: 1rem; text-align: center; display: inline-flex; align-items: center; justify-content: center; }
        .download-btn:active { transform: scale(0.96); }
        .download-btn:hover { background: var(--accent-hover); box-shadow: 0 8px 15px -3px rgba(99, 102, 241, 0.3); }
        
        .unlock-btn { background: var(--locked); color: #fff; }
        .unlock-btn:hover { background: #d97706; box-shadow: 0 8px 15px -3px rgba(245, 158, 11, 0.3); }
        .download-zip-btn { background: var(--success); width: 100%; margin-bottom: 25px; padding: 18px; font-size: 1.15rem; box-shadow: 0 10px 15px -3px rgba(16, 185, 129, 0.2); border-radius: 16px;}
        .download-zip-btn:hover { background: var(--success-hover); box-shadow: 0 10px 20px -3px rgba(16, 185, 129, 0.4); }
        .empty-state { text-align: center; color: var(--text-muted); padding: 60px 0; font-size: 1.15rem; background: var(--bg); border-radius: 16px; border: 1px dashed var(--border);}

        /* Name Modal */
        .modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(9, 9, 11, 0.9); display: none; justify-content: center; align-items: center; z-index: 100000; backdrop-filter: blur(8px); }
        .modal-content { background: var(--card); padding: 50px 40px; border-radius: 24px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.8); width: 90%; max-width: 450px; text-align: center; border: 1px solid var(--border); }
        .modal-content h3 { margin-top: 0; font-size: 2rem; margin-bottom: 15px; font-weight: 800;}
        .modal-content input { width: 100%; padding: 18px; border-radius: 14px; border: 2px solid var(--border); background: var(--bg); color: white; font-size: 1.25rem; text-align: center; margin-bottom: 25px; box-sizing: border-box; transition: all 0.3s;}
        .modal-content input:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.15); }
        .modal-btn-row { display: flex; gap: 10px; width: 100%; }
        .modal-btn-row button { background: var(--accent); color: white; border: none; padding: 18px; border-radius: 14px; font-weight: bold; font-size: 1.2rem; cursor: pointer; transition: all 0.3s; flex: 1; }
        .modal-btn-row button:hover { background: var(--accent-hover); transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.3);}
        .btn-cancel { background: #3f3f46 !important; }
        .btn-cancel:hover { background: #52525b !important; box-shadow: none !important; }

        /* LIVE CHAT SYSTEM */
        #chatFab { position: fixed; bottom: 30px; right: 30px; background: var(--accent); color: white; width: 65px; height: 65px; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-size: 1.8rem; box-shadow: 0 10px 20px rgba(99, 102, 241, 0.4); cursor: pointer; transition: all 0.3s; z-index: 100; display: none; }
        #chatFab:hover { transform: scale(1.1) translateY(-5px); background: var(--accent-hover); }
        
        /* Fixed to 100dvh for better mobile layout */
        #chatDrawer { position: fixed; top: 0; right: -500px; width: 420px; max-width: 100vw; height: 100dvh; background: var(--chat-bg); border-left: 1px solid var(--border); z-index: 9999; display: flex; flex-direction: column; transition: right 0.3s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: -10px 0 30px rgba(0,0,0,0.5); }
        #chatDrawer.open { right: 0; }
        
        .chat-header { padding: 20px; background: var(--card); border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 10px rgba(0,0,0,0.2); z-index: 10; }
        .chat-header select { background: var(--bg); color: white; border: 1px solid var(--border); padding: 12px 18px; border-radius: 12px; font-size: 1.05rem; font-weight: bold; outline: none; cursor: pointer; flex: 1; margin-right: 15px;}
        .chat-header select:focus { border-color: var(--accent); }
        .close-chat-btn { background: rgba(255,255,255,0.05); color: var(--text-muted); border: 1px solid var(--border); font-size: 1.2rem; cursor: pointer; padding: 10px 15px; border-radius: 12px; transition: all 0.2s;}
        .close-chat-btn:hover { color: white; background: rgba(255,255,255,0.1); }
        
        .chat-messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 15px; background: #0b1120; scroll-behavior: smooth; }
        
        .msg-bubble { max-width: 85%; padding: 14px 18px; border-radius: 18px; position: relative; font-size: 0.95rem; line-height: 1.5; word-wrap: break-word; user-select: none; -webkit-user-select: none;}
        .msg-my { align-self: flex-end; background: var(--chat-my); color: white; border-bottom-right-radius: 4px; box-shadow: 0 4px 10px rgba(79, 70, 229, 0.2); }
        .msg-other { align-self: flex-start; background: var(--chat-other); color: white; border-bottom-left-radius: 4px; box-shadow: 0 4px 10px rgba(0,0,0,0.2); }
        .msg-sender { font-size: 0.8rem; font-weight: 800; opacity: 0.85; margin-bottom: 6px; display: block; color: #e0e7ff; }
        .msg-time { font-size: 0.7rem; opacity: 0.6; text-align: right; margin-top: 6px; display: block; }
        
        .msg-media { max-width: 100%; border-radius: 12px; margin-top: 5px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
        .msg-file-link { display: inline-flex; align-items: center; gap: 8px; background: rgba(0,0,0,0.25); padding: 12px 18px; border-radius: 12px; color: white; text-decoration: none; margin-top: 5px; font-weight: bold; font-size: 0.95rem; border: 1px solid rgba(255,255,255,0.1); transition: all 0.2s;}
        .msg-file-link:hover { background: rgba(0,0,0,0.4); transform: translateY(-1px); }

        .chat-input-area { padding: 15px; background: var(--card); border-top: 1px solid var(--border); display: flex; gap: 12px; align-items: center; z-index: 10; box-shadow: 0 -4px 10px rgba(0,0,0,0.2); }
        .attach-btn { background: rgba(255,255,255,0.05); color: white; border: 1px solid var(--border); width: 50px; height: 50px; border-radius: 14px; font-size: 1.3rem; cursor: pointer; transition: all 0.2s; display: flex; justify-content: center; align-items: center;}
        .attach-btn:hover { background: rgba(255,255,255,0.1); }
        .chat-input-area input[type="text"] { flex: 1; background: var(--bg); border: 1px solid var(--border); color: white; padding: 15px 18px; border-radius: 14px; font-size: 1rem; outline: none; transition: border 0.3s; }
        .chat-input-area input[type="text"]:focus { border-color: var(--accent); }
        .send-btn { background: var(--accent); color: white; border: none; width: 50px; height: 50px; border-radius: 14px; font-size: 1.3rem; cursor: pointer; transition: all 0.2s; display: flex; justify-content: center; align-items: center; box-shadow: 0 4px 10px rgba(99, 102, 241, 0.3);}
        .send-btn:hover { background: var(--accent-hover); transform: translateY(-2px); }

        /* Scrollbar styling for chat */
        .chat-messages::-webkit-scrollbar { width: 6px; }
        .chat-messages::-webkit-scrollbar-thumb { background: #3f3f46; border-radius: 10px; }

        /* Context Menu */
        .ctx-menu { position: fixed; background: var(--card); border: 1px solid #3f3f46; box-shadow: 0 15px 30px rgba(0,0,0,0.8); border-radius: 12px; padding: 6px; z-index: 100000; min-width: 180px; display: none; }
        .ctx-menu button { display: block; width: 100%; text-align: left; background: transparent; border: none; color: white; padding: 12px 16px; border-radius: 8px; cursor: pointer; font-size: 0.95rem; transition: background 0.2s; font-weight: 500;}
        .ctx-menu button:hover { background: rgba(255,255,255,0.1); transform: none; box-shadow: none;}
        .ctx-menu .danger { color: #ef4444; }
        .ctx-menu .danger:hover { background: rgba(239,68,68,0.15); }

        /* Upload Choice Modal */
        .upload-choice-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(9,9,11,0.85); display: none; justify-content: center; align-items: center; z-index: 99999; backdrop-filter: blur(6px); }
        .upload-choice-overlay.active { display: flex; }
        .upload-choice-card { background: #18181b; padding: 35px 30px; border-radius: 20px; border: 1px solid #27272a; box-shadow: 0 25px 50px rgba(0,0,0,0.6); width: 90%; max-width: 400px; text-align: center; }
        .upload-choice-card h3 { margin: 0 0 8px 0; font-size: 1.5rem; font-weight: 800; }
        .upload-choice-card p { color: #a1a1aa; margin: 0 0 25px 0; font-size: 0.95rem; }
        .upload-choice-card .file-preview { background: #09090b; border: 1px solid #27272a; border-radius: 12px; padding: 12px 16px; margin-bottom: 20px; color: #a1a1aa; font-size: 0.9rem; word-break: break-all; font-family: monospace; }
        .choice-btn { width: 100%; padding: 16px; border: none; border-radius: 14px; font-size: 1.1rem; font-weight: 700; cursor: pointer; margin-bottom: 10px; transition: all 0.2s; display: flex; align-items: center; justify-content: center; gap: 10px; }
        .choice-btn:hover { transform: translateY(-2px); }
        .choice-chat { background: var(--accent); color: white; }
        .choice-chat:hover { background: var(--accent-hover); box-shadow: 0 8px 20px rgba(99,102,241,0.3); }
        .choice-lan { background: #10b981; color: white; }
        .choice-lan:hover { background: #059669; box-shadow: 0 8px 20px rgba(16,185,129,0.3); }
        .choice-cancel { background: #3f3f46; color: #a1a1aa; font-size: 0.95rem; }
        .choice-cancel:hover { background: #52525b; color: white; }

        @media (max-width: 700px) {
            body { padding: 15px; }
            .container { padding: 25px; border-radius: 20px; }
            h1 { font-size: 1.8rem; }
            .upload-row { flex-direction: column; }
            li { flex-direction: column; align-items: stretch; gap: 15px; padding: 20px; }
            .checkbox-custom { position: absolute; right: 20px; top: 25px; }
            .file-info { padding-right: 35px; }
            .download-btn { width: 100%; padding: 16px; font-size: 1.1rem; }
            li { position: relative; }
            
            /* Mobile Chat Styling */
            #chatDrawer { right: -100vw; width: 100%; border-left: none; }
            #chatDrawer.open { right: 0; }
            /* Safe area spacing for modern phones (iPhones) */
            .chat-input-area { padding-bottom: calc(15px + env(safe-area-inset-bottom)); }
            #chatFab { bottom: 20px; right: 20px; }
        }
    </style>
</head>
<body>
    <!-- Name Setup Modal -->
    <div id="nameModal" class="modal-overlay">
        <div class="modal-content">
            <h3>Welcome! 👋</h3>
            <p style="color: var(--text-muted); margin-bottom: 30px; font-size: 1.05rem;" id="nameModalText">Enter your name to join this premium network.</p>
            <input type="text" id="setupNameInput" placeholder="Your Name" autocomplete="off" onkeypress="if(event.key === 'Enter') saveName()">
            <div class="modal-btn-row">
                <button onclick="saveName()">Save Name</button>
                <button onclick="closeNameModal()" id="cancelNameBtn" class="btn-cancel" style="display: none;">Cancel</button>
            </div>
        </div>
    </div>

    <!-- Main Content -->
    <div class="container" id="mainContent">
        <div class="header-container">
            <h1>
                👑 <span id="hostNameDisplay">{{ host_name }}</span>'s Server 
                <span class="premium-badge">PREMIUM</span>
            </h1>
            <div class="subtitle" id="secureStatus">{% if is_secure %}🔒 Secure Connection Active{% else %}🌐 Open Access Mode{% endif %}</div>
            <button onclick="openNameModal()" class="change-name-btn">
                👤 <span id="currentClientName">User</span> <span style="opacity: 0.5; margin-left: 5px;">(Change)</span>
            </button>
        </div>
        
        <div class="upload-card" id="uploadSection" style="display: none;">
            <h2 style="margin-top: 0; font-size: 1.4rem; margin-bottom: 20px; color: #e0e7ff; display: flex; align-items: center; gap: 8px;">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
                Share a File
            </h2>
            <form action="/upload" method="POST" enctype="multipart/form-data" id="uploadForm">
                <input type="hidden" name="uploader_name" id="hiddenUploaderName">
                <div class="upload-row">
                    <input type="file" name="file" id="fileInput" required style="flex: 1; padding: 14px; border-radius: 14px; border: 1px dashed rgba(99, 102, 241, 0.4); background: rgba(0,0,0,0.2); color: white; width: 100%; box-sizing: border-box; font-size: 1rem; cursor: pointer;">
                </div>
                <button type="submit" class="download-btn" style="width: 100%; background: #4f46e5; font-size: 1.1rem; padding: 16px;" id="uploadBtn">Upload to Host</button>
            </form>
        </div>

        <input type="text" id="searchInput" class="search-bar" placeholder="🔍 Search files or folders..." onkeyup="filterFiles()" style="margin-bottom: 30px;">
        
        <form action="/download_selected" method="POST" id="downloadForm">
            <button type="submit" class="download-btn download-zip-btn" id="zipBtn" style="display: none;">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 8px;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                Download Selected as ZIP
            </button>
            <ul id="fileList">
                <!-- Injected via JS -->
            </ul>
        </form>
    </div>

    <!-- Chat FAB & Drawer -->
    <div id="chatFab" onclick="toggleChat()" title="Open Live Chat">💬</div>
    
    <div id="chatDrawer">
        <div class="chat-header">
            <select id="chatTarget" onchange="refreshChatUI(true)">
                <option value="group">🌐 Group Chat</option>
                <option value="Host">👑 Admin (Private)</option>
            </select>
            <button class="close-chat-btn" onclick="toggleChat()">✖</button>
        </div>
        <div class="chat-messages" id="chatMessages">
            <!-- Chat bubbles injected here -->
        </div>
        <div class="chat-input-area">
            <input type="file" id="chatFileInput" style="display:none" onchange="showUploadChoice()" multiple>
            <button class="attach-btn" onclick="document.getElementById('chatFileInput').click()" title="Attach File/Image">📎</button>
            <input type="text" id="chatTextInput" placeholder="Type a message..." autocomplete="off" onkeypress="if(event.key === 'Enter') sendChatMsg()">
            <button class="send-btn" onclick="sendChatMsg()">➤</button>
        </div>
    </div>

    <!-- Chat Context Menu -->
    <div id="chatCtxMenu" class="ctx-menu">
        <button onclick="doDeleteMsg('me')">🗑️ Delete for me</button>
        <button id="btnDelEveryone" class="danger" onclick="doDeleteMsg('everyone')">🚮 Delete for everyone</button>
        <button onclick="document.getElementById('chatCtxMenu').style.display='none'">Cancel</button>
    </div>

    <!-- Upload Choice Modal -->
    <div class="upload-choice-overlay" id="uploadChoiceModal">
        <div class="upload-choice-card">
            <h3>📎 Attach Files</h3>
            <p>How would you like to share?</p>
            <div class="file-preview" id="choiceFilePreview">No files selected</div>
            <button class="choice-btn choice-chat" onclick="executeUpload('chat')">💬 Send in Chat</button>
            <button class="choice-btn choice-lan" onclick="executeUpload('lan')">📁 Upload to LAN Shared Files</button>
            <button class="choice-btn choice-cancel" onclick="cancelUploadChoice()">Cancel</button>
        </div>
    </div>

    <script>
        let myName = localStorage.getItem("lan_username") || "";
        let lastDataString = "";
        const selectedFiles = new Set();
        
        // Chat variables
        let chatMessagesData = [];
        let lastChatId = 0;
        let isChatOpen = false;
        let activeMsgId = null;
        
        document.addEventListener("DOMContentLoaded", () => {
            if (!myName) {
                openNameModal();
            } else {
                document.getElementById('hiddenUploaderName').value = myName;
                document.getElementById('currentClientName').innerText = myName;
                fetchUpdates(); 
                fetchChatUpdates();
            }

            document.getElementById('uploadForm').onsubmit = function() {
                const btn = document.getElementById('uploadBtn');
                btn.innerHTML = '<span style="display:inline-block; animation: spin 1s linear infinite;">🔄</span> Uploading...';
                btn.style.opacity = '0.7';
                btn.style.pointerEvents = 'none';
            };

            // Close context menu on external click
            document.addEventListener('click', (e) => {
                if(!e.target.closest('#chatCtxMenu')){
                    document.getElementById('chatCtxMenu').style.display = 'none';
                }
            });
        });

        function openNameModal() {
            document.getElementById('setupNameInput').value = myName;
            if (myName) {
                document.getElementById('nameModalText').innerText = "Update your display name.";
                document.getElementById('cancelNameBtn').style.display = 'block';
            } else {
                document.getElementById('nameModalText').innerText = "Enter your name to join this premium network.";
                document.getElementById('cancelNameBtn').style.display = 'none';
            }
            document.getElementById('nameModal').style.display = 'flex';
            document.getElementById('setupNameInput').focus();
        }

        function closeNameModal() {
            if (myName) {
                document.getElementById('nameModal').style.display = 'none';
            }
        }

        function saveName() {
            const input = document.getElementById('setupNameInput').value.trim();
            if (input) {
                myName = input;
                localStorage.setItem("lan_username", myName);
                document.getElementById('hiddenUploaderName').value = myName;
                document.getElementById('currentClientName').innerText = myName;
                document.getElementById('nameModal').style.display = 'none';
                fetchUpdates(); 
                fetchChatUpdates();
            }
        }

        function filterFiles() {
            const query = document.getElementById('searchInput').value.toLowerCase();
            const items = document.querySelectorAll('#fileList li');
            let downloadableCount = 0;

            items.forEach(item => {
                const filename = item.getAttribute('data-name');
                if(filename.includes(query)) {
                    item.style.display = 'flex';
                    const cb = item.querySelector('input[type="checkbox"]');
                    if (cb && cb.checked) downloadableCount++;
                } else {
                    item.style.display = 'none';
                }
            });

            const zipBtn = document.getElementById('zipBtn');
            if (zipBtn) zipBtn.style.display = downloadableCount > 1 ? 'flex' : 'none';
        }

        async function fetchUpdates() {
            if (!myName) return; 
            try {
                const res = await fetch('/api/files?u=' + encodeURIComponent(myName));
                const data = await res.json();

                if (data.kicked) {
                    localStorage.removeItem("lan_username");
                    alert("You have been disconnected from the session by the host.");
                    window.location.reload();
                    return;
                }
                
                if (data.host_name) {
                    document.getElementById('hostNameDisplay').innerText = data.host_name;
                }

                const chatFab = document.getElementById('chatFab');
                if (data.chat_enabled) {
                    chatFab.style.display = 'flex';
                } else {
                    chatFab.style.display = 'none';
                    if (isChatOpen) toggleChat(); 
                }

                const text = JSON.stringify(data.files);
                document.getElementById('uploadSection').style.display = data.can_upload ? 'block' : 'none';

                if (text === lastDataString) return; 
                lastDataString = text;
                const files = data.files;

                document.querySelectorAll('.checkbox-custom').forEach(cb => {
                    if(cb.checked) selectedFiles.add(cb.value);
                    else selectedFiles.delete(cb.value);
                });

                const listHtml = Object.entries(files).map(([id, info]) => {
                    let li = `<li data-name="${info.name.toLowerCase()}">`;
                    const icon = info.is_folder ? '<span style="font-size:1.8rem">📁</span>' : '<span style="font-size:1.8rem">📄</span>';
                    
                    if (info.is_locked && !info.is_unlocked) {
                        li += `<div class="file-info">
                            <span style="font-size: 2rem; flex-shrink: 0;">🔒</span>
                            <div style="display: flex; flex-direction: column; align-items: flex-start;">
                                <span class="filename" style="color:var(--text-muted);">${info.name}</span>
                                <div class="file-meta-container">
                                    <span class="file-meta">${info.size_formatted}</span>
                                    <span class="file-meta">By ${info.uploader}</span>
                                </div>
                            </div>
                        </div>
                        <a href="/unlock/${id}" class="download-btn unlock-btn">Decrypt</a>`;
                    } else {
                        const isNew = !document.querySelector(`input[value="${id}"]`);
                        const wasChecked = selectedFiles.has(id);
                        const checkedAttr = (wasChecked || isNew) ? 'checked' : '';
                        if (wasChecked || isNew) selectedFiles.add(id);

                        li += `<div class="file-info">
                            <input type="checkbox" name="selected_files" value="${id}" class="checkbox-custom" ${checkedAttr} onchange="filterFiles()">
                            <div style="display: flex; flex-direction: column; align-items: flex-start;">
                                <span class="filename" style="display:flex; align-items:center; gap:10px;">${icon} ${info.name}</span>
                                <div class="file-meta-container">
                                    <span class="file-meta">
                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:4px"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
                                        ${info.size_formatted}
                                    </span>
                                    <span class="file-meta">
                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:4px"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                                        ${info.uploader}
                                    </span>
                                </div>
                            </div>
                        </div>
                        <a href="/download/${id}" class="download-btn" download>
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:6px"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                            Download
                        </a>`;
                    }
                    li += `</li>`;
                    return li;
                }).join('');

                const fileList = document.getElementById('fileList');
                if (Object.keys(files).length === 0) {
                    fileList.innerHTML = '<div class="empty-state">No files or folders are currently being shared.<br><span style="font-size:0.9rem; opacity:0.7; margin-top:10px; display:inline-block">Host can add files, or you can upload if permitted.</span></div>';
                } else {
                    fileList.innerHTML = listHtml;
                }
                
                filterFiles(); 
            } catch(e) {
                console.error("Live update error", e);
            }
        }

        // --- CHAT SYSTEM LOGIC ---
        function toggleChat() {
            const drawer = document.getElementById('chatDrawer');
            isChatOpen = !isChatOpen;
            
            if (isChatOpen) {
                drawer.classList.add('open');
                document.body.style.overflow = window.innerWidth <= 700 ? "hidden" : "";
                document.getElementById('chatTextInput').focus();
                refreshChatUI(true);
            } else {
                drawer.classList.remove('open');
                document.body.style.overflow = "";
            }
        }

        async function fetchChatUpdates() {
            if (!myName) return;
            try {
                const res = await fetch(`/api/chat?last_id=${lastChatId}`);
                const data = await res.json();
                
                let changed = false;
                
                // Process Server-side deletions
                if (data.deleted_everyone) {
                    chatMessagesData.forEach(m => {
                        if (data.deleted_everyone.includes(m.id) && m.content !== '🚫 This message was deleted.') {
                            m.content = '🚫 This message was deleted.';
                            m.type = 'text';
                            m.url = null;
                            changed = true;
                        }
                    });
                }
                if (data.deleted_for_me) {
                    const oldLen = chatMessagesData.length;
                    chatMessagesData = chatMessagesData.filter(m => !data.deleted_for_me.includes(m.id));
                    if (chatMessagesData.length !== oldLen) changed = true;
                }

                if (data.messages && data.messages.length > 0) {
                    chatMessagesData = chatMessagesData.concat(data.messages);
                    lastChatId = data.messages[data.messages.length - 1].id;
                    changed = true;
                }
                
                if (changed && isChatOpen) {
                    // Only auto scroll to bottom if new messages were ADDED, not just deleted
                    refreshChatUI(data.messages && data.messages.length > 0); 
                }
            } catch(e) { console.error("Chat fetch error", e); }
        }

        function formatTime(unixTime) {
            const d = new Date(unixTime * 1000);
            let hours = d.getHours();
            let minutes = d.getMinutes();
            const ampm = hours >= 12 ? 'PM' : 'AM';
            hours = hours % 12;
            hours = hours ? hours : 12; 
            minutes = minutes < 10 ? '0'+minutes : minutes;
            return hours + ':' + minutes + ' ' + ampm;
        }

        function handleChatContext(e, id, isMine) {
            e.preventDefault();
            activeMsgId = id;
            const ctx = document.getElementById('chatCtxMenu');
            ctx.style.display = 'block';
            
            let x = e.clientX || (e.touches && e.touches[0].clientX) || window.innerWidth/2;
            let y = e.clientY || (e.touches && e.touches[0].clientY) || window.innerHeight/2;
            
            if(x + 180 > window.innerWidth) x = window.innerWidth - 190;
            if(y + 120 > window.innerHeight) y = window.innerHeight - 130;

            ctx.style.left = x + 'px';
            ctx.style.top = y + 'px';
            
            document.getElementById('btnDelEveryone').style.display = isMine ? 'block' : 'none';
        }

        async function doDeleteMsg(type) {
            document.getElementById('chatCtxMenu').style.display = 'none';
            if (!activeMsgId) return;
            
            const fd = new FormData();
            fd.append('type', type);
            try {
                await fetch(`/api/chat/delete/${activeMsgId}`, { method: 'POST', body: fd });
                fetchChatUpdates();
            } catch(e) { console.error(e); }
        }

        function refreshChatUI(forceScroll) {
            const container = document.getElementById('chatMessages');
            const target = document.getElementById('chatTarget').value; 
            
            let html = '';
            const relevantMsgs = chatMessagesData.filter(m => {
                if (target === 'group') return m.to === null;
                if (target === 'Host') {
                    return m.to === 'Host' || m.from === 'Host'; 
                }
                return false;
            });

            if(relevantMsgs.length === 0) {
                 html = `<div style="text-align:center; color:#a1a1aa; padding-top:40px;">No messages yet. Send one below to start chatting!</div>`;
            } else {
                relevantMsgs.forEach(m => {
                    const isMine = m.is_mine;
                    const bubbleClass = isMine ? 'msg-my' : 'msg-other';
                    const senderName = isMine ? 'You' : m.from_name;
                    
                    html += `<div class="msg-bubble ${bubbleClass}" oncontextmenu="handleChatContext(event, ${m.id}, ${isMine})">`;
                    if (!isMine && target === 'group') {
                        html += `<span class="msg-sender">${senderName}</span>`;
                    }
                    
                    if (m.type === 'text') {
                        html += `<span>${m.content}</span>`;
                    } else if (m.type === 'image') {
                        html += `<img src="${m.url}" class="msg-media" onclick="window.open('${m.url}', '_blank')">`;
                        if (m.content) html += `<div style="margin-top:5px">${m.content}</div>`;
                    } else if (m.type === 'video') {
                        html += `<video src="${m.url}" controls class="msg-media"></video>`;
                        if (m.content) html += `<div style="margin-top:5px">${m.content}</div>`;
                    } else if (m.type === 'lan_file') {
                        // Premium layout for LAN file injections
                        html += `<div class="msg-file-link" style="background: rgba(16,185,129,0.1); border-color: #10b981; display:flex; align-items:center; gap:12px; margin-top:0;">
                                    <span style="font-size:1.8rem">📁</span>
                                    <div style="flex:1; overflow:hidden;">
                                        <div style="font-weight:bold; white-space:nowrap; text-overflow:ellipsis; overflow:hidden;">${m.filename}</div>
                                        <div style="font-size:0.75rem; opacity:0.8; color: #10b981; margin-top:2px;">LAN Shared File</div>
                                    </div>
                                    <a href="${m.url}" class="download-btn" style="padding: 10px 14px; font-size: 0.85rem;" download>⬇️ Get</a>
                                 </div>`;
                    } else {
                        // Regular File
                        html += `<a href="${m.url}" class="msg-file-link" download>
                                    📄 ${m.filename}
                                 </a>`;
                        if (m.content) html += `<div style="margin-top:5px">${m.content}</div>`;
                    }
                    
                    html += `<span class="msg-time">${formatTime(m.time)}</span></div>`;
                });
            }
            
            // Re-inject the temporary loading bubble if an upload is currently happening
            if (document.getElementById('tempUploadIndicator')) {
                html += `<div id="tempUploadIndicator" class="msg-bubble msg-my"><span style="opacity:0.7">Uploading file(s)... ⏳</span></div>`;
            }

            container.innerHTML = html;
            if (forceScroll) {
                container.scrollTop = container.scrollHeight;
            }
        }

        async function sendChatMsg() {
            const input = document.getElementById('chatTextInput');
            const text = input.value.trim();
            if (!text) return;
            
            const target = document.getElementById('chatTarget').value;
            const to_ip = target === 'group' ? '' : target;
            
            input.value = '';
            
            const fd = new FormData();
            fd.append('text', text);
            fd.append('to_ip', to_ip);
            fd.append('from_name', myName);

            try {
                await fetch('/api/chat/send', { method: 'POST', body: fd });
                fetchChatUpdates(); 
            } catch(e) { console.error(e); }
        }

        function showUploadChoice() {
            const fileInput = document.getElementById('chatFileInput');
            if (!fileInput.files.length) return;
            const names = Array.from(fileInput.files).map(f => f.name).join(', ');
            document.getElementById('choiceFilePreview').innerText = fileInput.files.length + ' file(s): ' + names;
            document.getElementById('uploadChoiceModal').classList.add('active');
        }

        function cancelUploadChoice() {
            document.getElementById('uploadChoiceModal').classList.remove('active');
            document.getElementById('chatFileInput').value = '';
        }

        async function executeUpload(mode) {
            document.getElementById('uploadChoiceModal').classList.remove('active');
            
            const fileInput = document.getElementById('chatFileInput');
            if (!fileInput.files.length) return;
            
            const target = document.getElementById('chatTarget').value;
            const to_ip = target === 'group' ? '' : target;
            
            const fd = new FormData();
            fd.append('to_ip', to_ip);
            fd.append('from_name', myName);
            fd.append('mode', mode); // 'chat' or 'lan'
            for(let i=0; i<fileInput.files.length; i++){
                fd.append('files', fileInput.files[i]);
            }
            
            // Show temporary loading indicator in chat
            const container = document.getElementById('chatMessages');
            container.innerHTML += `<div id="tempUploadIndicator" class="msg-bubble msg-my"><span style="opacity:0.7">Uploading file(s)... ⏳</span></div>`;
            container.scrollTop = container.scrollHeight;
            
            try {
                await fetch('/api/chat/upload', { method: 'POST', body: fd });
            } catch(e) { 
                console.error(e); 
            } finally {
                const tempInd = document.getElementById('tempUploadIndicator');
                if (tempInd) tempInd.remove();
                fileInput.value = ''; // clear
                fetchUpdates();
                fetchChatUpdates();
            }
        }

        setInterval(fetchUpdates, 2000);
        setInterval(fetchChatUpdates, 1500);
    </script>
</body>
</html>
"""

# --- CHAT HELPER FUNCTIONS ---
def get_chat_messages_for_ip(ip, last_id):
    """Filters chat messages so a client only gets Group + their own PMs, minus their deleted ones."""
    res = []
    hidden_ids = DELETED_FOR_ME.get(ip, set())
    
    for m in CHAT_MESSAGES:
        if m['id'] > last_id:
            if m['id'] in hidden_ids:
                continue
                
            # Group message
            if m['to'] is None:
                res_m = dict(m)
                res_m['is_mine'] = (m['from'] == ip)
                res.append(res_m)
            # Private message involving this IP
            elif m['to'] == ip or m['from'] == ip:
                res_m = dict(m)
                res_m['is_mine'] = (m['from'] == ip)
                res.append(res_m)
    return res

@app.before_request
def check_kick_or_login():
    if request.endpoint == 'login' or request.endpoint == 'static':
        return
        
    if SERVER_STATE.get('is_secure') and request.cookies.get('lan_auth_pin') != SERVER_STATE.get('pin'):
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if not SERVER_STATE.get('is_secure'):
        return redirect(url_for('index'))

    pin_arg = request.args.get('pin')
    if pin_arg and pin_arg == SERVER_STATE['pin']:
        log_system_event(request.remote_addr, "🔓 Auto-login via Secure QR.", request.headers.get('User-Agent', ''))
        resp = make_response(redirect(url_for('index')))
        resp.set_cookie('lan_auth_pin', SERVER_STATE['pin'])
        return resp

    if request.method == 'POST':
        pin_post = request.form.get('pin')
        if pin_post == SERVER_STATE['pin']:
            log_system_event(request.remote_addr, "🔓 Authenticated via PIN.", request.headers.get('User-Agent', ''))
            resp = make_response(redirect(url_for('index')))
            resp.set_cookie('lan_auth_pin', SERVER_STATE['pin'])
            return resp
        else:
            log_system_event(request.remote_addr, "❌ Failed Auth (Wrong PIN).", request.headers.get('User-Agent', ''))
            return render_template_string(LOGIN_TEMPLATE, error="Invalid PIN.", host_name=SERVER_STATE['host_name'])

    return render_template_string(LOGIN_TEMPLATE, error=None, host_name=SERVER_STATE['host_name'])

@app.route('/')
def index():
    log_system_event(request.remote_addr, "👀 Viewed the shared list.", request.headers.get('User-Agent', ''))
    return render_template_string(HTML_TEMPLATE, host_name=SERVER_STATE['host_name'], is_secure=SERVER_STATE['is_secure'])

@app.route('/api/files')
def api_files():
    ip = request.remote_addr
    if ip in SERVER_STATE.get('pending_kicks', set()):
        SERVER_STATE['pending_kicks'].remove(ip)
        return jsonify({"kicked": True})

    client_name = request.args.get('u', '').strip()
    log_system_event(ip, "🔄 Polling API", request.headers.get('User-Agent', ''), client_name)
    
    unlocked = session.get('unlocked', [])
    files_data = {
        fid: {
            'name': info['name'],
            'size_formatted': info.get('size_formatted', 'Unknown Size'),
            'is_locked': bool(info['pin']),
            'is_unlocked': fid in unlocked,
            'uploader': info.get('uploader', 'Unknown'),
            'is_folder': info.get('is_folder', False)
        }
        for fid, info in shared_files.items()
    }
    
    can_up = True
    if ip in SERVER_STATE['users']:
        can_up = SERVER_STATE['users'][ip]['can_upload']

    return jsonify({
        "files": files_data, 
        "can_upload": can_up, 
        "host_name": SERVER_STATE['host_name'],
        "chat_enabled": SERVER_STATE['chat_enabled']
    })

# --- CHAT API ROUTES ---
@app.route('/api/chat', methods=['GET'])
def api_get_chat():
    ip = request.remote_addr
    last_id = int(request.args.get('last_id', 0))
    msgs = get_chat_messages_for_ip(ip, last_id)
    
    # Return new messages alongside deleted histories to perfectly sync client state
    return jsonify({
        "messages": msgs,
        "deleted_everyone": list(DELETED_EVERYONE),
        "deleted_for_me": list(DELETED_FOR_ME.get(ip, set()))
    })

@app.route('/api/chat/delete/<int:msg_id>', methods=['POST'])
def api_delete_chat(msg_id):
    ip = request.remote_addr
    del_type = request.form.get('type')
    
    if del_type == "everyone":
        for m in CHAT_MESSAGES:
            if m['id'] == msg_id:
                if m['from'] == ip or ip == "Host":
                    DELETED_EVERYONE.add(msg_id)
                    m['content'] = '🚫 This message was deleted.'
                    m['type'] = 'text'
                    m['url'] = None
                    m['filename'] = None
                    gui_command_queue.put("refresh_chat_ui")
                    return jsonify({"success": True})
        return jsonify({"error": "Unauthorized"}), 403
        
    elif del_type == "me":
        if ip not in DELETED_FOR_ME:
            DELETED_FOR_ME[ip] = set()
        DELETED_FOR_ME[ip].add(msg_id)
        return jsonify({"success": True})
        
    return jsonify({"error": "Invalid type"}), 400

@app.route('/api/chat/send', methods=['POST'])
def api_send_chat():
    global chat_msg_id_counter
    ip = request.remote_addr
    text = request.form.get('text', '').strip()
    to_ip = request.form.get('to_ip', '').strip() or None
    from_name = request.form.get('from_name', '').strip() or SERVER_STATE['users'].get(ip, {}).get('name', 'Unknown')
    
    if text:
        msg = {
            'id': chat_msg_id_counter,
            'from': ip,
            'from_name': from_name,
            'to': to_ip,
            'type': 'text',
            'content': text,
            'url': None,
            'filename': None,
            'time': time.time()
        }
        CHAT_MESSAGES.append(msg)
        chat_msg_id_counter += 1
        gui_command_queue.put("refresh_chat_ui")
    return jsonify({"success": True})

@app.route('/api/chat/upload', methods=['POST'])
def api_upload_chat_file():
    global chat_msg_id_counter
    ip = request.remote_addr
    to_ip = request.form.get('to_ip', '').strip() or None
    from_name = request.form.get('from_name', '').strip() or SERVER_STATE['users'].get(ip, {}).get('name', 'Unknown')
    mode = request.form.get('mode', 'chat')
    
    files = request.files.getlist('files')
    if not files: return jsonify({"error": "No files"}), 400

    if mode == 'lan':
        # Direct integration for rich LAN Shared Files inside the Chat
        for file in files:
            if not file.filename: continue
            filename = file.filename
            filepath = os.path.join(UPLOAD_DIR, filename)
            
            if os.path.exists(filepath):
                name, ext = os.path.splitext(filename)
                filename = f"{name}_{str(uuid.uuid4())[:6]}{ext}"
                filepath = os.path.join(UPLOAD_DIR, filename)
                
            file.save(filepath)
            
            file_id = str(uuid.uuid4())
            shared_files[file_id] = {
                'name': filename,
                'path': filepath,
                'pin': None,
                'size_formatted': format_size(get_actual_size(filepath)),
                'uploader': from_name,
                'is_folder': False
            }
            
            msg = {
                'id': chat_msg_id_counter,
                'from': ip,
                'from_name': from_name,
                'to': to_ip,
                'type': 'lan_file',
                'content': None,
                'url': f"/download/{file_id}",
                'filename': filename,
                'time': time.time()
            }
            CHAT_MESSAGES.append(msg)
            chat_msg_id_counter += 1
            
        gui_command_queue.put("refresh_files")
        gui_command_queue.put("refresh_chat_ui")
        return jsonify({"success": True})

    # Standard Chat Media Processing (Non-LAN)
    if len(files) > 1:
        zip_filename = f"SharedFolder_{uuid.uuid4().hex[:6]}.zip"
        zip_path = os.path.join(CHAT_DIR, zip_filename)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in files:
                if f.filename:
                    f.save(os.path.join(tempfile.gettempdir(), f.filename))
                    zf.write(os.path.join(tempfile.gettempdir(), f.filename), arcname=f.filename)
        
        msg = {
            'id': chat_msg_id_counter,
            'from': ip,
            'from_name': from_name,
            'to': to_ip,
            'type': 'file',
            'content': f"Sent {len(files)} files as Folder Archive",
            'url': f"/chat_media/{zip_filename}",
            'filename': zip_filename,
            'time': time.time()
        }
    else:
        file = files[0]
        if not file.filename: return jsonify({"error": "No file name"}), 400
        
        filename = file.filename
        safe_name = f"{uuid.uuid4().hex[:6]}_{filename}"
        filepath = os.path.join(CHAT_DIR, safe_name)
        file.save(filepath)

        mime_type, _ = mimetypes.guess_type(filename)
        msg_type = 'file'
        if mime_type:
            if mime_type.startswith('image/'): msg_type = 'image'
            elif mime_type.startswith('video/'): msg_type = 'video'

        msg = {
            'id': chat_msg_id_counter,
            'from': ip,
            'from_name': from_name,
            'to': to_ip,
            'type': msg_type,
            'content': None,
            'url': f"/chat_media/{safe_name}",
            'filename': filename,
            'time': time.time()
        }

    CHAT_MESSAGES.append(msg)
    chat_msg_id_counter += 1
    gui_command_queue.put("refresh_chat_ui")
    return jsonify({"success": True})

@app.route('/chat_media/<filename>')
def serve_chat_media(filename):
    return send_file(os.path.join(CHAT_DIR, filename))

# --- STANDARD FILE ROUTES ---
@app.route('/upload', methods=['POST'])
def upload_file():
    ip = request.remote_addr
    if ip in SERVER_STATE['users'] and not SERVER_STATE['users'][ip]['can_upload']:
        return "Upload Permission Denied", 403

    if 'file' not in request.files: return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '': return redirect(url_for('index'))
        
    if file:
        filename = file.filename
        filepath = os.path.join(UPLOAD_DIR, filename)
        
        if os.path.exists(filepath):
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{str(uuid.uuid4())[:6]}{ext}"
            filepath = os.path.join(UPLOAD_DIR, filename)
            
        file.save(filepath)
        
        file_id = str(uuid.uuid4())
        size_formatted = format_size(get_actual_size(filepath))
        uploader_name = request.form.get('uploader_name', '').strip() or SERVER_STATE['users'].get(ip, {}).get('name', 'Unknown')
        
        shared_files[file_id] = {
            'name': filename,
            'path': filepath,
            'pin': None,
            'size_formatted': size_formatted,
            'uploader': uploader_name,
            'is_folder': False
        }
        
        log_system_event(ip, f"📤 Uploaded file: {filename}", request.headers.get('User-Agent', ''), uploader_name)
        gui_command_queue.put("refresh_files")
        
        return redirect(url_for('index'))

@app.route('/unlock/<file_id>', methods=['GET', 'POST'])
def unlock_file(file_id):
    if file_id not in shared_files: abort(404)
    file_info = shared_files[file_id]
    
    if request.method == 'POST':
        pin_post = request.form.get('pin')
        if pin_post == file_info['pin']:
            unlocked = session.get('unlocked', [])
            if file_id not in unlocked:
                unlocked.append(file_id)
                session['unlocked'] = unlocked
            log_system_event(request.remote_addr, f"🔓 Unlocked: {file_info['name']}")
            return redirect(url_for('index'))
        else:
            return render_template_string(UNLOCK_TEMPLATE, error="Invalid PIN. Try again.", file_name=file_info['name'])
            
    return render_template_string(UNLOCK_TEMPLATE, error=None, file_name=file_info['name'])

@app.route('/download/<file_id>')
def download_file(file_id):
    if file_id not in shared_files: abort(404)
    file_info = shared_files[file_id]
    
    if file_info['pin'] and file_id not in session.get('unlocked', []):
        return redirect(url_for('unlock_file', file_id=file_id))
        
    file_path = file_info['path']
    if not os.path.exists(file_path): abort(404)

    log_system_event(request.remote_addr, f"⬇️ Started downloading: {file_info['name']}")

    if file_info.get('is_folder'):
        temp_dir = tempfile.gettempdir()
        zip_path = os.path.join(temp_dir, f"{file_info['name']}_{uuid.uuid4().hex[:6]}")
        shutil.make_archive(zip_path, 'zip', file_path)
        return send_file(zip_path + ".zip", as_attachment=True, download_name=f"{file_info['name']}.zip")
    else:
        def generate_file_chunks():
            try:
                with open(file_path, 'rb') as f:
                    while True:
                        if file_id not in shared_files:
                            break
                        chunk = f.read(8192)
                        if not chunk: break
                        yield chunk
            except Exception as e: print(f"Streaming error: {e}")

        response = Response(stream_with_context(generate_file_chunks()))
        response.headers['Content-Disposition'] = f'attachment; filename="{file_info["name"]}"'
        response.headers['Content-Type'] = 'application/octet-stream'
        response.headers['Content-Length'] = os.path.getsize(file_path)
        return response

@app.route('/download_selected', methods=['POST'])
def download_selected():
    selected_ids = request.form.getlist('selected_files')
    valid_ids = [fid for fid in selected_ids if fid in shared_files and (not shared_files[fid]['pin'] or fid in session.get('unlocked', []))]
    
    if not valid_ids: return "No valid/unlocked files selected.", 400
    if len(valid_ids) == 1: return redirect(url_for('download_file', file_id=valid_ids[0]))

    log_system_event(request.remote_addr, f"📦 Generating bulk ZIP for {len(valid_ids)} items.")
    temp_dir = tempfile.gettempdir()
    zip_path = os.path.join(temp_dir, f"bulk_download_{uuid.uuid4().hex[:6]}.zip")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f_id in valid_ids:
            info = shared_files[f_id]
            path = info['path']
            if not os.path.exists(path): continue

            if info.get('is_folder'):
                for root, _, files in os.walk(path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.join(info['name'], os.path.relpath(file_path, path))
                        zf.write(file_path, arcname)
            else:
                zf.write(path, arcname=info['name'])
    
    return send_file(zip_path, as_attachment=True, download_name='shared_files.zip')

# --- SERVER THREAD CLASS ---
class ServerThread(threading.Thread):
    def __init__(self, app, host, port):
        threading.Thread.__init__(self)
        self.server = make_server(host, port, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()

# --- MAIN GUI APP ---
class LANShareApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("👑 My LAN File Sharer - Premium Edition")
        self.geometry("1150x850")
        self.minsize(950, 650)
        
        # Set window icon
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lan.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
        
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.server_thread = None
        self.is_running = False
        self.port_var = tk.StringVar(value="5000")
        self.host_name_var = tk.StringVar(value="Admin")
        
        self.secure_mode_var = tk.BooleanVar(value=False)
        self.server_pin_var = tk.StringVar(value="")

        self.direct_access_url = ""
        self.user_widgets = {} 
        self.chat_target_ip = None # None = Group

        self.setup_ui()
        self.process_logs() 
        
    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def setup_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Main Tabview
        self.tabview = ctk.CTkTabview(self, corner_radius=15)
        self.tabview.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        
        self.tab_dashboard = self.tabview.add("📊 Dashboard & Settings")
        self.tab_chat = self.tabview.add("💬 Live Chat Hub")
        
        self.setup_dashboard_tab()
        self.setup_chat_tab()

    def setup_dashboard_tab(self):
        self.tab_dashboard.grid_rowconfigure(0, weight=6) 
        self.tab_dashboard.grid_rowconfigure(1, weight=4) 
        self.tab_dashboard.grid_columnconfigure(0, weight=4) 
        self.tab_dashboard.grid_columnconfigure(1, weight=3) 

        # ==================== TOP LEFT FRAME (File Management) ====================
        self.left_frame = ctk.CTkFrame(self.tab_dashboard, corner_radius=16, fg_color="#18181b", border_width=1, border_color="#27272a")
        self.left_frame.grid(row=0, column=0, padx=(10, 5), pady=(10, 5), sticky="nsew")
        self.left_frame.grid_rowconfigure(1, weight=1)
        self.left_frame.grid_columnconfigure(0, weight=1)

        header_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        self.lbl_files = ctk.CTkLabel(header_frame, text="📁 Shared Files", font=ctk.CTkFont(size=22, weight="bold"))
        self.lbl_files.pack(side="left")

        self.btn_open_uploads = ctk.CTkButton(header_frame, text="📂 Open Dir", command=self.open_uploads_folder, width=100, fg_color="#3f3f46", hover_color="#52525b")
        self.btn_open_uploads.pack(side="right")

        self.file_list_frame = ctk.CTkScrollableFrame(self.left_frame, fg_color="transparent")
        self.file_list_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.btn_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.btn_frame.grid(row=2, column=0, padx=20, pady=20, sticky="ew")
        self.btn_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.btn_add_file = ctk.CTkButton(self.btn_frame, text="+ Files", command=self.add_files, height=40, font=ctk.CTkFont(weight="bold"), fg_color="#4f46e5", hover_color="#4338ca")
        self.btn_add_file.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.btn_add_folder = ctk.CTkButton(self.btn_frame, text="+ Folder", command=self.add_folder, height=40, fg_color="#0284c7", hover_color="#0369a1", font=ctk.CTkFont(weight="bold"))
        self.btn_add_folder.grid(row=0, column=1, padx=5, sticky="ew")

        self.btn_clear = ctk.CTkButton(self.btn_frame, text="Trash All", command=self.clear_files, fg_color="#ef4444", hover_color="#dc2626", height=40, font=ctk.CTkFont(weight="bold"))
        self.btn_clear.grid(row=0, column=2, padx=(5, 0), sticky="ew")

        # ==================== TOP RIGHT FRAME (Server Controls) ====================
        self.right_frame = ctk.CTkScrollableFrame(self.tab_dashboard, corner_radius=16, fg_color="#18181b", border_width=1, border_color="#27272a")
        self.right_frame.grid(row=0, column=1, padx=(5, 10), pady=(10, 5), sticky="nsew")
        self.right_frame.grid_columnconfigure(0, weight=1)

        self.lbl_server = ctk.CTkLabel(self.right_frame, text="⚙️ Premium Settings", font=ctk.CTkFont(size=22, weight="bold"))
        self.lbl_server.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")

        self.settings_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.settings_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.settings_frame.grid_columnconfigure(1, weight=1)
        
        self.lbl_name = ctk.CTkLabel(self.settings_frame, text="Host Name:", font=ctk.CTkFont(weight="bold"))
        self.lbl_name.grid(row=0, column=0, padx=5, pady=8, sticky="w")
        
        name_input_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        name_input_frame.grid(row=0, column=1, padx=5, pady=8, sticky="e")
        self.entry_name = ctk.CTkEntry(name_input_frame, textvariable=self.host_name_var, width=120)
        self.entry_name.pack(side="left", padx=(0,5))
        self.btn_update_name = ctk.CTkButton(name_input_frame, text="Upd", width=40, fg_color="#0ea5e9", hover_color="#0284c7", command=self.update_host_name_live)
        self.btn_update_name.pack(side="left")

        self.lbl_port = ctk.CTkLabel(self.settings_frame, text="Port:", font=ctk.CTkFont(weight="bold"))
        self.lbl_port.grid(row=1, column=0, padx=5, pady=8, sticky="w")
        self.entry_port = ctk.CTkComboBox(self.settings_frame, variable=self.port_var, values=["5000", "8000", "8080", "8888", "9000"], width=165)
        self.entry_port.grid(row=1, column=1, padx=5, pady=8, sticky="e")

        self.switch_secure = ctk.CTkSwitch(self.settings_frame, text="Secure Mode", variable=self.secure_mode_var, command=self.toggle_secure_ui, progress_color="#10b981")
        self.switch_secure.grid(row=2, column=0, padx=5, pady=15, sticky="w")
        self.entry_server_pin = ctk.CTkEntry(self.settings_frame, textvariable=self.server_pin_var, width=80, placeholder_text="PIN", state="disabled")
        self.entry_server_pin.grid(row=2, column=1, padx=5, pady=15, sticky="e")

        # Chat toggle
        self.btn_toggle_chat = ctk.CTkButton(self.right_frame, text="💬 Start Live Chat Room", fg_color="#6366f1", hover_color="#4f46e5", height=40, command=self.toggle_global_chat)
        self.btn_toggle_chat.grid(row=3, column=0, padx=20, pady=5, sticky="ew")

        self.btn_start_stop = ctk.CTkButton(self.right_frame, text="🚀 Start Server", command=self.toggle_server, height=50, font=ctk.CTkFont(size=17, weight="bold"), fg_color="#10b981", hover_color="#059669", corner_radius=12)
        self.btn_start_stop.grid(row=4, column=0, padx=20, pady=15, sticky="ew")

        self.status_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.status_frame.grid(row=5, column=0, padx=20, pady=5, sticky="nsew")
        self.status_frame.grid_columnconfigure(0, weight=1)
        
        self.lbl_url = ctk.CTkLabel(self.status_frame, text="Status: Offline", text_color="#a1a1aa", font=ctk.CTkFont(size=14))
        self.lbl_url.grid(row=0, column=0, pady=(0, 10))

        link_btns_frame = ctk.CTkFrame(self.status_frame, fg_color="transparent")
        link_btns_frame.grid(row=1, column=0, pady=(0, 15))
        
        self.btn_copy_link = ctk.CTkButton(link_btns_frame, text="📋 Link", command=self.copy_link, height=35, width=80, state="disabled", fg_color="#3f3f46", hover_color="#52525b")
        self.btn_copy_link.pack(side="left", padx=5)

        self.btn_open_web = ctk.CTkButton(link_btns_frame, text="🌐 Web", command=self.open_web_view, height=35, width=80, state="disabled", fg_color="#0284c7", hover_color="#0369a1")
        self.btn_open_web.pack(side="left", padx=5)

        self.qr_label = ctk.CTkLabel(self.status_frame, text="", cursor="hand2")
        self.qr_label.grid(row=2, column=0, pady=10)
        self.qr_label.bind("<Button-1>", lambda e: self.show_large_qr())

        # ==================== BOTTOM FRAME (Activity Log & Users) ====================
        self.activity_frame = ctk.CTkFrame(self.tab_dashboard, corner_radius=16, fg_color="#18181b", border_width=1, border_color="#27272a")
        self.activity_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=(5, 10), sticky="nsew")
        
        self.activity_frame.grid_columnconfigure(0, weight=5) 
        self.activity_frame.grid_columnconfigure(1, weight=4) 
        self.activity_frame.grid_rowconfigure(1, weight=1)

        self.lbl_activity = ctk.CTkLabel(self.activity_frame, text="⚡ Live Server Logs", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_activity.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        self.lbl_users = ctk.CTkLabel(self.activity_frame, text="📱 Network Devices (0)", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_users.grid(row=0, column=1, padx=20, pady=10, sticky="w")

        self.txt_logs = ctk.CTkTextbox(self.activity_frame, state="disabled", font=ctk.CTkFont(family="Consolas", size=13), fg_color="#09090b", text_color="#34d399", border_width=1, border_color="#27272a", corner_radius=10)
        self.txt_logs.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        self.users_frame = ctk.CTkScrollableFrame(self.activity_frame, fg_color="#09090b", corner_radius=10, border_width=1, border_color="#27272a")
        self.users_frame.grid(row=1, column=1, padx=(0, 20), pady=(0, 20), sticky="nsew")

    def setup_chat_tab(self):
        self.tab_chat.grid_rowconfigure(0, weight=1)
        self.tab_chat.grid_columnconfigure(0, weight=2) # List side
        self.tab_chat.grid_columnconfigure(1, weight=6) # Chat side

        # Left: Chat List
        self.chat_list_frame = ctk.CTkScrollableFrame(self.tab_chat, fg_color="#18181b", corner_radius=16, border_width=1, border_color="#27272a")
        self.chat_list_frame.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")

        self.lbl_chat_list = ctk.CTkLabel(self.chat_list_frame, text="Conversations", font=ctk.CTkFont(size=20, weight="bold"))
        self.lbl_chat_list.pack(pady=10, padx=10, anchor="w")

        # Fixed Group Button
        self.btn_chat_group = ctk.CTkButton(self.chat_list_frame, text="🌐 Global Group", fg_color="#4f46e5", height=45, anchor="w", font=ctk.CTkFont(weight="bold", size=14), command=lambda: self.switch_chat_target(None))
        self.btn_chat_group.pack(fill="x", padx=10, pady=5)
        
        self.chat_users_container = ctk.CTkFrame(self.chat_list_frame, fg_color="transparent")
        self.chat_users_container.pack(fill="both", expand=True)
        self.chat_user_btns = {} # IP -> CTkButton

        # Right: Chat Messages & Input
        self.chat_main_frame = ctk.CTkFrame(self.tab_chat, fg_color="#18181b", corner_radius=16, border_width=1, border_color="#27272a")
        self.chat_main_frame.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="nsew")
        self.chat_main_frame.grid_rowconfigure(1, weight=1)
        self.chat_main_frame.grid_columnconfigure(0, weight=1)

        self.lbl_current_chat = ctk.CTkLabel(self.chat_main_frame, text="🌐 Global Group Chat", font=ctk.CTkFont(size=22, weight="bold"))
        self.lbl_current_chat.grid(row=0, column=0, padx=20, pady=15, sticky="w")

        self.chat_messages_frame = ctk.CTkScrollableFrame(self.chat_main_frame, fg_color="#0b1120", corner_radius=10)
        self.chat_messages_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="nsew")

        # Input Area
        input_area = ctk.CTkFrame(self.chat_main_frame, fg_color="transparent", height=60)
        input_area.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        input_area.grid_columnconfigure(1, weight=1)

        self.btn_chat_attach = ctk.CTkButton(input_area, text="📎", width=45, height=45, font=ctk.CTkFont(size=20), fg_color="#3f3f46", hover_color="#52525b", command=self.host_chat_attach)
        self.btn_chat_attach.grid(row=0, column=0, padx=(0, 10))

        self.chat_input_var = tk.StringVar()
        self.entry_chat = ctk.CTkEntry(input_area, textvariable=self.chat_input_var, height=45, font=ctk.CTkFont(size=15), placeholder_text="Type a message...")
        self.entry_chat.grid(row=0, column=1, sticky="ew")
        self.entry_chat.bind("<Return>", lambda e: self.host_chat_send())

        self.btn_chat_send = ctk.CTkButton(input_area, text="Send ➤", width=80, height=45, font=ctk.CTkFont(weight="bold", size=15), command=self.host_chat_send)
        self.btn_chat_send.grid(row=0, column=2, padx=(10, 0))

    def toggle_global_chat(self):
        if not SERVER_STATE['chat_enabled']:
            conf = messagebox.askyesno("Start Chat", "Enable the Live Chat room for all connected devices?", parent=self)
            if conf:
                SERVER_STATE['chat_enabled'] = True
                self.btn_toggle_chat.configure(text="🛑 Stop Live Chat", fg_color="#ef4444", hover_color="#dc2626")
                self.append_log("💬 Live Chat features ENABLED globally.")
        else:
            SERVER_STATE['chat_enabled'] = False
            self.btn_toggle_chat.configure(text="💬 Start Live Chat Room", fg_color="#6366f1", hover_color="#4f46e5")
            self.append_log("💬 Live Chat features DISABLED globally.")

    def open_uploads_folder(self):
        try:
            if platform.system() == "Windows": os.startfile(UPLOAD_DIR)
            elif platform.system() == "Darwin": subprocess.Popen(["open", UPLOAD_DIR])
            else: subprocess.Popen(["xdg-open", UPLOAD_DIR])
            self.append_log("📂 Opened Uploads Directory.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder: {e}")

    def update_host_name_live(self):
        new_name = self.host_name_var.get().strip()
        if new_name:
            SERVER_STATE['host_name'] = new_name
            self.append_log(f"🔄 Host Name updated dynamically to: 👑 {new_name}")
            gui_command_queue.put("refresh_files") 
        else:
            messagebox.showwarning("Warning", "Host name cannot be empty.")

    def open_web_view(self):
        if self.is_running and self.direct_access_url:
            webbrowser.open(self.direct_access_url)

    def get_file_icon(self, filepath, is_folder=False):
        if is_folder: return None, "📁"
        ext = os.path.splitext(filepath)[1].lower()
        if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            try:
                img = Image.open(filepath)
                img.thumbnail((45, 45))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(45, 45))
                return ctk_img, ""
            except Exception: return None, "🖼️"
        elif ext in ['.mp4', '.mkv', '.avi', '.mov']: return None, "🎬"
        elif ext in ['.mp3', '.wav', '.flac']: return None, "🎵"
        elif ext in ['.zip', '.rar', '.tar', '.gz', '.7z']: return None, "🗜️"
        elif ext in ['.txt', '.pdf', '.doc', '.docx', '.csv']: return None, "📄"
        else: return None, "📄"

    def toggle_secure_ui(self):
        if self.secure_mode_var.get():
            self.entry_server_pin.configure(state="normal")
            if not self.server_pin_var.get():
                self.server_pin_var.set(str(random.randint(1000, 9999)))
        else:
            self.entry_server_pin.configure(state="disabled")

    def add_files(self):
        file_paths = filedialog.askopenfilenames(title="Select files to share")
        if file_paths:
            for path in file_paths:
                file_id = str(uuid.uuid4())
                shared_files[file_id] = {
                    'name': os.path.basename(path), 
                    'path': path, 
                    'pin': None, 
                    'size_formatted': format_size(get_actual_size(path)), 
                    'uploader': "👑 " + SERVER_STATE['host_name'],
                    'is_folder': False
                }
            self.refresh_file_list()

    def add_folder(self):
        folder_path = filedialog.askdirectory(title="Select folder to share")
        if folder_path:
            file_id = str(uuid.uuid4())
            def async_folder_add():
                size = get_actual_size(folder_path)
                shared_files[file_id] = {
                    'name': os.path.basename(folder_path), 
                    'path': folder_path, 
                    'pin': None, 
                    'size_formatted': format_size(size), 
                    'uploader': "👑 " + SERVER_STATE['host_name'],
                    'is_folder': True
                }
                gui_command_queue.put("refresh_files")
            threading.Thread(target=async_folder_add, daemon=True).start()

    def clear_files(self):
        shared_files.clear()
        self.refresh_file_list()
        self.append_log("🛑 Cleared all files from share list.")

    def remove_file(self, file_id):
        if file_id in shared_files:
            name = shared_files[file_id]['name']
            del shared_files[file_id]
            self.refresh_file_list()
            self.append_log(f"🛑 Removed '{name}'.")

    def download_file_locally(self, file_id):
        file_info = shared_files.get(file_id)
        if not file_info: return
        src_path = file_info['path']
        if not os.path.exists(src_path):
            messagebox.showerror("Error", "Source file no longer exists.")
            return

        if file_info.get('is_folder'):
            self.open_uploads_folder()
            return
            
        dest_path = filedialog.asksaveasfilename(initialfile=file_info['name'], title="Save file to...")
        if dest_path:
            try:
                shutil.copy2(src_path, dest_path)
                self.append_log(f"💾 Host saved a local copy of: {file_info['name']}")
                messagebox.showinfo("Success", f"File saved successfully to:\n{dest_path}")
            except Exception as e: messagebox.showerror("Error", f"Failed to save file: {e}")

    def toggle_pin(self, file_id, btn_reference):
        current_pin = shared_files[file_id].get('pin')
        file_name = shared_files[file_id]['name']

        if current_pin:
            shared_files[file_id]['pin'] = None
            btn_reference.configure(text="🔓", fg_color="#3b82f6", hover_color="#2563eb")
            self.append_log(f"🔓 Removed File PIN for '{file_name}'")
        else:
            dialog = ctk.CTkInputDialog(text=f"Set a numeric PIN (Min 4 digits) for:\n{file_name}", title="Set File Lock")
            pin = dialog.get_input()
            if pin is not None:
                if pin.isdigit() and len(pin) >= 4:
                    shared_files[file_id]['pin'] = pin
                    btn_reference.configure(text="🔒", fg_color="#f59e0b", hover_color="#d97706")
                    self.append_log(f"🔒 Set File PIN for '{file_name}'")
                else: messagebox.showwarning("Invalid PIN", "The PIN must be at least 4 numeric digits.", parent=self)

    def refresh_file_list(self):
        for widget in self.file_list_frame.winfo_children(): widget.destroy()
        if not shared_files:
            lbl = ctk.CTkLabel(self.file_list_frame, text="No files or folders added yet.", text_color="gray", font=ctk.CTkFont(size=14))
            lbl.pack(pady=40)
            return

        for file_id, file_info in shared_files.items():
            item_frame = ctk.CTkFrame(self.file_list_frame, fg_color="#27272a", corner_radius=12, border_width=1, border_color="#3f3f46")
            item_frame.pack(fill="x", padx=5, pady=6)
            
            img_preview, text_preview = self.get_file_icon(file_info['path'], file_info.get('is_folder'))
            if img_preview:
                lbl_icon = ctk.CTkLabel(item_frame, image=img_preview, text="")
                lbl_icon.image = img_preview 
            else:
                lbl_icon = ctk.CTkLabel(item_frame, text=text_preview, font=ctk.CTkFont(size=30))
            lbl_icon.pack(side="left", padx=15, pady=12)

            info_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=12)
            
            lbl_name = ctk.CTkLabel(info_frame, text=file_info['name'], font=ctk.CTkFont(size=15, weight="bold"), anchor="w")
            lbl_name.pack(fill="x")
            
            meta_text = f"By {file_info.get('uploader', 'Unknown')} • {file_info.get('size_formatted', 'Unknown')}"
            lbl_meta = ctk.CTkLabel(info_frame, text=meta_text, font=ctk.CTkFont(size=12), text_color="#a1a1aa", anchor="w")
            lbl_meta.pack(fill="x")

            btn_remove = ctk.CTkButton(item_frame, text="X", width=35, fg_color="#ef4444", hover_color="#dc2626", font=ctk.CTkFont(weight="bold"), command=lambda f_id=file_id: self.remove_file(f_id))
            btn_remove.pack(side="right", padx=(5, 15), pady=12)

            btn_save = ctk.CTkButton(item_frame, text="💾 Save", width=60, fg_color="#10b981", hover_color="#059669", font=ctk.CTkFont(weight="bold"), command=lambda f_id=file_id: self.download_file_locally(f_id))
            btn_save.pack(side="right", padx=5, pady=12)

            is_locked = bool(file_info.get('pin'))
            lock_text = "🔒" if is_locked else "🔓"
            lock_color = "#f59e0b" if is_locked else "#3b82f6"
            lock_hover = "#d97706" if is_locked else "#2563eb"
            
            btn_lock = ctk.CTkButton(item_frame, text=lock_text, width=35, fg_color=lock_color, hover_color=lock_hover, font=ctk.CTkFont(size=16))
            btn_lock.configure(command=lambda f_id=file_id, btn=btn_lock: self.toggle_pin(f_id, btn))
            btn_lock.pack(side="right", padx=5, pady=12)

    # --- Connected Users UI Handling ---
    def refresh_users_ui(self):
        user_count = len(SERVER_STATE['users'])
        self.lbl_users.configure(text=f"📱 Network Devices ({user_count})")

        for ip in list(self.user_widgets.keys()):
            if ip not in SERVER_STATE['users']:
                self.user_widgets[ip]['box'].destroy()
                del self.user_widgets[ip]

        for ip, data in SERVER_STATE['users'].items():
            if ip not in self.user_widgets: self.create_user_box(ip, data)
            else: self.update_user_box(ip, data)

        self.refresh_chat_user_list()

    def kick_user(self, ip):
        """Clean removal of user. No permanent ban, just forces disconnect."""
        if ip not in SERVER_STATE['users']: return
        
        user_name = SERVER_STATE['users'][ip]['name']
        confirm = messagebox.askyesno("Confirm Disconnect", f"Disconnect '{user_name}' ({ip})? They will have to re-enter their name if they refresh the page.", parent=self)
        
        if confirm:
            SERVER_STATE['pending_kicks'].add(ip)
            del SERVER_STATE['users'][ip]
            self.append_log(f"🚪 Disconnected User: {user_name} ({ip})")
            self.refresh_users_ui()
            gui_command_queue.put("refresh_chat_ui")
                
    def create_user_box(self, ip, data):
        box = ctk.CTkFrame(self.users_frame, fg_color="#27272a", corner_radius=10)
        box.pack(fill="x", padx=5, pady=5)
        
        info_frame = ctk.CTkFrame(box, fg_color="transparent")
        info_frame.pack(side="left", padx=15, pady=8, fill="x", expand=True)
        
        lbl_name = ctk.CTkLabel(info_frame, text=data['name'], font=ctk.CTkFont(weight="bold", size=14), anchor="w")
        lbl_name.pack(fill="x")
        
        status = "🟢 Active" if (time.time() - data['last_seen'] < 60) else "🟡 Idle"
        lbl_info = ctk.CTkLabel(info_frame, text=f"{ip} | {data['os']} | {status}", font=ctk.CTkFont(size=11), text_color="#a1a1aa", anchor="w")
        lbl_info.pack(fill="x")
        
        right_panel = ctk.CTkFrame(box, fg_color="transparent")
        right_panel.pack(side="right", padx=10, pady=5)
        
        switch_var = tk.BooleanVar(value=data['can_upload'])
        switch = ctk.CTkSwitch(right_panel, text="Uploads", variable=switch_var, command=lambda: self.toggle_upload_permission(ip, switch_var), progress_color="#6366f1", width=60)
        switch.pack(side="left", padx=5)

        btn_remove = ctk.CTkButton(right_panel, text="Remove", width=60, height=28, font=ctk.CTkFont(size=11, weight="bold"), fg_color="#ef4444", hover_color="#dc2626", command=lambda i=ip: self.kick_user(i))
        btn_remove.pack(side="left", padx=5)

        self.user_widgets[ip] = {
            'box': box, 'lbl_name': lbl_name, 'lbl_info': lbl_info, 'switch_var': switch_var
        }

    def update_user_box(self, ip, data):
        w = self.user_widgets[ip]
        status = "🟢 Active" if (time.time() - data['last_seen'] < 60) else "🟡 Idle"
        w['lbl_info'].configure(text=f"{ip} | {data['os']} | {status}")
        
        if time.time() - data['last_seen'] > 60:
            w['lbl_name'].configure(text_color="#a1a1aa")
        else:
            w['lbl_name'].configure(text_color="#fafafa")
            
        w['lbl_name'].configure(text=data['name'])
        if w['switch_var'].get() != data['can_upload']: w['switch_var'].set(data['can_upload'])

    def toggle_upload_permission(self, ip, var):
        state = var.get()
        SERVER_STATE['users'][ip]['can_upload'] = state
        action = "Allowed" if state else "Denied"
        self.append_log(f"🛡️ {action} upload permission for {SERVER_STATE['users'][ip]['name']}")

    # --- HOST CHAT UI ---
    def refresh_chat_user_list(self):
        for widget in self.chat_users_container.winfo_children(): widget.destroy()

        for ip, data in SERVER_STATE['users'].items():
            btn_color = "#3f3f46" if self.chat_target_ip == ip else "transparent"
            btn = ctk.CTkButton(self.chat_users_container, text=f"👤 {data['name']}", fg_color=btn_color, hover_color="#52525b", height=40, anchor="w", command=lambda i=ip: self.switch_chat_target(i))
            btn.pack(fill="x", padx=10, pady=2)
            
    def switch_chat_target(self, ip):
        self.chat_target_ip = ip
        self.btn_chat_group.configure(fg_color="#4f46e5" if ip is None else "transparent")
        self.refresh_chat_user_list() 
        
        target_name = "🌐 Global Group Chat" if ip is None else f"🔒 Private: {SERVER_STATE['users'].get(ip, {}).get('name', ip)}"
        self.lbl_current_chat.configure(text=target_name)
        self.render_chat_messages()

    def show_msg_context_menu(self, event, msg_id, is_mine):
        menu = tk.Menu(self, tearoff=0, font=("Inter", 10))
        menu.add_command(label="🗑️ Delete for me", command=lambda: self.delete_msg_host(msg_id, "me"))
        menu.add_command(label="🚮 Delete for everyone", command=lambda: self.delete_msg_host(msg_id, "everyone"))
        menu.tk_popup(event.x_root, event.y_root)

    def delete_msg_host(self, msg_id, del_type):
        if del_type == "everyone":
            DELETED_EVERYONE.add(msg_id)
            for m in CHAT_MESSAGES:
                if m['id'] == msg_id:
                    m['content'] = '🚫 This message was deleted.'
                    m['type'] = 'text'
                    m['url'] = None
                    m['filename'] = None
        elif del_type == "me":
            if "Host" not in DELETED_FOR_ME:
                DELETED_FOR_ME["Host"] = set()
            DELETED_FOR_ME["Host"].add(msg_id)
        
        self.render_chat_messages()
        gui_command_queue.put("refresh_chat_ui")

    def render_chat_messages(self):
        for widget in self.chat_messages_frame.winfo_children(): widget.destroy()

        hidden_ids = DELETED_FOR_ME.get("Host", set())
        relevant = []
        for m in CHAT_MESSAGES:
            if m['id'] in hidden_ids: continue
            
            if self.chat_target_ip is None:
                if m['to'] is None: relevant.append(m)
            else:
                if (m['to'] == self.chat_target_ip and m['from'] == 'Host') or (m['from'] == self.chat_target_ip and m['to'] == 'Host'):
                    relevant.append(m)

        for m in relevant:
            is_mine = (m['from'] == 'Host')
            align = "e" if is_mine else "w"
            color = "#4f46e5" if is_mine else "#334155"
            sender = "👑 You" if is_mine else m['from_name']

            bubble = ctk.CTkFrame(self.chat_messages_frame, fg_color=color, corner_radius=10)
            bubble.pack(anchor=align, padx=10, pady=5)

            if not is_mine and self.chat_target_ip is None:
                ctk.CTkLabel(bubble, text=sender, font=ctk.CTkFont(size=10, weight="bold"), text_color="#a1a1aa").pack(anchor="w", padx=10, pady=(5,0))

            if m['type'] == 'text':
                ctk.CTkLabel(bubble, text=m['content'], wraplength=400, justify="left").pack(padx=10, pady=10)
            elif m['type'] == 'lan_file':
                file_ui = ctk.CTkFrame(bubble, fg_color="#064e3b", corner_radius=8, border_width=1, border_color="#10b981")
                file_ui.pack(padx=10, pady=10, fill="x")
                ctk.CTkLabel(file_ui, text="📁", font=ctk.CTkFont(size=25)).pack(side="left", padx=(10,5))
                info_frame = ctk.CTkFrame(file_ui, fg_color="transparent")
                info_frame.pack(side="left", fill="x", expand=True, padx=5, pady=5)
                ctk.CTkLabel(info_frame, text=m['filename'], font=ctk.CTkFont(weight="bold")).pack(anchor="w")
                ctk.CTkLabel(info_frame, text="LAN Shared File", font=ctk.CTkFont(size=10), text_color="#10b981").pack(anchor="w")
                btn_file = ctk.CTkButton(file_ui, text="Get", width=50, fg_color="#10b981", hover_color="#059669", command=lambda url=m['url']: webbrowser.open(f"http://{self.get_local_ip()}:{self.port_var.get()}{url}"))
                btn_file.pack(side="right", padx=10)
            else:
                icon = "🖼️ Image" if m['type']=='image' else "🎬 Video" if m['type']=='video' else "📄 File"
                btn_file = ctk.CTkButton(bubble, text=f"{icon}: {m['filename']}", fg_color="transparent", border_width=1, border_color="#cbd5e1", command=lambda f=m['filename']: self.open_chat_file(f))
                btn_file.pack(padx=10, pady=10)

            # Bind Context Menu for Host Deletions
            bubble.bind("<Button-3>", lambda e, mid=m['id'], mine=is_mine: self.show_msg_context_menu(e, mid, mine))
            for child in bubble.winfo_children():
                child.bind("<Button-3>", lambda e, mid=m['id'], mine=is_mine: self.show_msg_context_menu(e, mid, mine))
                for subchild in child.winfo_children():
                    subchild.bind("<Button-3>", lambda e, mid=m['id'], mine=is_mine: self.show_msg_context_menu(e, mid, mine))
                
    def host_chat_send(self):
        text = self.chat_input_var.get().strip()
        if not text: return
        global chat_msg_id_counter
        
        msg = {
            'id': chat_msg_id_counter, 'from': 'Host', 'from_name': '👑 ' + SERVER_STATE['host_name'],
            'to': self.chat_target_ip, 'type': 'text', 'content': text,
            'url': None, 'filename': None, 'time': time.time()
        }
        CHAT_MESSAGES.append(msg)
        chat_msg_id_counter += 1
        self.chat_input_var.set("")
        self.render_chat_messages()

    def host_chat_attach(self):
        filepaths = filedialog.askopenfilenames(title="Select file(s) to share")
        if not filepaths: return
        
        choice_win = ctk.CTkToplevel(self)
        choice_win.title("Share Method")
        choice_win.geometry("380x280")
        choice_win.grab_set()
        choice_win.resizable(False, False)
        
        choice_win.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - 190
        y = self.winfo_y() + (self.winfo_height() // 2) - 140
        choice_win.geometry(f"+{x}+{y}")
        
        ctk.CTkLabel(choice_win, text="📎 Share Files", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(25, 5))
        ctk.CTkLabel(choice_win, text=f"{len(filepaths)} file(s) selected", text_color="#a1a1aa").pack(pady=(0, 20))
        
        def do_chat():
            choice_win.destroy()
            self._send_files_to_chat(filepaths)
        
        def do_lan():
            choice_win.destroy()
            self._send_files_to_lan(filepaths)
        
        ctk.CTkButton(choice_win, text="💬 Send in Chat", fg_color="#6366f1", hover_color="#4f46e5", height=45, font=ctk.CTkFont(weight="bold", size=15), command=do_chat).pack(fill="x", padx=30, pady=5)
        ctk.CTkButton(choice_win, text="📁 Upload to LAN Shared Files", fg_color="#10b981", hover_color="#059669", height=45, font=ctk.CTkFont(weight="bold", size=15), command=do_lan).pack(fill="x", padx=30, pady=5)
        ctk.CTkButton(choice_win, text="Cancel", fg_color="#3f3f46", hover_color="#52525b", height=38, command=choice_win.destroy).pack(fill="x", padx=30, pady=(5, 20))

    def _send_files_to_chat(self, filepaths):
        global chat_msg_id_counter
        for filepath in filepaths:
            filename = os.path.basename(filepath)
            safe_name = f"{uuid.uuid4().hex[:6]}_{filename}"
            dest = os.path.join(CHAT_DIR, safe_name)
            shutil.copy2(filepath, dest)

            mime_type, _ = mimetypes.guess_type(filename)
            msg_type = 'file'
            if mime_type:
                if mime_type.startswith('image/'): msg_type = 'image'
                elif mime_type.startswith('video/'): msg_type = 'video'

            msg = {
                'id': chat_msg_id_counter, 'from': 'Host', 'from_name': '👑 ' + SERVER_STATE['host_name'],
                'to': self.chat_target_ip, 'type': msg_type, 'content': None,
                'url': f"/chat_media/{safe_name}", 'filename': filename, 'time': time.time()
            }
            CHAT_MESSAGES.append(msg)
            chat_msg_id_counter += 1
            
        self.render_chat_messages()

    def _send_files_to_lan(self, filepaths):
        global chat_msg_id_counter
        for filepath in filepaths:
            file_id = str(uuid.uuid4())
            filename = os.path.basename(filepath)
            
            # Save to standard LAN share
            dest = os.path.join(UPLOAD_DIR, filename)
            if os.path.exists(dest):
                name, ext = os.path.splitext(filename)
                filename = f"{name}_{str(uuid.uuid4())[:6]}{ext}"
                dest = os.path.join(UPLOAD_DIR, filename)
            shutil.copy2(filepath, dest)
            
            shared_files[file_id] = {
                'name': filename,
                'path': dest,
                'pin': None,
                'size_formatted': format_size(get_actual_size(dest)),
                'uploader': "👑 " + SERVER_STATE['host_name'],
                'is_folder': False
            }
            
            # Rich Message Injection inside Chat
            msg = {
                'id': chat_msg_id_counter, 'from': 'Host', 'from_name': '👑 ' + SERVER_STATE['host_name'],
                'to': self.chat_target_ip, 'type': 'lan_file',
                'content': None,
                'url': f"/download/{file_id}", 'filename': filename, 'time': time.time()
            }
            CHAT_MESSAGES.append(msg)
            chat_msg_id_counter += 1
            
        self.refresh_file_list()
        self.render_chat_messages()

    def open_chat_file(self, filename):
        for f in os.listdir(CHAT_DIR):
            if f.endswith(filename):
                try:
                    p = os.path.join(CHAT_DIR, f)
                    if platform.system() == "Windows": os.startfile(p)
                    elif platform.system() == "Darwin": subprocess.Popen(["open", p])
                    else: subprocess.Popen(["xdg-open", p])
                except Exception as e: print(e)
                return

    # -----------------------------------------

    def generate_qr(self, url):
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(190, 190))
        self.qr_label.configure(image=ctk_img, text="\nScan QR Code", compound="top", font=ctk.CTkFont(size=12, slant="italic"))
        self.qr_label.image = ctk_img

    def show_large_qr(self):
        if not self.is_running or not self.direct_access_url: return
        top = ctk.CTkToplevel(self)
        top.title("Scan QR Code to Join")
        top.geometry("450x450")
        top.grab_set()

        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4)
        qr.add_data(self.direct_access_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(400, 400))
        lbl = ctk.CTkLabel(top, image=ctk_img, text="")
        lbl.pack(expand=True, fill="both", padx=20, pady=20)

    def copy_link(self):
        if self.is_running and self.direct_access_url:
            self.clipboard_clear()
            self.clipboard_append(self.direct_access_url)
            self.btn_copy_link.configure(text="✅ Copied!")
            self.after(2000, lambda: self.btn_copy_link.configure(text="📋 Link") if self.is_running else None)

    def append_log(self, message):
        self.txt_logs.configure(state="normal")
        self.txt_logs.insert("end", message + "\n")
        self.txt_logs.see("end")
        self.txt_logs.configure(state="disabled")

    def process_logs(self):
        while not gui_command_queue.empty():
            cmd = gui_command_queue.get()
            if cmd == "refresh_files": self.refresh_file_list()
            elif cmd == "refresh_users": self.refresh_users_ui()
            elif cmd == "refresh_chat_ui": 
                if self.tabview.get() == "💬 Live Chat Hub":
                    self.render_chat_messages()

        while not system_logs.empty():
            msg = system_logs.get()
            self.append_log(msg)
            
        if self.is_running:
            self.refresh_users_ui()

        self.after(500, self.process_logs)

    def toggle_server(self):
        if not self.is_running:
            try: port = int(self.port_var.get())
            except ValueError:
                messagebox.showwarning("Invalid Port", "Port must be a valid number.")
                return

            if self.secure_mode_var.get():
                server_pin = self.server_pin_var.get().strip()
                if not server_pin.isdigit() or len(server_pin) != 4:
                    messagebox.showwarning("Invalid PIN", "For a secure server, the Global PIN must be exactly 4 numeric digits.")
                    return
                SERVER_STATE['is_secure'] = True
                SERVER_STATE['pin'] = server_pin
            else: SERVER_STATE['is_secure'] = False

            try:
                ip_addr = self.get_local_ip()
                url = f"http://{ip_addr}:{port}"

                SERVER_STATE['host_name'] = self.host_name_var.get().strip() or "Admin"
                SERVER_STATE['users'].clear()
                SERVER_STATE['pending_kicks'].clear()
                CHAT_MESSAGES.clear()
                DELETED_EVERYONE.clear()
                DELETED_FOR_ME.clear()
                
                for w in self.user_widgets.values(): w['box'].destroy()
                self.user_widgets.clear()
                self.refresh_chat_user_list()
                self.render_chat_messages()
                
                if SERVER_STATE['is_secure']: self.direct_access_url = f"{url}/login?pin={SERVER_STATE['pin']}"
                else: self.direct_access_url = url

                self.server_thread = ServerThread(app, '0.0.0.0', port)
                self.server_thread.start()

                self.is_running = True
                self.btn_start_stop.configure(text="🛑 Stop Server", fg_color="#ef4444", hover_color="#dc2626")
                self.entry_port.configure(state="disabled")
                self.switch_secure.configure(state="disabled")
                self.entry_server_pin.configure(state="disabled")
                self.btn_copy_link.configure(state="normal")
                self.btn_open_web.configure(state="normal")
                
                # Auto-enable Live Chat when server starts
                SERVER_STATE['chat_enabled'] = True
                self.btn_toggle_chat.configure(text="🛑 Stop Live Chat", fg_color="#ef4444", hover_color="#dc2626")
                
                if SERVER_STATE['is_secure']: self.lbl_url.configure(text=f"🔒 SECURE ACTIVE\n{url}", text_color="#10b981")
                else: self.lbl_url.configure(text=f"🌐 OPEN ACTIVE\n{url}", text_color="#10b981")
                    
                self.generate_qr(self.direct_access_url)

                self.append_log(f"\n--- 🚀 Premium Server Started on Port {port} ---")
                mode_str = "Secure (PIN Required)" if SERVER_STATE['is_secure'] else "Open (No Global PIN)"
                self.append_log(f"Mode: {mode_str}")
                self.append_log("💬 Live Chat auto-enabled.")
                self.append_log("Waiting for network devices to connect...")

            except Exception as e:
                messagebox.showerror("Server Error", f"Could not start server. Port might be in use.\n{e}")
        else:
            if self.server_thread:
                self.server_thread.shutdown()
                self.server_thread.join()
            
            self.is_running = False
            self.btn_start_stop.configure(text="🚀 Start Server", fg_color="#10b981", hover_color="#059669")
            self.entry_port.configure(state="normal")
            self.switch_secure.configure(state="normal")
            if self.secure_mode_var.get(): self.entry_server_pin.configure(state="normal")
                
            self.btn_copy_link.configure(state="disabled", text="📋 Link")
            self.btn_open_web.configure(state="disabled")
            self.direct_access_url = ""
            
            self.lbl_url.configure(text="Status: Offline", text_color="#a1a1aa")
            self.qr_label.configure(image="", text="")
            
            for w in self.user_widgets.values(): w['box'].destroy()
            self.user_widgets.clear()
            self.refresh_chat_user_list()
            
            self.append_log("\n--- 🛑 Server Stopped ---")

    def on_closing(self):
        if self.is_running:
            self.btn_start_stop.configure(text="Closing Server...", state="disabled")
            self.update() 
            if self.server_thread:
                self.server_thread.shutdown()
                self.server_thread.join()
        self.destroy()

if __name__ == "__main__":
    app_window = LANShareApp()
    app_window.protocol("WM_DELETE_WINDOW", app_window.on_closing)
    app_window.mainloop()