"""#66 Скриншоты TUI для README (Textual save_screenshot)."""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Страховка от загрязнённого PYTHONPATH (AppDir из тестов)
os.environ.pop("PYTHONPATH", None)

OUT = Path(__file__).parent.parent / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)


async def _capture(app, name: str) -> bool:
    try:
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            svg_path = OUT / f"{name}.svg"
            app.save_screenshot(filename=str(svg_path))
            print(f"✅ {name}: {svg_path.name}")
            return True
    except Exception as e:
        print(f"❌ {name}: {e}")
        return False


async def main() -> int:
    ok = total = 0

    try:
        from aura.cockpit.studio import AuraStudio
        total += 1
        if await _capture(AuraStudio(), "studio"):
            ok += 1
    except Exception as e:
        print(f"⚠️  studio: {e}")

    try:
        from aura.cockpit.configurator import ConfiguratorApp
        total += 1
        if await _capture(ConfiguratorApp(), "configurator"):
            ok += 1
    except Exception as e:
        print(f"⚠️  configurator: {e}")

    print(f"\n📊 {ok}/{total} в {OUT}")
    return 0 if ok > 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
