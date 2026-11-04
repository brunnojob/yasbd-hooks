"""Boundary recovery for bracketed numeric citations."""
import re

from ._add import _add
from ._types import Hook, HookContext


def bracketed_citations() -> Hook:
    """Keep attached [12,13] citations with the preceding sentence.

    Requires a lowercase-ending word, sentence punctuation, attached brackets,
    positive 1–4 digit references and horizontal space before uppercase prose.
    Text and whitespace are never rewritten.
    """
    pattern = re.compile(
        r'(?<!\w)[A-Za-z][a-z]+[.!?]'
        r'(?P<markers>\[[1-9][0-9]{0,3}(?:[,–-][1-9][0-9]{0,3})*\])'
        r'(?=[ \t]+[A-Z][a-z])'
    )

    def apply(ctx: HookContext) -> None:
        text = ctx['text']
        matches = list(pattern.finditer(text))
        ctx['boundaries'][:] = [
            pos for pos in ctx['boundaries']
            if pos in (0, len(text)) or not any(
                m.start('markers') <= pos < m.end() for m in matches
            )
        ]
        _add(ctx, (m.end() for m in matches))
    return apply
