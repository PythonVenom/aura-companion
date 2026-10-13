"""aura doctor — health check всех агентов."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / "aura_project"))

from aura.kernel.bootstrap import AuraKernel


async def main():
    kernel = AuraKernel()
    await kernel.start()
    await asyncio.sleep(3)

    print("=" * 50)
    print("  AURA DOCTOR")
    print("=" * 50)
    print()
    print(f"Органов: {len(kernel.registry.all())}")
    for name, status in kernel.registry.all().items():
        icon = "✅" if status == "running" else "❌"
        print(f"  {icon} {name:20} {status}")

    print()
    print(f"Правил router: {len(kernel.router._rules)}")

    await kernel.stop()
    print()
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
