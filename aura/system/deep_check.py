"""Deep Check — полная самопроверка всех систем Aura.

Проверяет 14 категорий: ядро, голос, микрофон, LLM, память,
bridge, железо, DE, агенты, документы, тесты, ruff, git, демон.

Наука: Saltzer & Schroeder 1975 (audit trail),
       Nielsen 1993 (visibility of system status).
"""

from __future__ import annotations

import contextlib
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path.home() / "aura-companion"
VENV_PY = str(REPO / "venv" / "bin" / "python3")


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str = ""
    fix: str = ""


@dataclass
class DeepReport:
    results: list[CheckResult] = field(default_factory=list)

    def add(self, r: CheckResult) -> None:
        self.results.append(r)

    @property
    def ok_count(self) -> int:
        return sum(1 for r in self.results if r.ok)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def all_ok(self) -> bool:
        return all(r.ok for r in self.results)

    def failures(self) -> list[CheckResult]:
        return [r for r in self.results if not r.ok]


# ── Проверки ──────────────────────────────────────────

def check_python() -> CheckResult:
    if not Path(VENV_PY).exists():
        return CheckResult("Python venv", False, "нет venv/bin/python3",
                           "python3 -m venv venv")
    try:
        r = subprocess.run([VENV_PY, "--version"],
                           capture_output=True, text=True, timeout=3)
        ver = r.stdout.strip() or r.stderr.strip()
        return CheckResult("Python venv", True, ver)
    except Exception as e:
        return CheckResult("Python venv", False, str(e))


def check_voice() -> CheckResult:
    voice = REPO / "voices" / "ru_RU-irina-medium.onnx"
    if not voice.exists():
        return CheckResult("Голос (voice.onnx)", False, "нет файла голоса",
                           "скачать ru_RU-irina-medium.onnx")
    if not shutil.which("piper") and not (REPO / "venv/bin/piper").exists():
        return CheckResult("Голос (piper)", False, "piper не в PATH")
    return CheckResult("Голос (Piper + Ирина)", True, str(voice.name))


def check_microphone() -> CheckResult:
    if shutil.which("arecord"):
        with contextlib.suppress(Exception):
            r = subprocess.run(["arecord", "-l"],
                               capture_output=True, text=True, timeout=3)
            if "card" in r.stdout:
                return CheckResult("Микрофон", True, "обнаружен")
    return CheckResult("Микрофон", False, "arecord не нашёл карту")


def check_llm() -> CheckResult:
    if not shutil.which("ollama"):
        return CheckResult("LLM (ollama)", False, "ollama не установлен")
    with contextlib.suppress(Exception):
        r = subprocess.run(["ollama", "list"],
                           capture_output=True, text=True, timeout=5)
        if "qwen" in r.stdout.lower() or "llama" in r.stdout.lower():
            return CheckResult("LLM (ollama)", True, "модели есть")
    return CheckResult("LLM (ollama)", False, "нет моделей",
                       "ollama pull qwen2.5:7b-instruct-q4_K_M")


def check_memory() -> CheckResult:
    db = Path.home() / ".config" / "aura" / "state.db"
    key = Path.home() / ".config" / "aura" / "db.key"
    if not db.exists():
        return CheckResult("Память (SQLCipher)", False, "нет state.db")
    if not key.exists():
        return CheckResult("Память (ключ)", False, "нет db.key")
    return CheckResult("Память (SQLCipher)", True, "state.db + db.key")


def check_bridge() -> CheckResult:
    sock = Path("/tmp/aura_firefox.sock")
    host = shutil.which("pgrep")
    if not sock.exists():
        return CheckResult("Bridge (socket)", False, "нет /tmp/aura_firefox.sock",
                           "загрузить расширение в Firefox")
    # Проверим, есть ли процесс
    if host:
        with contextlib.suppress(Exception):
            r = subprocess.run(["pgrep", "-f", "aura_bridge_host"],
                               capture_output=True, text=True, timeout=3)
            if r.stdout.strip():
                return CheckResult("Bridge (host + socket)", True, "живой")
    return CheckResult("Bridge", False, "сокет есть, host нет")


def check_brightness() -> CheckResult:
    if not shutil.which("brightnessctl"):
        return CheckResult("Яркость (brightnessctl)", False, "не установлен",
                           "pacman -S brightnessctl")
    return CheckResult("Яркость (brightnessctl)", True)


def check_volume() -> CheckResult:
    if shutil.which("wpctl") or shutil.which("pactl"):
        return CheckResult("Звук (wpctl/pactl)", True)
    return CheckResult("Звук", False, "нет wpctl/pactl")


def check_desktop() -> CheckResult:
    if shutil.which("qdbus6") or shutil.which("qdbus"):
        return CheckResult("Рабочие столы (qdbus)", True)
    if shutil.which("wmctrl"):
        return CheckResult("Рабочие столы (wmctrl)", True)
    return CheckResult("Рабочие столы", False, "нет qdbus6 / wmctrl",
                       "pacman -S wmctrl")


