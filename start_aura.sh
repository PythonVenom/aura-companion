#!/bin/bash
# Запуск Ollama
ollama serve &
sleep 5

# Запуск АУРЫ
cd /home/pythonvenom/aura_project
source /home/pythonvenom/jarvis_py312/bin/activate
python aura.py
