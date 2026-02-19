"""Sample Python fixture — utility helpers."""


def reverse_string(s: str) -> str:
    """Reverse a string."""
    return s[::-1]


def process(name: str) -> str:
    """Process a name: reverse then greet."""
    from .main import greet

    reversed_name = reverse_string(name)
    return greet(reversed_name)
