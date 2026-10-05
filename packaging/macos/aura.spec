# -*- mode: python ; coding: utf-8 -*-
"""Aura macOS — PyInstaller spec → .app bundle.
Наука: PyInstaller BUNDLE (macOS), NSSpeechSynthesizer, Homebrew.
"""
import sys
from pathlib import Path

ROOT = Path(SPECPATH).parent.parent

HIDDEN_IMPORTS = [
    "aura.agents.telegram", "aura.agents.whatsapp", "aura.agents.vk_web",
    "aura.agents.email_agent", "aura.agents.sms_bridge",
    "aura.agents.blind", "aura.agents.blind_reply",
    "aura.agents.proactive_alert", "aura.agents.emotion_voice",
    "aura.agents.soul_talk", "aura.agents.reminiscence",
    "aura.agents.health_twin", "aura.agents.federated_adapter",
    "aura.agents.routine_learner", "aura.agents.onboarding",
    "aura.agents.predictor", "aura.agents.adaptive_reminders",
    "aura.agents.unified_router",
    "aura.platform_adapters.macos",
    "aura.platform_adapters.factory",
]

a = Analysis(
    [str(ROOT / "aura_main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / "aura" / "config"), "aura/config"),
        (str(ROOT / "aura" / "i18n"), "aura/i18n"),
        (str(ROOT / "docs"), "docs"),
    ],
    hiddenimports=HIDDEN_IMPORTS,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "numpy.tests"],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="aura",
    debug=False,
    strip=False,
    upx=False,               # UPX плохо работает на macOS
    console=False,
    # target_arch не задаём: CI даёт x86_64 или arm64.
    # Для universal2 нужен universal Python — отдельная сборка (v8.2).
)

coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, name="aura")

app = BUNDLE(
    coll,
    name="Aura.app",
    icon=None,
    bundle_identifier="com.pythonvenom.aura",
    info_plist={
        "CFBundleName": "Aura",
        "CFBundleDisplayName": "Aura",
        "CFBundleVersion": "0.8.0",
        "CFBundleShortVersionString": "0.8.0",
        "NSMicrophoneUsageDescription":
            "Aura использует микрофон для голосового управления.",
        "NSSpeechRecognitionUsageDescription":
            "Aura использует распознавание речи на устройстве.",
        "LSUIElement": False,
        "LSMinimumSystemVersion": "11.0",
    },
)
