"""F-094b: Pygame 2D-карта — процедурная графика.

Спрайты рисуются кодом:
- Звёздное поле (мерцание)
- Секторы — гексагоны
- Гиперлинии между секторами
- Корабль Aura — треугольник
- Пульсация текущего
"""
from __future__ import annotations

import math
import random
import sys

import pygame

from aura.lore.campaign import SECTORS, get_current, get_next

# ── Настройки ─────────────────────────────────────────
WIDTH, HEIGHT = 1100, 720
FPS = 30

BG = (8, 12, 24)
STAR = (180, 200, 220)
HYPER = (40, 80, 110)
TEXT = (220, 240, 230)
TEXT_DIM = (120, 150, 145)
CURRENT = (0, 255, 130)
VISITED = (0, 200, 220)
LOCKED = (90, 90, 110)
CURSOR = (255, 220, 100)
SHIP = (255, 180, 60)


class Starfield:
    """Мерцающее звёздное поле."""

    def __init__(self, n: int = 300) -> None:
        self.stars = [
            {
                "x": random.randint(0, WIDTH),
                "y": random.randint(0, HEIGHT),
                "r": random.choice([1, 1, 1, 2]),
                "phase": random.random() * math.tau,
                "speed": random.uniform(0.5, 2.0),
            }
            for _ in range(n)
        ]

    def draw(self, screen: pygame.Surface, t: float) -> None:
        for s in self.stars:
            alpha = 0.5 + 0.5 * math.sin(s["phase"] + t * s["speed"])
            c = tuple(int(v * alpha) for v in STAR)
            pygame.draw.circle(screen, c, (s["x"], s["y"]), s["r"])


