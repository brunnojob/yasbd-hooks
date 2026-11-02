"""Chemical notation callback factory."""


from collections.abc import Iterable
import re

from ._add import _add
from ._types import Hook, HookContext


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
