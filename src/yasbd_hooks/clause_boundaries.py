"""Clause boundaries callback factory."""

import re
from ._add import _add
from ._types import Hook, HookContext

_DEFAULT_CLAUSE_PUNCTUATION = ',;:'
_SUPPORTED_CLAUSE_PUNCTUATION = _DEFAULT_CLAUSE_PUNCTUATION + '—–…；：'

def clause_boundaries(*, punctuation: str = _DEFAULT_CLAUSE_PUNCTUATION) -> Hook:
    """Split after chosen clause punctuation before whitespace; opt-in only.

    The default remains the conservative ASCII set. Broader soft separators
    can be enabled explicitly through ``punctuation``.
    """
    if not punctuation or any(c not in _SUPPORTED_CLAUSE_PUNCTUATION for c in punctuation):
        raise ValueError(
            'punctuation must contain only supported clause separators '
            '(,;:, —, –, …, ； or ：)'
        )
    pattern = re.compile('[' + re.escape(punctuation) + r'](?=\s+\S)')

    def apply(ctx: HookContext) -> None:
        _add(ctx, (m.end() for m in pattern.finditer(ctx['text'])))
    return apply
