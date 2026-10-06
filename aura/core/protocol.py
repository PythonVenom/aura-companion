"""
Протокол взаимодействия агентов.

Каждый агент реализует AgentProtocol и обрабатывает AgentRequest,
возвращая AgentResponse. Это обеспечивает:
- Изоляцию агентов (каждый знает только свой контракт)
- Тестируемость (легко мокать)
- Расширяемость (новый агент = новый класс)
- Кроссплатформенность (агент не знает про ОС)
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field


class AgentStatus(StrEnum):
    """Статус обработки запроса агентом."""

    OK = "ok"
    NOT_HANDLED = "not_handled"
    DENIED = "denied"  # Capability-check: доступ запрещён
    ERROR = "error"
    PARTIAL = "partial"


class AgentRequest(BaseModel):
    """Запрос к агенту."""

    text: str = Field(default="", description="Исходный текст команды от пользователя")
    command: str = Field(default="", description="Нормализованная команда (если есть)")
    args: dict[str, Any] = Field(default_factory=dict, description="Аргументы команды")
    context: dict[str, Any] = Field(default_factory=dict, description="Контекст")
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = {"arbitrary_types_allowed": True}


class AgentResponse(BaseModel):
    """Ответ агента."""

    status: AgentStatus
    text: str = Field(default="", description="Текст ответа для озвучки")
    silent: bool = Field(default=False, description="True = не озвучивать (ADR-048)")
    data: dict[str, Any] = Field(default_factory=dict, description="Структурированные данные")
    error: str | None = Field(default=None, description="Описание ошибки")
    agent_name: str = Field(default="", description="Имя агента")

    model_config = {"arbitrary_types_allowed": True}

    @classmethod
    def ok(cls, text: str, agent_name: str = "", silent: bool = False, **data: Any) -> AgentResponse:
        """Быстрый конструктор успешного ответа. silent=True — не озвучивать (ADR-048)."""
        return cls(status=AgentStatus.OK, text=text, silent=silent, data=data, agent_name=agent_name)

    @classmethod
    def not_handled(cls, agent_name: str = "") -> AgentResponse:
        """Агент не умеет обрабатывать этот запрос."""
        return cls(status=AgentStatus.NOT_HANDLED, agent_name=agent_name)

    @classmethod
    def denied(cls, message: str, agent_name: str = "") -> AgentResponse:
        """Доступ запрещён capability-системой (Saltzer & Schroeder 1975)."""
        return cls(status=AgentStatus.DENIED, text=message,
                   agent_name=agent_name)

    @classmethod
    def error_response(cls, message: str, agent_name: str = "") -> AgentResponse:
        """Ошибка обработки."""
        return cls(status=AgentStatus.ERROR, error=message, agent_name=agent_name)


@runtime_checkable
class AgentProtocol(Protocol):
    """
    Контракт агента.

    Каждый агент:
    - имеет имя (для логирования и отладки)
    - умеет проверять, может ли обработать запрос (can_handle)
    - умеет обрабатывать запрос (handle)
    """

    name: str

    def can_handle(self, request: AgentRequest) -> bool:
        """Может ли агент обработать этот запрос."""
        ...

    async def handle(self, request: AgentRequest) -> AgentResponse:
        """Обработать запрос. Вернуть AgentResponse."""
        ...


class BaseAgent:
    """
    Базовая реализация агента.

    Наследники переопределяют can_handle и handle.
    По умолчанию агент ничего не умеет — это безопасно.

    MODULE_* — метаданные модуля (см. ADR-011):
    - MODULE_NAME — имя модуля для modules.toml.
    - MODULE_DESCRIPTION — краткое описание для GUI.
    - MODULE_REQUIRES — зависимости (другие модули).
    - MODULE_ALWAYS — True если модуль критичен (нельзя выключить).
    """

    name: str = "base"
    MODULE_NAME: str = "base"
    MODULE_DESCRIPTION: str = ""
    MODULE_REQUIRES: tuple = ()
    MODULE_ALWAYS: bool = False

    def __init_subclass__(cls, **kwargs):
        """Авто-заполнение MODULE_NAME из name (ADR-011)."""
        super().__init_subclass__(**kwargs)
        if cls.MODULE_NAME == "base" and cls.name != "base":
            cls.MODULE_NAME = cls.name

    def can_handle(self, request: AgentRequest) -> bool:
        return False

    async def handle(self, request: AgentRequest) -> AgentResponse:
        return AgentResponse.not_handled(agent_name=self.name)


__all__ = [
    "AgentProtocol",
    "AgentRequest",
    "AgentResponse",
    "AgentStatus",
    "BaseAgent",
]
