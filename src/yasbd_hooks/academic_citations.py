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


def academic_citations(*, journals: Iterable[str] | None = None, general: bool = True) -> Hook:
    """Protect journal abbreviations immediately followed by an 1800–2099 year.

    General matching requires three to six capitalized abbreviations.
    Set general=False for the literal catalogue or exact custom names only.
    This boundary guard is not a citation parser.
    Matching is case-sensitive and horizontal whitespace is flexible.
    """
    if journals is None:
        journals = _DEFAULT_JOURNALS
    if isinstance(journals, str):
        raise TypeError('journals must be an iterable of strings')
    patterns = []
    for journal in journals:
        if not isinstance(journal, str) or not journal.strip():
            raise ValueError('journals must contain nonempty strings')
        literal = r'[ \t]+'.join(re.escape(part) for part in journal.split())
        patterns.append(re.compile(r'(?<!\w)' + literal + r'(?=[ \t]+(?:18|19|20)\d{2}\b)'))

    if general:
        patterns.append(re.compile(
            r'(?<!\w)(?:J\.|[A-Z][A-Za-z]+\.)[ \t]+'
            r'(?:[A-Z][A-Za-z]+\.[ \t]+){1,4}'
            r'[A-Z][A-Za-z]*\.(?=[ \t]+(?:18|19|20)\d{2}\b)'
        ))

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
