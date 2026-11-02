"""Clause boundaries callback factory."""


import re

from ._add import _add
from ._types import Hook, HookContext


_DEFAULT_CLAUSE_PUNCTUATION = ',;:'


def clause_boundaries(*, punctuation: str = _DEFAULT_CLAUSE_PUNCTUATION) -> Hook:
    """Split after chosen clause punctuation before whitespace; opt-in only."""
    if not punctuation or any(c not in _DEFAULT_CLAUSE_PUNCTUATION for c in punctuation):
        raise ValueError('punctuation must contain only commas, semicolons or colons')
    pattern = re.compile('[' + re.escape(punctuation) + r'](?=\s+\S)')

    def apply(ctx: HookContext) -> None:
        _add(ctx, (m.end() for m in pattern.finditer(ctx['text'])))
    return apply
