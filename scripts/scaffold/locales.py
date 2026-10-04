#!/usr/bin/env python3
"""scaffold/locale.py de  — создаёт aura/i18n/locales/de.yaml с переводом из en через ollama."""
import argparse, sys, json, urllib.request
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("lang", help="de, fr, ja, ...")
a = ap.parse_args()

root = Path(__file__).resolve().parents[2]
locales = root / "aura/i18n/locales"
en = locales / "en.yaml"
target = locales / f"{a.lang}.yaml"

if target.exists():
    print(f"[skip] {target.name} уже есть"); sys.exit(0)
if not en.exists():
    print(f"[fail] нет {en}"); sys.exit(1)

import yaml
src = yaml.safe_load(en.read_text(encoding="utf-8"))

lang_name = {"de":"German","fr":"French","ja":"Japanese","ko":"Korean",
             "pt":"Portuguese","it":"Italian","ar":"Arabic","tr":"Turkish"}.get(a.lang, a.lang)

prompt = (f"Translate these YAML values to {lang_name}. Keep keys as-is. "
          f"Return ONLY valid YAML, no commentary:\n\n"
          + yaml.safe_dump(src, allow_unicode=True))

try:
    data = json.dumps({
        "model": "qwen2.5:7b-instruct-q4_K_M",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 800},
    }).encode("utf-8")
    req = urllib.request.Request("http://localhost:11434/api/chat", data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    text = result.get("message", {}).get("content", "")
    # чистим markdown fences
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("yaml"): text = text[4:]
    translated = yaml.safe_load(text.strip())
    target.write_text(yaml.safe_dump(translated, allow_unicode=True, sort_keys=False),
                      encoding="utf-8")
    print(f"[ok] {target.relative_to(root)}")
except Exception as e:
    # fallback — копируем en, помечаем TODO
    target.write_text("# TODO: translate from en\n" + en.read_text(encoding="utf-8"),
                      encoding="utf-8")
    print(f"[warn] LLM недоступен: {e}. Скопирован en с TODO")
