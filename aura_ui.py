import streamlit as st
import json
import os
import time
import subprocess
import requests

st.set_page_config(page_title="🌟 АУРА", layout="wide")

# ===================================================
# ЗАГРУЗКА ЛОГОВ
# ===================================================
def load_logs():
    log_file = "/home/pythonvenom/aura_project/logs/aura.log"
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            return f.read().split('\n')[-50:]
    return ["Лог не найден"]

def load_memory():
    mem_file = "/home/pythonvenom/aura_project/knowledge/memory.json"
    if os.path.exists(mem_file):
        with open(mem_file, 'r') as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def load_conversations():
    conv_file = "/home/pythonvenom/aura_project/knowledge/conversations.log"
    if os.path.exists(conv_file):
        with open(conv_file, 'r') as f:
            return f.read().split('\n')[-30:]
    return []

# ===================================================
# ИНТЕРФЕЙС
# ===================================================
st.title("🌟 АУРА — Голосовой ИИ-ассистент")
st.caption("Следи за работой АУРЫ в реальном времени")

# Статус
col1, col2, col3 = st.columns(3)
with col1:
    try:
        response = requests.get("http://localhost:11434/api/version", timeout=2)
        st.success("🧠 Мозг: ONLINE")
    except:
        st.error("🧠 Мозг: OFFLINE")

with col2:
    result = subprocess.run(["sudo", "systemctl", "is-active", "aura.service"], capture_output=True, text=True)
    if result.stdout.strip() == "active":
        st.success("🔊 АУРА: ONLINE")
    else:
        st.error("🔊 АУРА: OFFLINE")

with col3:
    st.success("🎤 Слух: АКТИВЕН")

# Управление
st.sidebar.title("📊 Управление АУРОЙ")

col1, col2, col3 = st.sidebar.columns(3)
with col1:
    if st.button("▶️ Запустить"):
        os.system("sudo systemctl start aura.service")
        st.success("Запущено!")
        time.sleep(1)
        st.rerun()

with col2:
    if st.button("⏹️ Остановить"):
        os.system("sudo systemctl stop aura.service")
        st.success("Остановлено!")
        time.sleep(1)
        st.rerun()

with col3:
    if st.button("🔄 Перезапустить"):
        os.system("sudo systemctl restart aura.service")
        st.success("Перезапущено!")
        time.sleep(2)
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.metric("Фактов в памяти", len(load_memory().get("факты", {})))
st.sidebar.metric("Строк лога", len(load_logs()))

# Табы
tab1, tab2, tab3 = st.tabs(["📝 Логи", "🧠 Память", "💬 Диалоги"])

with tab1:
    st.subheader("📝 Последние логи")
    logs = load_logs()
    st.text_area("Логи", "\n".join(logs), height=400)

with tab2:
    st.subheader("🧠 Что помнит АУРА")
    memory = load_memory()
    if memory:
        st.json(memory)
    else:
        st.info("Пока ничего не запомнено")

with tab3:
    st.subheader("💬 Последние диалоги")
    conv = load_conversations()
    if conv:
        st.text_area("Диалоги", "\n".join(conv), height=300)
    else:
        st.info("Диалогов пока нет")

st.sidebar.caption("АУРА v3.0 | Разработано с ❤️")
