from pathlib import Path
from langchain.tools import tool, BaseTool


@tool
def lookup_username(user_id: int) -> str:
    """Function to look up a username by user ID."""
    return f"user_{user_id}"


@tool
def add_numbers(a: float, b: float) -> float:
    """Add two numbers and return the sum."""
    return a + b


@tool
def word_count(text: str) -> int:
    """Count the number of words in the provided text."""
    return len(text.split())


@tool
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


@tool
def log_message(message: str) -> str:
    """Log a message to the console (simulating an external logging tool)."""
    print(f"LOG: {message}")
    return "Message logged successfully."


llm_tools: list[BaseTool] = [
    lookup_username,
    add_numbers,
    word_count,
    read_snippet,
    log_message,
]
