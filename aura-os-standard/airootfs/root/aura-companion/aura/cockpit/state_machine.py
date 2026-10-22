"""StateMachine — зональный диспетчер.

Две фазы:
  1. Главный шлюз — выбор зоны (7 зон + выход)
  2. Внутри зоны — выбор действия

Наука: Brooks 1975 (диспетчер тонкий),
       Nielsen 1993 (recognition over recall).
"""

from __future__ import annotations

import contextlib

from aura.cockpit import menu as menu_mod
from aura.cockpit.guided_ui import run_guided
from aura.game.render_ascii import RenderAscii
from aura.game.spawner import count_threat, spawn_enemies_from_ruff
from aura.game.state import StateStore
from aura.lore.story import StoryLog


class CockpitSession:
    """Сессия кабинета. Зональный интерфейс."""

    def __init__(self, speak: bool = True):
        self.speak = speak
        self.renderer = RenderAscii()
        self.store = StateStore()
        self.state = self.store.load()
        self.story = StoryLog()
        self.orch = None
        if speak:
            try:
                from aura.voice.orchestrator import VoiceOrchestrator
                self.orch = VoiceOrchestrator()
            except Exception:
                self.orch = None

    # ── голос ────────────────────────────────────────────
    def _say(self, event: str, **ctx) -> None:
        if self.orch is None:
            return
        try:
            self.orch.say(event, **ctx)
        except Exception as e:
            print(f"⚠️ [voice] {e}")

    # ── перезагрузка ─────────────────────────────────────
    def _reload(self) -> None:
        self.store.close()
        self.store = StateStore()
        self.state = self.store.load()

    # ── главный цикл ─────────────────────────────────────
    def run(self) -> None:
        print()
        print(self.renderer.render_hud(self.state, self.story))
        self._say("hyperjump", modules=78)

        try:
            while True:
                # Главный шлюз
                print()
                print(self.renderer.render_menu(
                    "ГЛАВНЫЙ ШЛЮЗ",
                    [label for _, label in menu_mod.ZONES],
                ))
                try:
                    raw = input("\nКапитан? > ")
                except (EOFError, KeyboardInterrupt):
                    break

                zone = menu_mod.parse_zone_choice(raw)
                if zone is None:
                    if raw.strip() in ("0", "q", ""):
                        break
                    print("❓ Не поняла. Введи номер зоны.")
                    continue

                # Внутри зоны — цикл
                self._run_zone(zone)
                self._reload()
                print()
                print(self.renderer.render_hud(self.state, self.story))
        except KeyboardInterrupt:
            # Ctrl+C на любом уровне — graceful shutdown
            pass

        self._exit()

    def _run_zone(self, zone: str) -> None:
        """Цикл внутри зоны: подменю → действие → снова подменю."""
        while True:
            print()
            zone_title = dict(menu_mod.ZONES)[zone]
            print(self.renderer.render_menu(zone_title, [
                label for _, label in menu_mod.SUB_MENUS.get(zone, [])
            ]))
            try:
                raw = input("\nКапитан? > ")
            except (EOFError, KeyboardInterrupt):
                return

            action = menu_mod.parse_sub_choice(raw, zone)
            if action is None:
                return  # 0 = назад в главный шлюз

            handler = getattr(self, f"_do_{zone}_{action}", None)
            if handler is None:
                print(f"⚠️ Действие {zone}.{action} не реализовано")
            else:
                try:
                    handler()
                except Exception as e:
                    print(f"⚠️ [{zone}.{action}] {e}")
            self._reload()

    # ── ЗОНА: ОТДЫХ ──────────────────────────────────────
    def _do_rest_status(self) -> None:
        for line in menu_mod.build_status_lines():
            print("  " + line)
        self._say("status", shields=self.state.shields, reactor="чист",
                  sector=self.state.sector, xp=self.state.xp)
        self._pause()

    def _do_rest_form(self) -> None:
        from aura.cockpit.form import render_form
        print()
        print(render_form(verbose=False))
        self._pause()

    def _do_rest_form_v(self) -> None:
        from aura.cockpit.form import render_form
        print()
        print(render_form(verbose=True))
        self._pause()

    def _do_rest_brief(self) -> None:
        for line in menu_mod.build_brief_lines():
            print(f"📋 {line}")
        self._say("briefing", sector=self.state.sector,
                  remaining=0, active=0,
                  active_line="Задач в очереди: 0.")
        self._pause()

    def _do_rest_diary(self) -> None:
        tail = self.story.get_journal_tail(5)
        print(tail or "(журнал пуст)")
        self._pause()

    def _do_rest_remind(self) -> None:
        print("⏰ Напоминания — в F-061 (Calendar). Пока не работает.")
        self._pause()

    # ── ЗОНА: КАБИНА ─────────────────────────────────────
    def _do_cockpit_scan(self) -> None:
        """СКАН → сразу бой. Без меню, без возвратов.

        Цикл:
          1. Сканируем сектор — находим врагов.
          2. Для каждого врага — сразу run_guided.
          3. Победа → следующий. Отступление → выход.
        """
        from aura.game.problem import Problem

        print()
        print("═" * 64)
        print("🔭 СКАНИРОВАНИЕ СЕКТОРА")
        print("═" * 64)
        self._say("recon")

        targets = ("aura/", "scripts/", "tests/")
        fleet = []
        for t in targets:
            for e in spawn_enemies_from_ruff(t):
                fleet.append(e)

        if not fleet:
            print("\n✅ Сектор чист. Все системы в норме.")
            self._say("status",
                      shields=self.state.shields, reactor="чист",
                      sector=self.state.sector, xp=self.state.xp)
            self._pause()
            return

        print(f"\n🔴 ОБНАРУЖЕНО: {len(fleet)} врагов, "
              f"суммарная угроза: {count_threat(fleet)}")
        print()
        for i, e in enumerate(fleet[:12], 1):
            etype = {"drone": "🛸", "interceptor": "⚡",
                     "frigate": "🚀", "leviathan": "🐙"}.get(
                e.enemy_type, "👾")
            print(f"   {i:2}. {etype} {e.name:<8} "
                  f"угроза {e.threat}/5  @ {e.sector}:{e.line}")
        if len(fleet) > 12:
            print(f"   ... и ещё {len(fleet) - 12}")

        print()
        try:
            input("Enter — к бою... ")
        except (EOFError, KeyboardInterrupt):
            return

        # ── Непрерывный бой ──
        killed = 0
        for i, e in enumerate(fleet, 1):
            print()
            print("═" * 64)
            print(f"🎯 ЦЕЛЬ {i}/{len(fleet)}: {e.name} "
                  f"({e.enemy_type}, угроза {e.threat}/5)")
            print(f"   Сектор: {e.sector}:{e.line}")
            print("═" * 64)

            problem = Problem(
                code=e.name,
                sector=e.sector,
                line=e.line,
                raw_message=getattr(e, "message", ""),
            )
            ok = run_guided(problem, speak=self.speak)
            if not ok:
                print(f"\n🛸 Отступление. Убито: {killed}/{len(fleet)}")
                self._pause()
                return
            killed += 1

            self._reload()
            pct = self.state.progress
            print(f"  ✅ Убито: {killed}/{len(fleet)}  |  "
                  f"XP: {self.state.xp}  |  Сборка: {pct}%")

        # Итог
        print()
        print("═" * 64)
        print(f"🎉 СЕКТОР ЗАЧИЩЕН. Убито: {killed}/{len(fleet)}")
        print(f"   XP: {self.state.xp}  |  Ранг: {self.state.rank}")
        self._say("sector_clear",
                  old=self.state.sector, new="FORMALIZE")
        self._pause()

    def _do_cockpit_quest(self) -> None:
        """НЕПРЕРЫВНОЕ ПУТЕШЕСТВИЕ по roadmap.

        1. Победа → следующая задача из ROADMAP-V2.
        2. Наведение → прицел → выстрел.
        3. Никаких возвратов в меню.
        """
        from aura.game import roadmap
        from aura.game.problem import Problem

        print()
        print(self.renderer.render_menu("ПУТЕШЕСТВИЕ", [
            "Всё по roadmap — от начала до конца",
            "Только aura/ — текущий флот",
            "Только scripts/ — текущий флот",
            "Начать с конкретной задачи F-XXX",
        ]))
        try:
            raw = input("\nКапитан? > ").strip()
        except (EOFError, KeyboardInterrupt):
            return

        killed = 0

        # Режим: только aura/ — берём врагов из spawner
        if raw == "2":
            fleet = spawn_enemies_from_ruff("aura/")
            killed = self._continuous_flight(
                [Problem(
                    code=e.name, sector=e.sector,
                    line=e.line, raw_message=getattr(e, "message", "")
                ) for e in fleet]
            )
        elif raw == "3":
            fleet = spawn_enemies_from_ruff("scripts/")
            killed = self._continuous_flight(
                [Problem(
                    code=e.name, sector=e.sector,
                    line=e.line, raw_message=getattr(e, "message", "")
                ) for e in fleet]
            )
        elif raw == "4":
            input("Задача (F-XXX): > ")  # F-XXX, читаем для UX
            q = roadmap.next_quest()
            if q is None:
                print("✅ Roadmap пуст.")
                return
            print(f"🎯 {q.code}: {q.title}")
            killed = self._continuous_flight([self._quest_to_problem(q)])
        else:
            # Режим ВСЁ — бесконечный полёт по roadmap
            killed = self._endless_flight()

        # Итог
        if killed > 0:
            self._reload()
            self._say("sector_clear",
                      old=self.state.sector, new="FORMALIZE")
            print()
            print("═" * 64)
            print(f"🛸 ПУТЕШЕСТВИЕ ЗАВЕРШЕНО. Всего убито: {killed}")
            print(f"   XP: {self.state.xp}  |  Ранг: {self.state.rank}")

    def _continuous_flight(self, problems: list) -> int:
        """Летит по списку проблем. Возвращает число убитых."""
        killed = 0
        total = len(problems)
        for i, problem in enumerate(problems, 1):
            print()
            print(f"  ─── ЦЕЛЬ {i}/{total} │ всего убито: {killed} ───")
            ok = run_guided(problem, speak=self.speak)
            if not ok:
                print(f"\n🛸 Отступление. Убито: {killed}.")
                return killed
            killed += 1
            self._reload()
            print(f"  ✅ Убито: {killed}  |  XP: {self.state.xp}  |  "
                  f"Ранг: {self.state.rank}  |  Сборка: {self.state.progress}%")
        return killed

    def _endless_flight(self) -> int:
        """Бесконечный полёт: сначала ruff, потом roadmap."""
        from aura.game.problem import Problem

        killed = 0

        # Фаза 1: реальные баги (aura/ + scripts/ + tests/)
        for target in ("aura/", "scripts/", "tests/"):
            fleet = spawn_enemies_from_ruff(target)
            if not fleet:
                print(f"\n✅ Сектор {target} чист.")
                continue
            print(f"\n🛸 Сектор {target}: {len(fleet)} врагов")
            problems = [
                Problem(code=e.name, sector=e.sector,
                        line=e.line, raw_message=getattr(e, "message", ""))
                for e in fleet
            ]
            for i, p in enumerate(problems, 1):
                print()
                print(f"  ─── {target} │ цель {i}/{len(problems)} "
                      f"│ всего: {killed} ───")
                ok = run_guided(p, speak=self.speak)
                if not ok:
                    return killed
                killed += 1
                self._reload()
                print(f"  ✅ XP: {self.state.xp}  |  "
                      f"Сборка: {self.state.progress}%")

        # Фаза 2: задачи из roadmap (код-фиксы вручную)
        from aura.game import roadmap
        queue = roadmap.load_roadmap()
        if queue:
            print(f"\n📋 Roadmap: {len(queue)} задач")
            print("   (код-фиксы roadmap — следующий шаг F-060)")

        return killed

    def _quest_to_problem(self, q):
        """Quest → Problem для боя."""
        from aura.game.problem import Problem
        # Ищем реальный баг в aura/, привязанный к q.code
        return Problem(
            code=q.code,
            sector="aura/",
            line=0,
            raw_message=q.title,
        )

    def _do_cockpit_problem(self) -> None:
        from aura.game.problem import Problem

        fleet = spawn_enemies_from_ruff("aura/")
        if not fleet:
            print("✅ Сектор чист — проблем нет.")
            self._pause()
            return

        e = fleet[0]
        problem = Problem(
            code=e.name,
            sector=e.sector,
            line=e.line,
            raw_message=getattr(e, "message", ""),
        )
        run_guided(problem, speak=self.speak)
        self._pause()

    def _do_cockpit_battle(self) -> None:
        from aura.cockpit.combat_ui import fight
        from aura.game.combat import Enemy
        e = Enemy("TrainingDrone", "drone", "aura/train.py", 1, 80, 1)
        fight(e, level=self.state.level, speak=self.speak)

    # ── ЗОНА: БОЕЗАПАС ───────────────────────────────────
    def _do_arsenal_weapons(self) -> None:
        from aura.game.combat import ARSENAL
        print()
        for _k, w in ARSENAL.items():
            sign = "+" if w.xp_reward >= 0 else ""
            print(f"  {w.name:<18} {w.strategy:<10} "  # type: ignore[attr-defined]
                  f"шанс {w.base_chance}% урон {w.damage} XP {sign}{w.xp_reward}")
        self._pause()

    def _do_arsenal_patterns(self) -> None:
        from aura.game.patterns import PATTERNS
        print()
        for code, p in PATTERNS.items():
            print(f"  [{code}] {p.title:<30} → {p.strategy} ({p.difficulty}/5)")
        self._pause()

    def _do_arsenal_upgrade(self) -> None:
        print(f"💰 XP: {self.state.xp}. Апгрейд — в F-059 (после боя).")
        self._pause()

    # ── ЗОНА: ЖУРНАЛ ─────────────────────────────────────
    def _do_journal_tail(self) -> None:
        for line in menu_mod.build_journal_lines(10):
            print("  " + line)
        self._pause()

    def _do_journal_search(self) -> None:
        print("🔍 Поиск по журналу — в F-060 (Knowledge).")
        self._pause()

    def _do_journal_export(self) -> None:
        print("💾 Экспорт — в F-060 (Knowledge).")
        self._pause()

    # ── ЗОНА: ПАМЯТЬ ─────────────────────────────────────
    def _do_memory_note(self) -> None:
        try:
            from scripts.aura_note import append_note
            text = input("📝 Заметка > ").strip()
            if text:
                path = append_note(text)
                print(f"✅ {path}")
        except Exception as e:
            print(f"⚠️ {e}")
        self._pause()

    def _do_memory_find(self) -> None:
        print("🔍 Поиск по файлам — в F-060 (Knowledge).")
        self._pause()

    def _do_memory_read_story(self) -> None:
        from pathlib import Path
        p = Path.home() / "aura_private" / "STORY.md"
        if p.exists():
            print(p.read_text(encoding="utf-8")[-2000:])
        else:
            print("(STORY.md не найден)")
        self._pause()

    def _do_memory_read_roadmap(self) -> None:
        from pathlib import Path
        p = Path.home() / "aura_private" / "ROADMAP-V2.md"
        if p.exists():
            print(p.read_text(encoding="utf-8")[:2000])
        else:
            print("(ROADMAP-V2.md не найден)")
        self._pause()

    # ── ЗОНА: СВЯЗЬ ──────────────────────────────────────
    def _do_comm_deepseek(self) -> None:
        print("\n💬 Bridge к DeepSeek — F-057c (не готово).")
        self._pause()

    def _do_comm_vk(self) -> None:
        print("📡 VK — уже работает как агент, меню в M3.")
        self._pause()

    def _do_comm_calendar(self) -> None:
        print("📅 Календарь — F-061.")
        self._pause()

    def _do_settings_deep(self) -> None:
        from aura.system.deep_check import render_report
        print()
        print(render_report(verbose=True))
        # Голосом — итог
        from aura.system.deep_check import run_deep_check
        report = run_deep_check()
        if report.all_ok:
            self._say("status", shields=100, reactor="чист",
                      sector=self.state.sector, xp=self.state.xp)
        else:
            self._say("bug_found", count=len(report.failures()))
        self._pause()

    # ── ЗОНА: СПУСТИТЬ ВОЗДУХ (ONE-SHOT) ────────────────
    def _do_oneshot_run(self) -> None:
        from aura.system.oneshot import run_oneshot
        print()
        run_oneshot(dry_run=False, restart_daemon=True)
        self._say("status", shields=100, reactor="чист",
                  sector=self.state.sector, xp=self.state.xp)
        self._pause()

    def _do_oneshot_dry(self) -> None:
        from aura.system.oneshot import run_oneshot
        print()
        run_oneshot(dry_run=True, restart_daemon=False)
        self._pause()

    # ── ЗОНА: УПРАВЛЕНИЕ ПК ─────────────────────────────
    def _do_pc_panel(self) -> None:
        from aura.cockpit.pc_ui import pc_menu
        pc_menu()

    # ── ЗОНА: НАСТРОЙКИ ──────────────────────────────────
    def _do_settings_mute(self) -> None:
        print("🔇 Mute — F-062 (settings integration).")
        self._pause()

    def _do_settings_volume(self) -> None:
        print("🔊 Volume — F-062.")
        self._pause()

    def _do_settings_voice(self) -> None:
        print("🗣️ Проверка голоса...")
        self._say("status", shields=self.state.shields, reactor="чист",
                  sector=self.state.sector, xp=self.state.xp)
        self._pause()

    # ── утилиты ──────────────────────────────────────────
    def _pause(self) -> None:
        with contextlib.suppress(EOFError, KeyboardInterrupt):
            input("\nEnter — назад...")

    def _exit(self) -> None:
        # Save перед выходом
        with contextlib.suppress(Exception):
            self.state.recalc_progress()
            self.store.save(self.state)
        self.store.close()
        print()
        print("═" * 64)
        print("🦾 Аура: Прогресс сохранён. Кабинет закрыт.")
        print("       Корабль продолжает полёт.")
        print("       Слушаю микрофон. Скажи 'Аура' — отвечу.")
        print("═" * 64)


def run_session(speak: bool = True) -> None:
    CockpitSession(speak=speak).run()


__all__ = ["CockpitSession", "run_session"]
