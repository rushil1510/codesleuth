"""Sample Python fixture — main module."""


def greet(name: str) -> str:
    """Return a greeting string."""
    message = format_greeting(name)
    return message


def format_greeting(name: str) -> str:
    """Format name into a greeting."""
    return f"Hello, {name}!"


class Calculator:
    """A simple calculator."""

    def add(self, a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    def add_and_greet(self, a: int, b: int, name: str) -> str:
        """Add two numbers then greet someone."""
        result = self.add(a, b)
        greeting = greet(name)
        return f"{greeting} The sum is {result}."
