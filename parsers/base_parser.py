from abc import ABC, abstractmethod


# Base parser interface
class BaseParser(ABC):
    @abstractmethod
    def parse(self, filepath: str) -> str:
        """Abstract method to parse file content."""
        pass
