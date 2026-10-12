"""Briefing — брифинг-капсула для нового чата.

ОДИН файл = полный контекст проекта для копипаста в новый чат.
Решает главную боль: потеря контекста при смене чата.

Наука:
- Sweller 1988 (Cognitive Load) — один файл вместо 20
- Miller 1956 (7±2) — блочная структура
- Norman 1988 (Recognition) — всё видно
- Nielsen 1993 (Visibility) — статус явный
- Kahneman 2011 (System 1/2) — быстрый вход
- Hutchins 1995 (Distributed Cog) — знание в файле
- Brooks 1975 — не терять контекст
- Licklider 1960 — симбиоз
- Duhigg 2012 — habit loop
"""
from __future__ import annotations

import contextlib
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent

HOME = Path.home()
BRIEF_DIR = HOME / "aura_private" / "briefings"
REPOS = [HOME / "aura-companion", HOME / "aura_project"]


class BriefingAgent(BaseAgent):
    name = "briefing"
    MODULE_ALWAYS = True
    KEYWORDS = ("брифинг", "утренний отчёт", "что вчера делали",
                "обзор дня", "brief", "рапорт", "статус дня",
                "капсула", "контекст в чат")

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)
        path = self.generate()
        return AgentResponse.ok(f"Капсула готова: {path}", self.name)

    # ═══════════════════════════════════════════════════
    def generate(self) -> Path:
        BRIEF_DIR.mkdir(parents=True, exist_ok=True)
        now = datetime.now()
        yesterday = now - timedelta(days=1)

        L: list[str] = []
        L += self._s1_role()
        L += self._s2_rules()
        L += self._s3_what_is_aura()
        L += self._s4_map()
        L += self._s5_github()
        L += self._s6_repo_state()
        L += self._s7_yesterday(yesterday)
        L += self._s8_active()
        L += self._s9_key_docs()
        L += self._s10_directives()
        L += self._s11_adr_index()
        L += self._s12_systems()
        L += self._s13_problems()
        L += self._s14_next_step()
        L += ["", "---", "",
              f"*Капсула сгенерирована: {now:%Y-%m-%d %H:%M}*",
              "*Копируй целиком в новый чат. Больше не теряем контекст.*"]

        path = BRIEF_DIR / f"BRIEF-{now:%Y-%m-%d}.md"
        path.write_text("\n".join(L), encoding="utf-8")

        # ротация: 30 файлов
        briefs = sorted(BRIEF_DIR.glob("BRIEF-*.md"))
        for old in briefs[:-30]:
            with contextlib.suppress(Exception):
                old.unlink()

        return path

    # ═══════════════════════════════════════════════════
    # 1. РОЛЬ И ТОН
    def _s1_role(self) -> list[str]:
        return [
            "# 🛸 КАПСУЛА AURA — ONE-PASTE",
            "",
            f"> Дата: {datetime.now():%Y-%m-%d %H:%M} · Капитан: Иван Воронин",
            "> Скопируй этот файл целиком в новый чат. Всё что нужно — здесь.",
            "",
            "## 1. РОЛЬ И ТОН",
            "",
            "Ты — **Дядя Р2**, помогаешь капитану Ивану (PythonVenom) с проектом Aura.",
            "Стиль: короткий, по делу, игровой, без воды. Можно сарказм.",
            "Аналогии: Mass Effect, Warhammer, Borderlands, Fallout, X3.",
            "",
            "**Правила в чате:**",
            "- Не гнать по кругу. Один шаг → проверка → следующий.",
            "- Сначала диагностика (Д9), потом код.",
            "- Не подставлять / не гадать.",
            "- Не ломать работающее (Д20).",
            "- WIP=1, batch=1 (Д18-Д19).",
            "",
        ]

    # 2. ПРАВИЛА РАБОТЫ
    def _s2_rules(self) -> list[str]:
        return [
            "## 2. ПРАВИЛА РАБОТЫ (кратко)",
            "",
            "Полный список — в блоке 10 (Д1-Д34). Ключевые:",
            "",
            "- **Д9**: не гадать, сначала диагностика",
            "- **Д18**: WIP=1 — одна задача",
            "- **Д19**: batch=1 — патч → тест → коммит",
            "- **Д20**: не ломать работающее",
            "- **Д21**: капитан — первый тестер, без его ок не идёт бате",
            "- **Д31**: всё сказанное капитаном — записывать немедленно",
            "- **Д32**: читать AURA_MASTER.md перед сессией",
            "- **Д33**: если капитан напоминает — это моя вина",
            "",
        ]

    # 3. ЧТО ТАКОЕ AURA
    def _s3_what_is_aura(self) -> list[str]:
        return [
            "## 3. ЧТО ТАКОЕ AURA",
            "",
            "**Aura — не ассистент. Aura — операционная среда присутствия.**",
            "",
            "- Материнское ядро: Arch + Plasma",
            "- Дочери: плазмы затекают в любую ОС",
            "- Убийца клавиатуры и мыши как обязательного посредника",
            "- Voice layer over the OS. Local. Open Source. No cloud.",
            "- Миссия: голосовой слой для тех, кому голос = необходимость",
            "",
            "**Путь:** велосипед → Aura → Auto → Космос.",
            "Начал с ассистента для электровелосипеда. Получил elder-care.",
            "Это не ошибка — это эволюция (Bezos 1997, Taleb 2012, Christensen 1997).",
            "",
            "**Приоритеты:**",
            "1. Elder-care для бати",
            "2. Car-assistant (OBD MVP)",
            "3. Aura OS (Live-USB / ISO / LFS)",
            "4. Hell Mode (игра)",
            "",
        ]

    # 4. КАРТА ПРОЕКТА
    def _s4_map(self) -> list[str]:
        return [
            "## 4. КАРТА ПРОЕКТА",
            "",
            "```",
            "~/aura-companion/        — ядро (78 агентов, RAG 2588, голос)",
            "├── aura/agents/         — 93 файла агентов",
            "├── aura/core/           — orchestrator, registry, protocol",
            "├── aura/voice/          — T-one STT, Piper TTS",
            "├── aura/chat_ui.py      — чат с меню и HUD",
            "├── docs/adr/            — 121+ ADR",
            "├── DIRECTIVES.md        — Д1-Д34",
            "└── run_aura.sh          — запуск",
            "",
            "~/aura_project/          — игра + ISO",
            "├── aura/cockpit/        — секторы, советники, чат-меню",
            "├── aura/game/           — Engine, Combat, Problem, Patterns",
            "├── aura/lore/           — campaign, persona, advisors, codex",
            "├── platforms/out/       — aura-live.iso",
            "└── docs/ROADMAP_NEXT.md — очередь задач",
            "",
            "~/aura_private/          — приватное (не публикуется)",
            "├── docs/AURA_MASTER.md  — ЕДИНЫЙ источник правды",
            "├── docs/vision/         — VISION-2026-09-30 + 6 веток",
            "├── plans/               — TASKS, FROZEN, AUTO_BRAT_PLAN",
            "└── briefings/           — все капсулы",
            "",
            "~/aura_backup/           — VISION-файлы (архив)",
            "~/book/                  — книга «Тело: инструкция»",
            "/mnt/aura_hdd/ollama/    — модели (qwen2.5, llama3.1)",
            "```",
            "",
        ]

    # 5. GITHUB
    def _s5_github(self) -> list[str]:
        return [
            "## 5. GITHUB + КЛЮЧИ",
            "",
            "- **aura-companion**: github.com/PythonVenom/aura-companion (master)",
            "- **aura-project**: github.com/PythonVenom/aura-project (master)",
            "- **aura-control**: github.com/PythonVenom/aura-control",
            "- **SSH**: `~/.ssh/id_ed25519` (MSI Raider Arch)",
            "",
            "**Bundle-бэкапы**: `~/aura_bundles/aura-*.bundle`",
            "",
        ]

    # 6. СОСТОЯНИЕ РЕПО
    def _s6_repo_state(self) -> list[str]:
        L = ["## 6. СОСТОЯНИЕ РЕПОЗИТОРИЕВ", ""]
        for repo in REPOS:
            if not repo.exists():
                continue
            branch = self._git(repo, ["branch", "--show-current"]) or "?"
            last = self._git(repo, ["log", "-1", "--pretty=%h %s"]) or "?"
            status = self._git(repo, ["status", "--short"])
            dirty = len([l for l in status.splitlines() if l.strip()])
            L += [
                f"### {repo.name}",
                f"- Ветка: `{branch}`",
                f"- HEAD: `{last}`",
                f"- Изменённых файлов: {dirty}",
                "",
            ]
        return L

    # 7. ЧТО ДЕЛАЛИ ВЧЕРА
    def _s7_yesterday(self, since_dt: datetime) -> list[str]:
        L = [f"## 7. ЧТО ДЕЛАЛИ (с {since_dt:%Y-%m-%d %H:%M})", ""]
        total = 0
        for repo in REPOS:
            commits = self._git(repo, ["log", f"--since={since_dt:%Y-%m-%d %H:%M}",
                                      "--oneline"])
            if commits:
                lines = commits.splitlines()
                total += len(lines)
                L.append(f"### {repo.name} ({len(lines)})")
                for c in lines[:25]:
                    L.append(f"- {c}")
                L.append("")
        if total == 0:
            L.append("(нет коммитов за период)")
            L.append("")
        return L

    # 8. АКТИВНЫЕ ЗАДАЧИ
    def _s8_active(self) -> list[str]:
        L = ["## 8. АКТИВНЫЕ ЗАДАЧИ", ""]
        sources = [
            HOME / "aura_project/docs/ROADMAP_NEXT.md",
            HOME / "aura_private/plans/TASKS_2026-10-12.md",
        ]
        for p in sources:
            if not p.exists():
                continue
            L.append(f"### {p.name}")
            items = self._open_items(p, limit=15)
            if items:
                L += items
            else:
                L.append("(пусто)")
            L.append("")
        return L

    # 9. КЛЮЧЕВЫЕ ДОКУМЕНТЫ
    def _s9_key_docs(self) -> list[str]:
        return [
            "## 9. КЛЮЧЕВЫЕ ДОКУМЕНТЫ (что читать первым)",
            "",
            "| Что | Где |",
            "|---|---|",
            "| Единый источник правды | `~/aura_private/docs/AURA_MASTER.md` |",
            "| Видение 30.09 | `~/aura_private/docs/vision/VISION-2026-09-30.md` |",
            "| Бизнес-ветки | `VISION-AUTO/FACTORY/MARKETPLACE/REALTY/STEAM.md` |",
            "| Директивы | `~/aura-companion/DIRECTIVES.md` |",
            "| ADR-индекс | `~/aura-companion/docs/adr/README.md` |",
            "| Роадмап | `~/aura_project/docs/ROADMAP_NEXT.md` |",
            "| Заморозка | `~/aura_private/plans/FROZEN.md` |",
            "| Голосовые команды | `~/aura_private/plans/voice_commands.md` |",
            "",
        ]

    # 10. ДИРЕКТИВЫ
    def _s10_directives(self) -> list[str]:
        path = HOME / "aura-companion/DIRECTIVES.md"
        L = ["## 10. ДИРЕКТИВЫ (Д1-Д34)", ""]
        if path.exists():
            L.append("```")
            L += path.read_text(encoding="utf-8").strip().splitlines()
            L.append("```")
        else:
            L.append("(DIRECTIVES.md не найден)")
        L.append("")
        return L

    # 11. ADR-ИНДЕКС
    def _s11_adr_index(self) -> list[str]:
        adr_dir = HOME / "aura-companion/docs/adr"
        L = ["## 11. ADR — ИНДЕКС", ""]
        if not adr_dir.exists():
            return L + ["(нет docs/adr/)", ""]
        adrs = sorted(adr_dir.glob("*.md"))
        L.append(f"Всего ADR: {len(adrs)}")
        L.append("")
        L.append("**Ключевые:**")
        for a in adrs:
            name = a.stem
            if any(k in name.lower() for k in
                   ["053", "054", "055", "056", "057", "062",
                    "005", "007", "008", "110"]):
                L.append(f"- `{name}`")
        L.append("")
        return L

    # 12. СОСТОЯНИЕ СИСТЕМ
    def _s12_systems(self) -> list[str]:
        L = ["## 12. СОСТОЯНИЕ СИСТЕМ", ""]
        # RAG
        rag = "?"
        with contextlib.suppress(Exception):
            import sqlite3
            db = HOME / ".local/share/aura/rag_db/chroma.sqlite3"
            if db.exists():
                conn = sqlite3.connect(str(db))
                rag = conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
                conn.close()
        L.append(f"- **RAG:** {rag} диалогов")
        # Агенты
        with contextlib.suppress(Exception):
            d = HOME / "aura-companion/aura/agents"
            n = sum(1 for f in d.glob("*.py") if f.name != "__init__.py")
            L.append(f"- **Агентов (файлов):** {n}")
        # Systemd
        svc = self._systemd("aura.service")
        L.append(f"- **aura.service:** {svc}")
        # Ollama
        ollama = self._curl("http://localhost:11434/api/tags")
        if ollama:
            L.append("- **Ollama:** ✅")
        else:
            L.append("- **Ollama:** ❌")
        L.append("")
        return L

    # 13. ПРОБЛЕМЫ
    def _s13_problems(self) -> list[str]:
        return [
            "## 13. ОТКРЫТЫЕ ПРОБЛЕМЫ",
            "",
            "- 🔴 **РФРИТ грант** — дедлайн 19.10.2026 (~6 дней)",
            "- 🔴 **Bug 66** — утечка потоков listener.py (CPU 47%)",
            "- 🟡 **15 агентов** не загружены (93 файла, 78 в registry)",
            "- 🟡 **say_text** в orchestrator — потерян (проверить)",
            "- 🟡 **ISO** не грузится (vmlinuz-linux vs linux-lts)",
            "- 🟢 **RGB клавиатуры** MSI — не реализован (voice_commands)",
            "- 🟢 **Йога/цигун** — не реализован (F-111..F-115)",
            "- 🟢 **Dragon Core** визуал QML — ADR-062, не сделан",
            "",
            "Полный список — в AURA_MASTER.md, секция «Что НЕ работает».",
            "",
        ]

    # 14. СЛЕДУЮЩИЙ ШАГ
    def _s14_next_step(self) -> list[str]:
        return [
            "## 14. СЛЕДУЮЩИЙ ШАГ",
            "",
            "**Капитан, реши с чего начинаем:**",
            "",
            "1. 🇷🇺 **РФРИТ заявка** — дедлайн 19.10 (срочно!)",
            "2. 🐛 **Bug 66 fix** — утечка потоков",
            "3. 🧠 **Care-координатор MVP** — опора для автора",
            "4. 📦 **Portable-профиль MVP** (.aura/ export/import)",
            "5. 🚗 **F-150 Car-assistant** — OBD MVP, гаражный пилот",
            "",
            "**Правило входа:** капитан говорит A/B/C/D/E → я делаю A.",
            "Без выбора — не двигаюсь. WIP=1.",
            "",
            "---",
            "",
        ]

    # ═══════════════════════════════════════════════════
    def _git(self, repo: Path, args: list[str]) -> str:
        with contextlib.suppress(Exception):
            r = subprocess.run(
                ["git"] + args, cwd=str(repo),
                capture_output=True, text=True, timeout=5,
            )
            return r.stdout.strip()
        return ""

    def _open_items(self, path: Path, limit: int = 15) -> list[str]:
        out = []
        with contextlib.suppress(Exception):
            for line in path.read_text(encoding="utf-8").splitlines():
                s = line.strip()
                if s.startswith("- [ ]") or s.startswith("| F-"):
                    out.append(s)
                if len(out) >= limit:
                    break
        return out

    def _systemd(self, name: str) -> str:
        with contextlib.suppress(Exception):
            r = subprocess.run(
                ["systemctl", "--user", "is-active", name],
                capture_output=True, text=True, timeout=2,
            )
            return r.stdout.strip()
        return "?"

    def _curl(self, url: str) -> str:
        with contextlib.suppress(Exception):
            import urllib.request
            with urllib.request.urlopen(url, timeout=2) as r:
                return r.read().decode()[:200]
        return ""


__all__ = ["BriefingAgent"]
