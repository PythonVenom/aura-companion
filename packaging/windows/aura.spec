# -*- mode: python ; coding: utf-8 -*-
"""Aura Windows — PyInstaller spec.
Наука: PyInstaller spec, MSI/WiX (Microsoft), Python runtime bundling.
"""
import sys
from pathlib import Path

block_cipher = None

ROOT = Path(SPECPATH).parent.parent
HIDDEN_IMPORTS = [
    # Aura агенты — PyInstaller не видит динамические импорты
    "aura.agents.telegram",
    "aura.agents.whatsapp",
    "aura.agents.vk_web",
    "aura.agents.email_agent",
    "aura.agents.sms_bridge",
    "aura.agents.blind",
    "aura.agents.blind_reply",
    "aura.agents.proactive_alert",
    "aura.agents.emotion_voice",
    "aura.agents.soul_talk",
    "aura.agents.reminiscence",
    "aura.agents.health_twin",
    "aura.agents.federated_adapter",
    "aura.agents.routine_learner",
    "aura.agents.onboarding",
    "aura.agents.predictor",
    "aura.agents.adaptive_reminders",
    "aura.agents.unified_router",
    "aura.platform_adapters.linux",
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
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="aura",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,      # GUI mode
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / "packaging" / "windows" / "aura.ico") if (ROOT / "packaging" / "windows" / "aura.ico").exists() else None,
)

coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False, upx=True, upx_exclude=[],
    name="aura",
)