def check_agents() -> CheckResult:
    agents_dir = REPO / "aura" / "agents"
    if not agents_dir.exists():
        return CheckResult("Агенты", False, "нет aura/agents/")
    n = sum(1 for f in agents_dir.glob("*.py") if f.name != "__init__.py")
    if n < 50:
        return CheckResult("Агенты", False, f"только {n} файлов")
    return CheckResult("Агенты", True, f"{n} модулей")


def check_docs() -> CheckResult:
    docs = REPO / "docs"
    must = ["MANIFESTO.md", "SCIENCE.md"]
    missing = [m for m in must if not (docs / m).exists()]
    if missing:
        return CheckResult("Документация", False, f"нет: {missing}")
    return CheckResult("Документация", True, f"{len(list(docs.glob('*.md')))} файлов")


def check_ruff() -> CheckResult:
    with contextlib.suppress(Exception):
        r = subprocess.run(
            [VENV_PY, "-m", "ruff", "check", "aura/"],
            cwd=str(REPO), capture_output=True, text=True, timeout=30,
        )
        if r.returncode == 0:
            return CheckResult("Ruff", True, "0 ошибок")
        return CheckResult("Ruff", False, "есть ошибки",
                           "ruff check --fix aura/")
    return CheckResult("Ruff", False, "не смогла запустить")


def check_git() -> CheckResult:
    with contextlib.suppress(Exception):
        r = subprocess.run(["git", "status", "--short"],
                           cwd=str(REPO), capture_output=True,
                           text=True, timeout=5)
        if not r.stdout.strip():
            return CheckResult("Git", True, "рабочий каталог чист")
        n = len(r.stdout.strip().splitlines())
        return CheckResult("Git", True, f"{n} изменений (не закоммичены)")
    return CheckResult("Git", False, "git не отвечает")


def check_daemon() -> CheckResult:
    with contextlib.suppress(Exception):
        r = subprocess.run(
            ["systemctl", "--user", "is-active", "aura.service"],
            capture_output=True, text=True, timeout=5,
        )
        status = r.stdout.strip()
        if status == "active":
            return CheckResult("Демон (systemd)", True, "active")
        return CheckResult("Демон (systemd)", False, status,
                           "systemctl --user start aura.service")
    return CheckResult("Демон", False, "systemctl не отвечает")


def check_story() -> CheckResult:
    story = Path.home() / "aura_private" / "STORY.md"
    if not story.exists():
        return CheckResult("Журнал (STORY.md)", False, "нет файла")
    size = story.stat().st_size
    return CheckResult("Журнал (STORY.md)", True, f"{size} байт")


# ── Главная функция ───────────────────────────────────

ALL_CHECKS = [
    ("python", check_python),
    ("voice", check_voice),
    ("microphone", check_microphone),
    ("llm", check_llm),
    ("memory", check_memory),
    ("bridge", check_bridge),
    ("brightness", check_brightness),
    ("volume", check_volume),
    ("desktop", check_desktop),
    ("agents", check_agents),
    ("docs", check_docs),
    ("ruff", check_ruff),
    ("git", check_git),
    ("daemon", check_daemon),
    ("story", check_story),
]


def run_deep_check() -> DeepReport:
    """Прогнать все проверки. Возвращает отчёт."""
    report = DeepReport()
    for _name, fn in ALL_CHECKS:
        try:
            report.add(fn())
        except Exception as e:
            report.add(CheckResult(_name, False, f"исключение: {e}"))
    return report


def render_report(verbose: bool = False) -> str:
    """Текстовый отчёт."""
    report = run_deep_check()
    lines = []
    lines.append("╔══════════════════════════════════════════════════════════════╗")
    lines.append("║  🛸 ГЛУБОКАЯ ПРОВЕРКА СИСТЕМ                                 ║")
    lines.append("╠══════════════════════════════════════════════════════════════╣")
    for r in report.results:
        mark = "🟢" if r.ok else "🔴"
        line = f"║  {mark}  {r.name:<30} {r.detail[:22]:<22} ║"
        lines.append(line)
    lines.append("╠══════════════════════════════════════════════════════════════╣")
    lines.append(f"║  Итог: {report.ok_count}/{report.total} систем в норме"
                 f"{' ' * (44 - len(str(report.ok_count)) - len(str(report.total)))}║")
    lines.append("╚══════════════════════════════════════════════════════════════╝")

    if verbose and report.failures():
        lines.append("")
        lines.append("⚠️  Провалились:")
        for r in report.failures():
            lines.append(f"  • {r.name}: {r.detail}")
            if r.fix:
                lines.append(f"    → {r.fix}")

    return "\n".join(lines)


__all__ = [
    "CheckResult", "DeepReport",
    "render_report", "run_deep_check",
]
