from abc import ABC, abstractmethod


class AIBackend(ABC):
    """Common interface every backend must implement."""

    @abstractmethod
    def send(self, prompt: str) -> str:
        """Send a prompt and return the AI's response."""

    @abstractmethod
    def close(self) -> None:
        """Release any resources (process, connection, file handles)."""
