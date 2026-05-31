"""Base database client interface."""

from abc import ABC, abstractmethod


class DatabaseClient(ABC):
    @abstractmethod
    def execute(self, sql: str) -> list[dict]:
        ...
