"""Router — связывает агентов через шину.
time.answer → speaker.say. Без прямых импортов.
Наука: Mediator Pattern. Агенты не знают друг о друге.
"""
import logging

from aura.kernel.log import event_log
from aura.kernel.payload import get_payload

log = logging.getLogger("aura.router")


class Router:
    def __init__(self, bus):
        self.bus = bus
        self._rules: list = []

    def rule(self, from_topic: str, to_topic: str,
             transform=None, text_key: str = "text"):
        """Правило: from_topic → to_topic с опциональным transform.
        Если transform задан — вызывается с payload, возвращает dict или None.
        """
        async def _handler(event):
            payload = get_payload(event)
            if transform:
                out = transform(payload)
            else:
                text = payload.get(text_key, "")
                out = {"text": text} if text else None
            if out:
                log.info("router: %s → %s", from_topic, to_topic)
                await self.bus.publish(to_topic, out)
                event_log.append("router.forward",
                                 {"from": from_topic, "to": to_topic},
                                 src="router")

        self.bus.subscribe(from_topic, _handler)
        self._rules.append((from_topic, to_topic))
        log.info("rule: %s → %s", from_topic, to_topic)
