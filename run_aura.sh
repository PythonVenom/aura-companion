#!/bin/bash
export DISPLAY=:0
xhost +SI:localuser:pythonvenom
cd ~/aura_project
source venv/bin/activate
python aura_agent_parallel.py
