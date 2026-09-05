#!/usr/bin/env python3
import subprocess
import sys
import os

def execute_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout + result.stderr
    except Exception as e:
        return f"Ошибка: {e}"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = " ".join(sys.argv[1:])
        print(execute_command(cmd))
    else:
        # Режим ожидания команд из файла
        while True:
            cmd_file = "/tmp/aura_cmd.txt"
            result_file = "/tmp/aura_result.txt"
            if os.path.exists(cmd_file):
                with open(cmd_file, "r") as f:
                    cmd = f.read().strip()
                os.remove(cmd_file)
                if cmd:
                    result = execute_command(cmd)
                    with open(result_file, "w") as f:
                        f.write(result)
