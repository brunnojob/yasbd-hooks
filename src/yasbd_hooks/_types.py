"""Shared callback types compatible with the YASBD hook context."""
from collections.abc import Callable
from typing import TypedDict


class HookContext(TypedDict):
    text: str
    lang: str
    boundaries: list[int]
    paragraph_index: int


Hook = Callable[[HookContext], None]