class SectorMap:
    """Pygame-карта секторов F-094b."""

    # Координаты секторов (X3-стиль, сетка)
    SECTOR_POS = {
        # Grid 2x2 (X3-стиль)
        "FORMALIZE": (280, 220),   # гл.1, верх-лево
        "ORACLE":    (820, 220),   # гл.2, верх-право
        "HARDEN":    (820, 520),   # гл.3, низ-право
        "EXPAND":    (280, 520),   # гл.4, низ-лево
    }

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Aura · Star Map v2")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 16)
        self.font_title = pygame.font.SysFont("monospace", 22, bold=True)
        self.font_small = pygame.font.SysFont("monospace", 13)

        self.current = get_current()
        self.cursor = self.current
        self.visited = {self.current}
        self.running = True
        self.t = 0.0
        self.ship_angle = 0.0
        self.ship_target: tuple[int, int] | None = None
        self.ship_pos = list(self.SECTOR_POS.get(self.current, (100, 100)))

        self.names = list(SECTORS.keys())
        self.starfield = Starfield(300)

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.t += dt
            self._handle_events()
            self._update_ship(dt)
            self._draw()
        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self._on_key(event.key)

    def _on_key(self, key: int) -> None:
        if key == pygame.K_ESCAPE:
            self.running = False
        elif key == pygame.K_DOWN:
            i = self.names.index(self.cursor)
            self.cursor = self.names[(i + 1) % len(self.names)]
        elif key == pygame.K_UP:
            i = self.names.index(self.cursor)
            self.cursor = self.names[(i - 1) % len(self.names)]
        elif key == pygame.K_j:
            nxt = get_next(self.current)
            if nxt:
                self.visited.add(self.current)
                self.current = nxt
                self.cursor = nxt
                self.visited.add(nxt)
                self._start_jump()
        elif key == pygame.K_RETURN:
            self.current = self.cursor
            self.visited.add(self.cursor)
            self.ship_pos = list(self.SECTOR_POS.get(self.current, (100, 100)))

    def _start_jump(self) -> None:
        target = self.SECTOR_POS.get(self.current)
        if target:
            self.ship_target = target

    def _update_ship(self, dt: float) -> None:
        if self.ship_target is None:
            return
        tx, ty = self.ship_target
        sx, sy = self.ship_pos
        dx, dy = tx - sx, ty - sy
        dist = math.hypot(dx, dy)
        if dist < 5:
            self.ship_pos = [tx, ty]
            self.ship_target = None
            return
        speed = 400 * dt  # пикселей/сек
        self.ship_angle = math.atan2(dy, dx)
        self.ship_pos[0] += math.cos(self.ship_angle) * speed  # type: ignore[call-overload]
        self.ship_pos[1] += math.sin(self.ship_angle) * speed  # type: ignore[call-overload]

    # ── рисование ────────────────────────────────────────
    def _draw(self) -> None:
        self.screen.fill(BG)
        self._draw_grid()
        self.starfield.draw(self.screen, self.t)
        self._draw_hyperlines()
        self._draw_sectors()
        self._draw_ship()
        self._draw_hud()
        pygame.display.flip()

    def _draw_grid(self) -> None:
        """F-094d: пунктирная сетка 2x2."""
        step = 40
        color = (18, 30, 45)
        for x in range(0, WIDTH, step):
            for y in range(0, HEIGHT, step):
                if (x // step + y // step) % 2 == 0:
                    pygame.draw.circle(self.screen, color, (x, y), 1)

    def _draw_hyperlines(self) -> None:
        for name, meta in SECTORS.items():
            nxt = meta.get("next")
            if nxt and nxt in self.SECTOR_POS:
                a = self.SECTOR_POS[name]
                b = self.SECTOR_POS[nxt]
                # пунктирная линия с анимацией
                self._dashed_line(a, b, HYPER, 3)

    def _dashed_line(self, a, b, color, width) -> None:
        dx = b[0] - a[0]
        dy = b[1] - a[1]
        dist = math.hypot(dx, dy)
        if dist == 0:
            return
        ux, uy = dx / dist, dy / dist
        seg = 12
        gap = 8
        pos = (self.t * 40) % (seg + gap)
        while pos < dist:
            x1 = a[0] + ux * pos
            y1 = a[1] + uy * pos
            x2 = a[0] + ux * min(pos + seg, dist)
            y2 = a[1] + uy * min(pos + seg, dist)
            pygame.draw.line(self.screen, color, (x1, y1), (x2, y2), width)
            pos += seg + gap

    def _sector_color(self, name: str) -> tuple:
        if name == self.current:
            return CURRENT
        if name in self.visited:
            return VISITED
        return LOCKED

    def _draw_sectors(self) -> None:
        for name in self.names:
            x, y = self.SECTOR_POS.get(name, (0, 0))
            color = self._sector_color(name)
            radius = 28

            # пульсация текущего
            if name == self.current:
                pulse = int(radius + 6 + 4 * math.sin(self.t * 3))
                pygame.draw.circle(self.screen, color, (x, y), pulse, 2)
                pygame.draw.circle(self.screen, color, (x, y), radius, 0)
            elif name == self.cursor:
                pygame.draw.circle(self.screen, CURSOR, (x, y), radius + 4, 2)
                pygame.draw.circle(self.screen, color, (x, y), radius, 0)
            else:
                pygame.draw.circle(self.screen, color, (x, y), radius, 0)

            # рамка для видимых
            pygame.draw.circle(self.screen, TEXT_DIM, (x, y), radius, 1)

            # подпись
            mark = "🎯" if name == self.current else ("✓" if name in self.visited else "🔒")
            label = self.font.render(f"{mark} {name}", True, color)
            self.screen.blit(label, (x - label.get_width() // 2, y + radius + 6))

            # глава
            meta = SECTORS[name]
            sub = self.font_small.render(f"гл.{meta['chapter']}", True, TEXT_DIM)
            self.screen.blit(sub, (x - sub.get_width() // 2, y + radius + 26))

    def _draw_ship(self) -> None:
        x, y = self.ship_pos
        angle = self.ship_angle if self.ship_target else -math.pi / 2
        size = 12
        # треугольник
        pts = [
            (x + math.cos(angle) * size * 1.5, y + math.sin(angle) * size * 1.5),
            (x + math.cos(angle + 2.5) * size, y + math.sin(angle + 2.5) * size),
            (x + math.cos(angle - 2.5) * size, y + math.sin(angle - 2.5) * size),
        ]
        pygame.draw.polygon(self.screen, SHIP, pts)
        pygame.draw.polygon(self.screen, TEXT, pts, 1)

    def _draw_hud(self) -> None:
        try:
            from aura.game.state import StateStore
            s = StateStore().load()
            xp, rank = s.xp, s.rank
            hull = min(100, s.hull)
            shields = s.shields
        except Exception:
            xp, rank, hull, shields = 0, "?", 0, 0

        # заголовок
        title = self.font_title.render("🛸  AURA · STAR MAP", True, TEXT)
        self.screen.blit(title, (30, 20))

        # HUD слева внизу
        y = HEIGHT - 130
        lines = [
            (f"XP:      {xp}", TEXT),
            (f"Ранг:    {rank}", TEXT),
            (f"Корпус:  {hull}%", CURRENT if hull > 50 else SHIP),
            (f"Щиты:    {shields}%", CURRENT if shields > 50 else SHIP),
            (f"Сектор:  {self.current}", VISITED),
        ]
        for i, (line, color) in enumerate(lines):
            txt = self.font.render(line, True, color)
            self.screen.blit(txt, (30, y + i * 20))

        # Управление
        help_lines = [
            "↑↓  курсор",
            "Enter  выбрать",
            "j  прыжок",
            "Esc  выход",
        ]
        hy = 20
        for line in help_lines:
            txt = self.font_small.render(line, True, TEXT_DIM)
            self.screen.blit(txt, (WIDTH - 160, hy))
            hy += 18


def main() -> int:
    app = SectorMap()
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
