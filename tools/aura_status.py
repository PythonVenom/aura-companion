"""aura status — быстрый статус через CLI."""
import subprocess


def main():
    print("🛸 AURA STATUS")
    print("=" * 40)
    # systemd
    try:
        r = subprocess.run(["systemctl", "--user", "is-active",
                            "aura-kernel.service"],
                           capture_output=True, text=True, timeout=3)
        status = r.stdout.strip()
        icon = "✅" if status == "active" else "❌"
        print(f"  {icon} service: {status}")
    except Exception as e:
        print(f"  ❌ service: {e}")

    # git
    try:
        r = subprocess.run(["git", "-C",
                            str(__import__("pathlib").Path.home()
                                / "aura_project"),
                            "log", "--oneline", "-1"],
                           capture_output=True, text=True, timeout=3)
        print(f"  📝 last commit: {r.stdout.strip()}")
    except Exception as e:
        print(f"  ❌ git: {e}")

    print("=" * 40)


if __name__ == "__main__":
    main()
