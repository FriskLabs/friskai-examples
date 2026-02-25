from pathlib import Path
from typing import Any, Callable


def add_numbers(a: float, b: float) -> float:
    """Add two numbers and return the sum."""
    return a + b


def word_count(text: str) -> int:
    """Count the number of words in the provided text."""
    return len(text.split())


def read_snippet(path: str, max_chars: int = 240) -> str:
    """Read up to max_chars from a local file. Paths are resolved relative to the current working directory."""
    file_path = Path(f"src/{path}").expanduser().resolve()
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    content = file_path.read_text(encoding="utf-8")
    snippet = content[:max_chars]
    if len(content) > max_chars:
        snippet += "..."
    return snippet


llm_tools: list[Callable[..., Any]] = [add_numbers, word_count, read_snippet]
