"""Core data structures for the markdown parser."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol
from abc import ABC, abstractmethod
from enum import Enum


class ErrorLevel(Enum):
    """Error severity levels."""
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ParseError:
    """Represents a parsing error with context."""
    message: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    level: ErrorLevel = ErrorLevel.ERROR
    context: Optional[str] = None

    def __str__(self) -> str:
        """Format error message for display."""
        if self.line_number is not None:
            location = f"Line {self.line_number}"
            if self.column_number is not None:
                location += f", Column {self.column_number}"
            return f"{self.level.value.title()}: {self.message} ({location})"
        return f"{self.level.value.title()}: {self.message}"


@dataclass
class ParseResult:
    """Result of parsing markdown text."""
    ast: Any  # Token list from markdown-it-py or Document from mistletoe
    errors: List[ParseError]
    warnings: List[ParseError]
    metadata: Dict[str, Any]
    source_text: str

    @property
    def has_errors(self) -> bool:
        """Check if parsing resulted in errors."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if parsing resulted in warnings."""
        return len(self.warnings) > 0

    def add_error(self, message: str, line_number: Optional[int] = None,
                  level: ErrorLevel = ErrorLevel.ERROR) -> None:
        """Add an error to the result."""
        error = ParseError(message=message, line_number=line_number, level=level)
        if level == ErrorLevel.WARNING:
            self.warnings.append(error)
        else:
            self.errors.append(error)


class MarkdownParser(Protocol):
    """Protocol for markdown parsers."""

    def parse(self, text: str) -> ParseResult:
        """Parse markdown text and return result with AST and errors."""
        ...

    def get_supported_features(self) -> List[str]:
        """Return list of supported markdown features."""
        ...


class Renderer(ABC):
    """Abstract base class for renderers."""

    @abstractmethod
    def render(self, ast: Any, options: Optional[Dict[str, Any]] = None) -> str:
        """Render AST to target format."""
        pass

    @abstractmethod
    def get_output_format(self) -> str:
        """Return the output format name."""
        pass
