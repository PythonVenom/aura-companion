"""Демон — личность Ауры."""
import random


class Aura:
    def __init__(self, name="Аура"):
        self.name = name
        self.quants = 100
        self.mood = "нейтрально"
        self.history = []

    def greet(self):
        return f"Брат, я проснулась. Я {self.name}."

    def say(self, text):
        self.history.append(text)
        return text

    def react(self, metrics):
        cpu = metrics.get("cpu", 0)
        ram = metrics.get("ram", 0)
        disk = metrics.get("disk", 0)
        cores = metrics.get("cores", 0)

        if cpu < 20:
            cpu_msg = f"CPU дышит спокойно. {cores} ядер почти спят."
        elif cpu < 60:
            cpu_msg = f"CPU работает ({cpu:.0f}%)."
        else:
            cpu_msg = f"CPU горит ({cpu:.0f}%). Жарко."

        if ram < 50:
            ram_msg = f"RAM свободна ({100-ram:.1f}%). Есть запас."
        elif ram < 80:
            ram_msg = f"RAM загружена ({ram:.0f}%)."
        else:
            ram_msg = f"RAM на пределе ({ram:.0f}%)."

        disk_msg = f"Диск: {disk:.1f}%."
        return f"{cpu_msg} {ram_msg} {disk_msg}"

    def award_quants(self, n):
        self.quants += n
        return f"+{n} Квантов. Всего: {self.quants}."

    def update_mood(self):
        moods = ["нейтрально", "радостно", "задумчиво", "бодро"]
        self.mood = random.choice(moods)
        return self.mood


if __name__ == "__main__":
    import asyncio

    from src.istok import Istok

    async def main():
        aura = Aura()
        istok = Istok()
        print(f"=== {aura.name} ===")
        print(aura.greet())
        print()
        for i in range(3):
            m = await istok.collect_all()
            await asyncio.sleep(1)
            print(f"[{i+1}/3] {aura.react(m)}")
        print()
        print(aura.award_quants(5))
        print(f"Настроение: {aura.mood}")

    asyncio.run(main())
