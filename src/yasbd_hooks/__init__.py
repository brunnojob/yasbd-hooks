"""Opt-in, paragraph-local post-processing hooks for YASBD."""
from collections.abc import Callable, Iterable
import re
from typing import TypedDict


class HookContext(TypedDict):
    text: str
    lang: str
    boundaries: list[int]
    paragraph_index: int


Hook = Callable[[HookContext], None]
__all__ = ['chemical_notation', 'academic_citations', 'clause_boundaries',
           'ocr_artifacts', 'compose_hooks', 'HookContext', 'Hook']


def compose_hooks(*hooks: Hook) -> Hook:
    """Run callbacks in order on the same context; exceptions propagate."""
    if not all(callable(hook) for hook in hooks):
        raise TypeError('Every hook must be callable')

    def apply(ctx: HookContext) -> None:
        for hook in hooks:
            hook(ctx)
    return apply


def _add(ctx: HookContext, offsets: Iterable[int]) -> None:
    ctx['boundaries'][:] = sorted(set(ctx['boundaries']).union(offsets))


# Immutable groups keep additions reviewable without changing custom token lists.
_CHEMICAL_SYMBOLS = (
    'Br', 'Ca', 'Sc', 'Sr', 'Co', 'Fe', 'Cu', 'Zn', 'Mg', 'Mn', 'Ni',
    'Cd', 'Pb', 'Hg', 'Al', 'Si', 'Cl', 'Na', 'Li',
)
_ANALYTICAL_TOKENS = (
    'CO', 'LC-MS', 'GC-MS', 'LC-MS/MS', 'GC-MS/MS', 'HPLC', 'UHPLC',
    'NMR', 'FTIR', 'UV-Vis', 'XRD', 'XRF', 'ICP-MS', 'ICP-OES', 'HRMS',
)
_DEFAULT_SCIENTIFIC_TOKENS = _CHEMICAL_SYMBOLS + _ANALYTICAL_TOKENS


def chemical_notation(*, tokens: Iterable[str] = _DEFAULT_SCIENTIFIC_TOKENS) -> Hook:
    """Restore ends after exact-case scientific tokens followed by uppercase prose.

    Defaults include chemical symbols and analytical techniques. Explicit
    tokens replace the defaults entirely; an empty iterable disables matching.
    Matching remains case-sensitive and requires a full token, a period,
    whitespace and an ASCII uppercase continuation.

    This deliberately resolves ambiguity in favor of a sentence boundary. It
    cannot distinguish an element from a title such as 'Br. Smith'. Enable only
    for scientific corpora where that tradeoff is appropriate.
    """
    if isinstance(tokens, str):
        raise TypeError('tokens must be an iterable of strings, not a string')
    values = tuple(tokens)
    if any(not isinstance(value, str) or not value for value in values):
        raise ValueError('tokens must contain nonempty strings')
    pattern = re.compile(r'(?<!\w)(?:' + '|'.join(re.escape(v) for v in sorted(values, key=len, reverse=True)) + r')\.(?=\s+[A-Z])') if values else None

    def apply(ctx: HookContext) -> None:
        if pattern is not None:
            _add(ctx, (m.end() for m in pattern.finditer(ctx['text'])))
    return apply


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


_DEFAULT_CLAUSE_PUNCTUATION = ',;:'


def clause_boundaries(*, punctuation: str = _DEFAULT_CLAUSE_PUNCTUATION) -> Hook:
    """Split after chosen clause punctuation before whitespace; opt-in only."""
    if not punctuation or any(c not in _DEFAULT_CLAUSE_PUNCTUATION for c in punctuation):
        raise ValueError('punctuation must contain only commas, semicolons or colons')
    pattern = re.compile('[' + re.escape(punctuation) + r'](?=\s+\S)')

    def apply(ctx: HookContext) -> None:
        _add(ctx, (m.end() for m in pattern.finditer(ctx['text'])))
    return apply


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
