from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("aura-companion")
except PackageNotFoundError:
    __version__ = "1.0.0-rc1"

"""
Аура — семейный ИИ-компаньон.

Модульная архитектура:
- core — протокол, реестр, оркестратор
- agents — агенты (time, power, ...)
- platform — платформенные адаптеры
- memory — память (RAG, журнал)
"""


