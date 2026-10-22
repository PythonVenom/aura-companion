#!/usr/bin/env python3
"""Idempotent fix for Aura hang: speaker.py + aura_main.py."""
from pathlib import Path

ROOT = Path.home() / "aura_project"
SPEAKER = ROOT / "aura/agents/speaker.py"
MAIN = ROOT / "aura_main.py"
MARK = "# >>> AURA_HANG_FIX_V1"


def patch_speaker():
    src = SPEAKER.read_text(encoding="utf-8")
    if MARK in src:
        print("[skip] speaker.py already patched")
        return False

    old = (
        "                    self.aplay_process = subprocess.Popen(\n"
        "                        ['paplay', wav_file],\n"
        "                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
        "                    self.aplay_process.wait()\n"
        "                    os.unlink(text_file)\n"
        "                    try:\n"
        "                        os.unlink(wav_file)\n"
        "                    except Exception:\n"
        "                        pass\n"
    )
    new = (
        "                    self.aplay_process = subprocess.Popen(\n"
        "                        ['paplay', wav_file],\n"
        "                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
        "                    " + MARK + "\n"
        "                    # Оценка длительности: WAV 22050 Hz mono 16-bit\n"
        "                    try:\n"
        "                        _secs = max(2.0, os.path.getsize(wav_file) / 44100.0)\n"
        "                    except OSError:\n"
        "                        _secs = 10.0\n"
        "                    _timeout = _secs + 5.0\n"
        "                    try:\n"
        "                        self.aplay_process.wait(timeout=_timeout)\n"
        "                    except subprocess.TimeoutExpired:\n"
        "                        print(f'⚠️ paplay висит >{_timeout:.1f}s — kill')\n"
        "                        try:\n"
        "                            self.aplay_process.kill()\n"
        "                            self.aplay_process.wait(timeout=1.0)\n"
        "                        except Exception:\n"
        "                            pass\n"
        "                    finally:\n"
        "                        os.unlink(text_file)\n"
        "                        try:\n"
        "                            os.unlink(wav_file)\n"
        "                        except Exception:\n"
        "                            pass\n"
    )
    if old not in src:
        print("[FAIL] speaker.py: aplay block not found — abort")
        return False
    src = src.replace(old, new, 1)

    old_exc = (
        "            except Exception as e:\n"
        "                print(f\"❌ Ошибка озвучивания: {e}\")\n"
    )
    new_exc = (
        "            except Exception as e:\n"
        "                print(f\"❌ Ошибка озвучивания: {e}\")\n"
        "            finally:\n"
        "                self.is_speaking = False  " + MARK + "\n"
    )
    if old_exc not in src:
        print("[FAIL] speaker.py: except block not found — abort")
        return False
    src = src.replace(old_exc, new_exc, 1)

    SPEAKER.write_text(src, encoding="utf-8")
    print("[ok] speaker.py patched")
    return True


def patch_main():
    src = MAIN.read_text(encoding="utf-8")
    if MARK in src:
        print("[skip] aura_main.py already patched")
        return False

    old = (
        "                # Ждём окончания речи — по is_speaking, не aplay_process\n"
        "                while self.speaker.is_speaking:\n"
        "                    time.sleep(0.05)\n"
    )
    new = (
        "                # Ждём окончания речи — по is_speaking, не aplay_process\n"
        "                " + MARK + "\n"
        "                _speak_deadline = time.monotonic() + 30.0\n"
        "                while self.speaker.is_speaking and time.monotonic() < _speak_deadline:\n"
        "                    time.sleep(0.05)\n"
        "                if self.speaker.is_speaking:\n"
        "                    print('⚠️ speaker.is_speaking не сброшен за 30s — форсирую')\n"
        "                    self.speaker.is_speaking = False\n"
    )
    if old not in src:
        print("[FAIL] aura_main.py: speak-wait block not found — abort")
        return False
    src = src.replace(old, new, 1)

    MAIN.write_text(src, encoding="utf-8")
    print("[ok] aura_main.py patched")
    return True


if __name__ == "__main__":
    a = patch_speaker()
    b = patch_main()
    print("DONE" if (a or b) else "NOCHANGE")
