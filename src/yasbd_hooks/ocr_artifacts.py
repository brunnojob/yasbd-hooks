"""Ocr artifacts callback factory."""


import re

from ._add import _add
from ._types import Hook, HookContext


def ocr_artifacts() -> Hook:
    """Recover missing spaces after .!? before ASCII uppercase prose.

    Restricts period matches to lowercase words of at least two letters;
    decimals, initials and all-uppercase acronyms are left alone. This heuristic
    may split domains and identifiers, so it is never enabled automatically.
    Flattened citations such as previously.12,13 However are kept with
    the preceding sentence. Markers require 1–4 digit positive integers,
    optional comma/range separators, and a capitalized continuation.
    """
    pattern = re.compile(r'(?<!\w)[A-Za-z][a-z]+[.!?](?=[A-Z][a-z])')

    citation_pattern = re.compile(
        r'(?<!\w)[A-Za-z][a-z]+[.!?]'
        r'(?P<markers>[1-9][0-9]{0,3}(?:[,–-][1-9][0-9]{0,3})*)'
        r'(?=[ \t]+[A-Z][a-z])'
    )

    def apply(ctx: HookContext) -> None:
        text = ctx['text']
        matches = list(citation_pattern.finditer(text))
        ctx['boundaries'][:] = [
            pos for pos in ctx['boundaries']
            if pos in (0, len(text)) or not any(
                m.start('markers') <= pos < m.end() for m in matches
            )
        ]
        _add(ctx, (m.end() for m in matches))
        _add(ctx, (m.end() for m in pattern.finditer(text)))
    return apply
