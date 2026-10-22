#!/usr/bin/env python3
"""XFCE genmon plugin для Aura (ADR-081)."""
import json
import urllib.request

API = 'http://127.0.0.1:8765'
ICONS = {
    'idle': '🎙', 'listening': '🔴', 'thinking': '💭',
    'speaking': '🔊', 'paused': '⏸', 'error': '❌',
}

def get_state():
    try:
        with urllib.request.urlopen(API + '/status', timeout=1) as r:
            return json.loads(r.read()).get('state', 'unknown')
    except Exception:
        return 'unknown'

state = get_state()
icon = ICONS.get(state, '?')
print(f'<txt>{icon}</txt>')
print(f'<tool>Aura: {state}</tool>')
print(f'<click>xdg-open {API}/ui</click>')
