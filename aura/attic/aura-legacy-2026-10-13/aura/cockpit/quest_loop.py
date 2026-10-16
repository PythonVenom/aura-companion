"""Quest Loop — зацикленный диалог миссии.

Один вход → бой со всеми врагами → сюжет двигается.
Промах не закрывает цикл — выбор оружия повторяется.
Отступление возможно (skip), но тогда квест открыт.

Наука: Csikszentmihalyi 1990 (flow через повтор),
       Duhigg 2012 (habit loop — триггер → действие → награда).
"""

from __future__ import annotations

from aura.cockpit.combat_ui import ask_weapon, show_encounter
from aura.game.combat import ARSENAL, resolve_combat
from aura.game.quest import Quest
from aura.game.state import StateStore
from aura.lore.story import StoryLog
from aura.voice.orchestrator import VoiceOrchestrator


def _record_victory(enemy, result, state, story, store) -> None:
    """Победа над врагом — сохранить в state и журнал."""
    if result.xp:
        state.add_xp(result.xp)
    state.hull = max(0, state.hull)
    story.log_maneuver(
        commit=enemy.name,
        description=f"Победа: {enemy.name} @ {enemy.sector}:{enemy.line}",
        day=state.days_on_planet(),
        sector=state.sector,
    )
    store.save(state)


def _record_miss(enemy, state, story, store) -> None:
    """Промах — щиты падают, запись в журнал."""
    state.shields = max(0, state.shields - 10)
    story.log_maneuver(
        commit="miss",
        description=f"Промах по {enemy.name}",
        day=state.days_on_planet(),
        sector=state.sector,
    )
    store.save(state)


def run_quest(quest: Quest, speak: bool = True,
              max_attempts_per_enemy: int = 10) -> dict:
    """Зацикленный бой. Возвращает итог квеста.

    Returns:
        {"cleared": bool, "aborted": bool, "xp": int, "battles": int}
    """
    orch = VoiceOrchestrator() if speak else None
    store = StateStore()
    state = store.load()
    story = StoryLog()

    print()
    print("=" * 64)
    print(f"🎯 КВЕСТ: {quest.name}")
    print(f"   Сектор: {quest.sector_from} → {quest.sector_to}")
    print(f"   Флот: {quest.total} врагов, побеждено: 0")
    print("=" * 64)

    if orch:
        orch.say("enemy_spotted", file=quest.name)

    # Отступление в любой момент — команда 'q' в ask_weapon
    while not quest.is_clear:
        enemy = quest.remaining[0]
        attempts = 0

        # Зацикливаем бой с ОДНИМ врагом до победы
        while enemy.hp > 0:
            attempts += 1
            if attempts > max_attempts_per_enemy:
                print(f"\n⚠️  Слишком много попыток ({max_attempts_per_enemy}). "
                      f"Отступаем.")
                quest.aborted = True
                break

            print()
            print(show_encounter(enemy,
                                 shields=state.shields,
                                 hull=state.hull,
                                 reactor=state.reactor))

            action = ask_weapon(
                "Приказ, капитан? [1-6, q=отступить] "
            )
            if action is None:
                quest.aborted = True
                break

            weapon = ARSENAL[action]

            # Прыжок = отступление
            if action == "skip":
                print("\n🛸 Прыжок. Отступаем из сектора.")
                quest.aborted = True
                break

            print(f"\n🎲 {weapon.name}...")
            if orch:
                orch.say("shot_fired")

            result = resolve_combat(enemy, weapon, level=state.level)
            quest.battles += 1
            print(f"\n{result.message}")

            if result.hit:
                quest.xp_earned += result.xp
                _record_victory(enemy, result, state, story, store)
                if orch:
                    if result.enemy_destroyed:
                        orch.say("fix_success", hull=state.hull)
                    else:
                        orch.say("shot_fired")
                print(f"   HP врага: {enemy.hp}")
                # Перечитать state
                store.close()
                store = StateStore()
                state = store.load()
            else:
                _record_miss(enemy, state, story, store)
                store.close()
                store = StateStore()
                state = store.load()
                if orch:
                    orch.say("miss")
                print(f"   Щиты: {state.shields}%  HP врага: {enemy.hp}")

            # Если враг мёртв — выходим из внутреннего цикла
            if enemy.hp <= 0:
                print(f"\n✅ {enemy.name} уничтожен. "
                      f"Прогресс: {quest.killed}/{quest.total}")
                break

        # Если отступили — выходим совсем
        if quest.aborted:
            break

    # Итог квеста
    print()
    print("=" * 64)
    if quest.is_clear and not quest.aborted:
        print(f"🎉 КВЕСТ ЗАКРЫТ: {quest.name}")
        print(f"   Врагов побеждено: {quest.killed}/{quest.total}")
        print(f"   Боёв: {quest.battles}, XP: +{quest.xp_earned}")
        if orch:
            orch.say("sector_clear",
                     old=quest.sector_from, new=quest.sector_to)
        # Записать в журнал закрытие квеста
        story.log_maneuver(
            commit="QUEST-COMPLETE",
            description=f"Сектор {quest.sector_from} закрыт",
            day=state.days_on_planet(),
            sector=quest.sector_to,
        )
        # Двинуть сюжет
        state.sector = quest.sector_to
        store.save(state)
    else:
        print(f"🛸 Квест не закрыт. Отступили с {quest.killed}/{quest.total}.")
        if orch:
            orch.say("miss")

    print("=" * 64)
    store.close()

    return {
        "cleared": quest.is_clear and not quest.aborted,
        "aborted": quest.aborted,
        "xp": quest.xp_earned,
        "battles": quest.battles,
        "killed": quest.killed,
        "total": quest.total,
    }
