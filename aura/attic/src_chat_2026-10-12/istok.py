"""Исток — сбор метрик системы."""
import asyncio

import psutil


class Istok:
    def __init__(self):
        pass

    async def collect_all(self):
        asyncio.get_event_loop()
        cpu = psutil.cpu_percent(interval=0.2, percpu=False)
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent
        return {
            "cpu": cpu,
            "ram": ram,
            "disk": disk,
            "cores": psutil.cpu_count(),
        }
