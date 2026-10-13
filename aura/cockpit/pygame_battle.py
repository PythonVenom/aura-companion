"""F-094c: Pygame 2D-бой.

Визуальный бой: корабль vs враг-баг.
- Враги из ruff (spawn_enemies_from_ruff)
- resolve_combat + XP
- HP-бары, лог, анимация
"""
from __future__ import annotations

import contextlib
import random
import sys

import pygame

from aura.cockpit.pygame_sounds import Sounds
from aura.game.combat import ARSENAL, resolve_combat
from aura.game.spawner import spawn_enemies_from_ruff
from aura.game.state import StateStore
from aura.lore.advisors import ADVISORS, advisor_speak

# ── Настройки ─────────────────────────────────────────
WIDTH, HEIGHT = 1100, 720
FPS = 30

BG = (8, 12, 24)
TEXT = (220, 240, 230)
TEXT_DIM = (120, 150, 145)
PLAYER = (0, 255, 130)
ENEMY = (255, 80, 80)
ENEMY_HIT = (255, 200, 80)
HP_GREEN = (60, 220, 100)
HP_RED = (220, 60, 60)
HP_BG = (40, 40, 50)
SHIP = (255, 180, 60)


class PygameBattle:
    """Визуальный бой (F-094c)."""

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Aura · Battle")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 16)
        self.font_big = pygame.font.SysFont("monospace", 24, bold=True)
        self.font_small = pygame.font.SysFont("monospace", 13)

        # State
        self.store = StateStore()
        self.state = self.store.load()

        # Враги из ruff
        try:
            all_enemies = spawn_enemies_from_ruff("aura/")
        except Exception:
            all_enemies = []
        # Если пусто — синтетический враг
        if not all_enemies:
            from aura.game.combat import Enemy
            all_enemies = [Enemy(
                name="Fake Bug", enemy_type="drone", sector="aura/",
                line=1, hp=50, threat=3,
            )]
        self.all_enemies = all_enemies
        self.enemy_idx = 0
        self.enemy = self.all_enemies[0]
        self.enemy_max_hp = self.enemy.hp

        # Анимация удара
        self.hit_flash = 0.0
        self.shot_line: tuple | None = None
        self.shot_t = 0.0

        # Лог
        self.log: list[str] = []
        self._log(f"Бой начался: {self.enemy.name} [{self.enemy.enemy_type}] HP {self.enemy.hp}")
        self._log("A — Точный залп · R — Ракета · D — Дрон · F — Импульс · C — Советник · Esc — выход")

        self.running = True
        self.ended = False
        self.sounds = Sounds()
        self.t = 0.0

    # ── события ─────────────────────────────────────────
    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.t += dt
            if self.hit_flash > 0:
                self.hit_flash = max(0.0, self.hit_flash - dt)
            if self.shot_t > 0:
                self.shot_t = max(0.0, self.shot_t - dt)
            self._handle_events()
            self._draw()
        pygame.quit()
        self._save()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self._on_key(event.key)

    def _on_key(self, key: int) -> None:
        if key == pygame.K_ESCAPE:
            self.running = False
            return
        if self.ended:
            return
        actions = {
            pygame.K_a: "fix_anchor",
            pygame.K_r: "rewrite",
            pygame.K_d: "debug",
            pygame.K_f: "autofix",
            pygame.K_s: "skip",
        }
        if key in actions:
            self._do_attack(actions[key])
        elif key == pygame.K_c:
            self._counsel()

    def _do_attack(self, action: str) -> None:
        weapon = ARSENAL.get(action)
        if not weapon:
            return
        result = resolve_combat(self.enemy, weapon, level=self.state.level)
        self._log(result.message)
        self.sounds.play("shot" if result.hit else "click")
        self.hit_flash = 0.4
        self.shot_line = (action, self.t)
        self.shot_t = 0.3

        if result.hit:
            if result.xp:
                self.state.add_xp(result.xp)
        else:
            self.state.shields = max(0, self.state.shields - 10)

        if result.enemy_destroyed or action == "skip":
            self._next_enemy()

    def _counsel(self) -> None:
        key = random.choice(["tactician", "engineer", "navigator"])
        adv = ADVISORS[key]
        line = advisor_speak(key, "battle_start") or adv.motto
        self.sounds.play("advisor")
        self._log(f"{adv.emoji} {adv.name}: {line}")

    def _next_enemy(self) -> None:
        alive = [e for e in self.all_enemies if e.hp > 0]
        if not alive:
            self.sounds.play("win")
            self._log("🎉 Все враги уничтожены!")
            self.ended = True
            return
        self.enemy = alive[0]
        self.enemy_idx = self.all_enemies.index(self.enemy)
        self.enemy_max_hp = max(self.enemy.hp, 1)
        self._log(f"🎯 Следующая цель: {self.enemy.name} HP {self.enemy.hp}")

    def _log(self, msg: str) -> None:
        self.log.append(msg)
        if len(self.log) > 8:
            self.log.pop(0)

    def _save(self) -> None:
        with contextlib.suppress(Exception):
            self.store.save(self.state)

    # ── рисование ───────────────────────────────────────
    def _draw(self) -> None:
        self.screen.fill(BG)
        self._draw_stars()
        self._draw_ship()
        self._draw_enemy()
        self._draw_shot()
        self._draw_hud()
        self._draw_log()
        pygame.display.flip()

    def _draw_stars(self) -> None:
        rnd = random.Random(42)
        for _ in range(120):
            x = rnd.randint(0, WIDTH)
            y = rnd.randint(0, HEIGHT)
            a = 0.3 + 0.7 * random.random()
            c = tuple(int(v * a) for v in (140, 160, 180))
            pygame.draw.circle(self.screen, c, (x, y), 1)

    def _draw_ship(self) -> None:
        cx, cy = 220, HEIGHT // 2
        size = 24
        # треугольник вправо
        pts = [
            (cx + size, cy),
            (cx - size, cy - size * 0.7),
            (cx - size, cy + size * 0.7),
        ]
        pygame.draw.polygon(self.screen, SHIP, pts)
        pygame.draw.polygon(self.screen, TEXT, pts, 2)
        # подпись
        label = self.font.render("Ты", True, PLAYER)
        self.screen.blit(label, (cx - label.get_width() // 2, cy + size + 10))

    def _draw_enemy(self) -> None:
        cx, cy = 820, HEIGHT // 2
        # размер по threat
        size = 20 + self.enemy.threat * 4
        # цвет: мигает при ударе
        color = ENEMY_HIT if self.hit_flash > 0 else ENEMY
        # ромб
        pts = [(cx, cy - size), (cx + size, cy), (cx, cy + size), (cx - size, cy)]
        pygame.draw.polygon(self.screen, color, pts)
        pygame.draw.polygon(self.screen, TEXT, pts, 2)
        # имя
        label = self.font.render(self.enemy.name, True, color)
        self.screen.blit(label, (cx - label.get_width() // 2, cy + size + 10))
        # HP бар над врагом
        self._draw_bar(
            x=cx - 100, y=cy - size - 30, w=200, h=14,
            value=self.enemy.hp, max_value=self.enemy_max_hp,
            color=HP_RED,
        )

    def _draw_shot(self) -> None:
        if self.shot_t <= 0 or self.shot_line is None:
            return
        # луч от корабля к врагу
        start = (240, HEIGHT // 2)
        end = (800, HEIGHT // 2)
        width = max(1, int(self.shot_t * 20))
        pygame.draw.line(self.screen, ENEMY_HIT, start, end, width)

    def _draw_hud(self) -> None:
        # заголовок
        title = self.font_big.render("⚔  AURA · BATTLE", True, TEXT)
        self.screen.blit(title, (30, 20))

        # HP корабля
        self._draw_bar(
            x=30, y=70, w=300, h=18,
            value=min(100, self.state.hull), max_value=100,
            color=HP_GREEN, label="Корпус",
        )
        self._draw_bar(
            x=30, y=100, w=300, h=18,
            value=self.state.shields, max_value=100,
            color=(80, 160, 255), label="Щиты",
        )
        # XP
        xp = self.font.render(f"XP: {self.state.xp}", True, PLAYER)
        self.screen.blit(xp, (30, 130))
        rank = self.font.render(f"Ранг: {self.state.rank}", True, TEXT_DIM)
        self.screen.blit(rank, (180, 130))
        # осталось врагов
        alive = sum(1 for e in self.all_enemies if e.hp > 0)
        rest = self.font.render(f"Врагов осталось: {alive}/{len(self.all_enemies)}", True, TEXT_DIM)
        self.screen.blit(rest, (30, 155))

        # управление
        keys = [
            "A · точный залп",
            "R · ракета",
            "D · дрон",
            "F · импульс",
            "S · прыжок",
            "C · советник",
            "Esc · выход",
        ]
        y = 20
        for k in keys:
            txt = self.font_small.render(k, True, TEXT_DIM)
            self.screen.blit(txt, (WIDTH - 200, y))
            y += 18

    def _draw_bar(self, x, y, w, h, value, max_value, color, label=""):
        pygame.draw.rect(self.screen, HP_BG, (x, y, w, h))
        ratio = max(0.0, min(1.0, value / max(max_value, 1)))
        pygame.draw.rect(self.screen, color, (x, y, int(w * ratio), h))
        pygame.draw.rect(self.screen, TEXT_DIM, (x, y, w, h), 1)
        if label:
            txt = self.font_small.render(f"{label} {int(value)}/{int(max_value)}", True, TEXT)
            self.screen.blit(txt, (x + w + 10, y + 1))

    def _draw_log(self) -> None:
        y = HEIGHT - 8 * 18 - 20
        for i, line in enumerate(self.log[-8:]):
            color = TEXT if i == len(self.log[-8:]) - 1 else TEXT_DIM
            txt = self.font.render(line, True, color)
            self.screen.blit(txt, (30, y + i * 18))


def main() -> int:
    app = PygameBattle()
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
