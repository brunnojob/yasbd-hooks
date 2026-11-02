"""Ocr artifacts callback factory."""


import re

from ._add import _add
from ._types import Hook, HookContext


def ocr_artifacts() -> Hook:
    """Recover missing spaces after .!? before ASCII uppercase prose.

    Restricts period matches to lowercase words of at least two letters;
    decimals, initials and all-uppercase acronyms are left alone. This heuristic
    may split domains and identifiers, so it is never enabled automatically.
    """
    pattern = re.compile(r'(?<!\w)[A-Za-z][a-z]+[.!?](?=[A-Z][a-z])')

    def apply(ctx: HookContext) -> None:
        _add(ctx, (m.end() for m in pattern.finditer(ctx['text'])))
    return apply
