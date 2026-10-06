"""
Агент чтения экрана.

Работает через:
- maim (скриншот) → tesseract (OCR) → текст
- xdotool / wmctrl для активного окна

По науке:
- Изолирован (subprocess + tempfile)
- Тестируем (mock для subprocess)
- Не знает про AuraCore
"""

from __future__ import annotations

import os
import subprocess
import tempfile

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentScreenReader(BaseAgent):
    """
    Агент чтения экрана.

    Обрабатывает:
    - "прочитай экран" / "что на экране" → OCR всего экрана
    - "прочитай окно" / "что в окне" → OCR активного окна
    - "какое окно активно" / "активное окно" → заголовок окна
    """

    name = "screen_reader"
    MODULE_ALWAYS = True

    READ_SCREEN_KEYWORDS = ("прочитай экран", "что на экране", "прочти экран")
    READ_WINDOW_KEYWORDS = ("прочитай окно", "что в окне", "прочти окно")
    ACTIVE_WINDOW_KEYWORDS = ("активное окно", "какое окно", "текущее окно")

    OCR_LANG = "rus+eng"

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        keywords = (
            self.READ_SCREEN_KEYWORDS
            + self.READ_WINDOW_KEYWORDS
            + self.ACTIVE_WINDOW_KEYWORDS
        )
        return any(kw in text for kw in keywords)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        text = request.text.lower()

        if any(kw in text for kw in self.ACTIVE_WINDOW_KEYWORDS):
            return AgentResponse.ok(self.get_active_window(), self.name)

        if any(kw in text for kw in self.READ_WINDOW_KEYWORDS):
            return AgentResponse.ok(self.read_active_window(), self.name)

        if any(kw in text for kw in self.READ_SCREEN_KEYWORDS):
            return AgentResponse.ok(self.read_screen(), self.name)

        return AgentResponse.not_handled(self.name)

    # --- Внутренние методы ---

    def get_active_window(self) -> str:
        """Заголовок активного окна."""
        try:
            result = subprocess.run(
                ["xdotool", "getactivewindow", "getwindowname"],
                capture_output=True,
                text=True,
                check=False,
            )
            name = result.stdout.strip()
            if not name:
                return "🪟 Не удалось определить активное окно"
            return f"🪟 Активное окно: {name}"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def read_screen(self) -> str:
        """OCR всего экрана."""
        return self._ocr_region(None)

    def read_active_window(self) -> str:
        """OCR активного окна."""
        try:
            result = subprocess.run(
                ["xdotool", "getactivewindow"],
                capture_output=True,
                text=True,
                check=False,
            )
            wid = result.stdout.strip()
            if not wid:
                return "❌ Не удалось определить активное окно"
            return self._ocr_region(wid)
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def _ocr_region(self, window_id: str | None) -> str:
        """Сделать скриншот и прогнать через tesseract."""
        tmp_path = None
        try:
            fd, tmp_path = tempfile.mkstemp(suffix=".png", prefix="aura_ocr_")
            os.close(fd)

            # Скриншот
            shot_cmd = ["maim", "-i", window_id, tmp_path] if window_id else ["maim", tmp_path]

            shot = subprocess.run(shot_cmd, capture_output=True, text=True, check=False)
            if shot.returncode != 0:
                return f"❌ Не удалось сделать скриншот: {shot.stderr.strip()}"

            # OCR
            ocr = subprocess.run(
                ["tesseract", tmp_path, "-", "-l", self.OCR_LANG],
                capture_output=True,
                text=True,
                check=False,
            )
            if ocr.returncode != 0:
                return f"❌ OCR не сработал: {ocr.stderr.strip()}"

            text = ocr.stdout.strip()
            if not text:
                return "🔍 На экране нет распознаваемого текста"

            # Ограничить 800 символами
            if len(text) > 800:
                text = text[:797] + "..."
            return f"📖 Прочитала:\n{text}"
        except Exception as e:
            return f"❌ Ошибка OCR: {e}"
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception as e:
                    # F-006: не глотать (раздел 17 промта)
                    import logging
                    logging.getLogger('aura.screen_reader').debug(
                        'screen_reader error: %s', e)


__all__ = ["AgentScreenReader"]
