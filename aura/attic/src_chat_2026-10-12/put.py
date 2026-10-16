# put.py — Путь (Progression Engine)
# Задача: прокачка, Кванты, дерево развития.

import json
import os
from datetime import datetime

SAVE_FILE = os.path.expanduser("~/.aura_progress.json")

# Дерево развития: 5 веток × 5 уровней
TREE = {
    "Ядро": [
        "Тонкая настройка планировщика",
        "Управление энергией",
        "Кастомные патчи ядра",
        "Реалтайм-ядро",
        "Своё микроядро",
    ],
    "Драйверы": [
        "Обновление драйверов",
        "Оптимизация GPU",
        "Кастомные модули",
        "Продвинутая трассировка",
        "Свои драйверы",
    ],
    "ИИ": [
        "Локальный LLM",
        "Память Ауры",
        "Мораль Ауры",
        "Сюжет Ауры",
        "Полный симбиоз",
    ],
    "Безопасность": [
        "Базовая защита",
        "Шифрование",
        "Песочницы",
        "Аудит системы",
        "Своя криптография",
    ],
    "Интерфейс": [
        "Темы оформления",
        "Голосовое управление",
        "Жесты",
        "AR-оверлей",
        "Полный нейро-интерфейс",
    ],
}


class Put:
    def __init__(self):
        self.state = self.load()

    def load(self):
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, "r") as f:
                return json.load(f)
        return {
            "quants": 100,
            "level": 1,
            "branches": {b: 0 for b in TREE},
            "history": [],
            "created": datetime.now().isoformat(),
        }

    def save(self):
        with open(SAVE_FILE, "w") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)

    def award(self, amount, reason):
        self.state["quants"] += amount
        self.state["history"].append({
            "ts": datetime.now().isoformat(),
            "amount": amount,
            "reason": reason,
        })
        self.save()
        return f"+{amount} Квантов ({reason}). Всего: {self.state['quants']}."

    def spend(self, amount, reason):
        if self.state["quants"] < amount:
            return f"❌ Не хватает Квантов. Нужно {amount}, есть {self.state['quants']}."
        self.state["quants"] -= amount
        self.state["history"].append({
            "ts": datetime.now().isoformat(),
            "amount": -amount,
            "reason": reason,
        })
        self.save()
        return f"-{amount} Квантов ({reason}). Осталось: {self.state['quants']}."

    def upgrade(self, branch):
        if branch not in TREE:
            return f"❌ Ветка '{branch}' не найдена."
        current = self.state["branches"][branch]
        if current >= 5:
            return f"✅ Ветка '{branch}' уже максимальна (5/5)."
        cost = (current + 1) * 20
        if self.state["quants"] < cost:
            return f"❌ Нужно {cost} Квантов, есть {self.state['quants']}."
        self.state["quants"] -= cost
        self.state["branches"][branch] += 1
        self.save()
        unlocked = TREE[branch][current]
        return f"✅ {branch} → уровень {current + 1}. Открыто: «{unlocked}»."

    def show_tree(self):
        lines = ["=== Дерево Развития ==="]
        for branch, levels in TREE.items():
            lvl = self.state["branches"][branch]
            bar = "█" * lvl + "░" * (5 - lvl)
            lines.append(f"  {branch:<15} [{bar}] {lvl}/5")
        lines.append(f"\nКвантов: {self.state['quants']}  |  Уровень: {self.state['level']}")
        return "\n".join(lines)


def main():
    put = Put()
    print(put.show_tree())
    print()

    # Демо: начисляем Кванты
    print(put.award(20, "Первый запуск Истока"))
    print(put.award(15, "Аура заговорила"))
    print()

    # Демо: прокачиваем ветку
    print(put.upgrade("ИИ"))
    print(put.upgrade("Ядро"))
    print()

    print(put.show_tree())


if __name__ == "__main__":
    main()
