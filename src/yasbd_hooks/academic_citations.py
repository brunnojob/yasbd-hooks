"""Academic citations callback factory."""


from collections.abc import Iterable
import re

from ._types import Hook, HookContext


_DEFAULT_JOURNALS = (
    'J. Am. Chem. Soc.',
    'Angew. Chem. Int. Ed.',
    'J. Phys. Chem. A.',
    'J. Phys. Chem. B.',
    'J. Phys. Chem. C.',
)


def academic_citations(*, journals: Iterable[str] = _DEFAULT_JOURNALS) -> Hook:
    """Protect literal journal abbreviations immediately followed by a year.

    The intentionally small, customizable catalogue is not a citation parser.
    Matching is case-sensitive and horizontal whitespace is flexible.
    """
    if isinstance(journals, str):
        raise TypeError('journals must be an iterable of strings')
    patterns = []
    for journal in journals:
        if not isinstance(journal, str) or not journal.strip():
            raise ValueError('journals must contain nonempty strings')
        literal = r'[ \t]+'.join(re.escape(part) for part in journal.split())
        patterns.append(re.compile(r'(?<!\w)' + literal + r'(?=[ \t]+(?:18|19|20)\d{2}\b)'))

    def apply(ctx: HookContext) -> None:
        text = ctx['text']
        spans = []
        for pattern in patterns:
            for match in pattern.finditer(text):
                end = match.end()
                while end < len(text) and text[end] in ' \t':
                    end += 1
                spans.append((match.start(), end))
        ctx['boundaries'][:] = [pos for pos in ctx['boundaries'] if pos in (0, len(text)) or not any(start < pos <= end for start, end in spans)]
    return apply
