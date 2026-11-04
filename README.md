# yasbd-hooks

Reusable, opt-in callbacks for [YASBD](https://github.com/speedyk-005/yasbd-lib). Created from the separate-library proposal in [issue #412](https://github.com/speedyk-005/yasbd-lib/issues/412#issuecomment-6545826112).

## Install

Python 3.10+ and YASBD 1.0.4+ are required. This project is not published on PyPI yet.

```sh
python -m pip install "git+https://github.com/brunnojob/yasbd-hooks.git"
```

## Scientific text

```python
from yasbd import BoundaryDetector
from yasbd_hooks import academic_citations, chemical_notation, compose_hooks

scientific = compose_hooks(chemical_notation(), academic_citations())
detector = BoundaryDetector(lang="en", hook=scientific)

assert list(detector.segment(
    "The film was doped with Br. Selectivity was high."
)) == ["The film was doped with Br.", "Selectivity was high."]

reference = "Smith, A.; Jones, B. J. Am. Chem. Soc. 2020, 142, 1234-1240."
assert list(detector.segment(reference)) == [reference]
```

Hooks mutate paragraph-relative `ctx["boundaries"]` in place. Text, whitespace and character offsets are preserved; paragraph start and end remain intact. The general English rules are unchanged. `compose_hooks` runs callbacks in the supplied order, propagates errors, and accepts callbacks that reassign the boundary list.

| Factory | Behavior | Scope and limitations |
| --- | --- | --- |
| `chemical_notation()` | Restores a boundary after the scientific tokens listed below, before whitespace plus ASCII uppercase prose | Exact case. This assumes these tokens end sentences in your corpus; `Br. Smith` remains ambiguous. Lowercase `ca.` is untouched. |
| `academic_citations()` | Removes boundaries within journal abbreviations immediately followed by a year from 1800–2099 | Literal catalogue plus conservative general matching; `general=False` selects exact matching only. Case-sensitive, flexible spaces/tabs; not a bibliography parser. |
| `clause_boundaries()` | Adds boundaries after selected punctuation followed by whitespace | Clause segmentation, not grammatical sentence detection. Defaults to `,;:`; broader soft separators must be opted into explicitly. Can split quoted text. |
| `ocr_artifacts()` | Recovers missing spaces and flattened numeric citation endings, e.g. `Finished.Next` and `previously.12,13 However` | Conservative ASCII heuristic. May split domains/identifiers; does not rewrite or clean OCR text. |
| `bracketed_citations()` | Keeps attached numeric citations with the preceding sentence, e.g. `previously.[12,13] However` | Requires sentence punctuation, positive numeric references and a capitalized continuation. No text cleanup. |
| `compose_hooks(*hooks)` | Applies callbacks in order | Later callbacks can undo earlier boundary decisions. |

Default scientific tokens (exact case):

- Chemical symbols: `Br`, `Ca`, `Sc`, `Sr`, `Co`, `Fe`, `Cu`, `Zn`, `Mg`, `Mn`, `Ni`, `Cd`, `Pb`, `Hg`, `Al`, `Si`, `Cl`, `Na`, `Li`.
- Analytical notation: `CO`, `LC-MS`, `GC-MS`, `LC-MS/MS`, `GC-MS/MS`, `HPLC`, `UHPLC`, `NMR`, `FTIR`, `UV-Vis`, `XRD`, `XRF`, `ICP-MS`, `ICP-OES`, `HRMS`.

The hook is explicitly opt-in for scientific corpora; it does not infer the domain from surrounding prose. It requires a token boundary, a literal period, whitespace and an ASCII uppercase continuation. Lowercase variants, embedded word fragments, numeric continuations and missing spaces do not trigger a new boundary. Ambiguous chemical symbols can still represent names or titles, so select a custom list for mixed-domain text.

Custom `tokens=` **replaces** the defaults rather than extending them. Existing custom lists, generators and empty lists retain their behavior.

Customize the scientific corpus explicitly:

```python
chemistry = chemical_notation(tokens=["Br", "Ca", "LC-MS", "Eg"])
citations = academic_citations(journals=["J. Am. Chem. Soc.", "Custom J."], general=False)
```

Empty token collections create no-op callbacks. For journals, use `journals=[], general=False` for a no-op. These heuristics do not claim universal scientific-text accuracy.

For conservative clause splitting, use the default ASCII punctuation:

```python
clauses = clause_boundaries()
```

For scientific, OCR, or multilingual text, opt into the additional soft
separators explicitly:

```python
from yasbd_hooks import clause_boundaries

broader_clauses = clause_boundaries(punctuation="—–…；：")
```

The supported extended set includes em dashes, en dashes, ellipses, and the
full-width semicolon and colon. Sentence-final punctuation (`.`, `?`, `!`,
`¿`, and `¡`) is intentionally not accepted.

## Citation boundary guards

`academic_citations()` now recognizes common journal-like patterns such as
`J. Am. Chem. Soc. 2020`, `Proc. Natl. Acad. Sci. 2024`, and
`Phys. Rev. Lett. 2021`. General matching requires three to six capitalized,
period-terminated tokens; the first must be `J.` or a multi-letter abbreviation,
and intermediate tokens must have multiple letters. Only horizontal whitespace
and a following year from 1800–2099 are accepted. Boundaries outside the matched
journal span, including author initials, are preserved.

```python
citations = academic_citations()  # default catalogue plus general matching
exact = academic_citations(journals=["Custom J."], general=False)
catalogue_only = academic_citations(general=False)
```

A supplied `journals=` collection replaces the literal default catalogue.
General matching remains enabled unless `general=False`; set it to false for
strict custom-name matching. Empty collections and generators are supported.
Journal-shaped prose followed by a year can remain ambiguous; use exact mode
for mixed-domain text. This hook does not parse arbitrary bibliography metadata.

`ocr_artifacts()` also restores boundaries after flattened numeric citations.
`bracketed_citations()` is a separate, single-purpose hook for attached numeric
citations in square brackets. Both retain citations with the preceding sentence,
remove premature boundaries inside the marker, and preserve the original text.

```python
from yasbd import BoundaryDetector
from yasbd_hooks import bracketed_citations, compose_hooks, ocr_artifacts

hook = compose_hooks(ocr_artifacts(), bracketed_citations())
detector = BoundaryDetector(lang="en", hook=hook)
assert list(detector.segment("Reported previously.12,13 However, it is debated.")) == [
    "Reported previously.12,13", "However, it is debated."
]
assert list(detector.segment("Reported previously.[40–46] However, it is debated.")) == [
    "Reported previously.[40–46]", "However, it is debated."
]
```

Citation markers accept positive integers of one to four digits, comma lists,
and hyphen/en-dash ranges. A lowercase-ending word of at least two letters must
precede `.`, `!`, or `?`; horizontal whitespace and an ASCII capitalized word
must follow the marker. Decimals, initials, acronyms, malformed lists, lowercase
continuations and cross-line continuations are left alone. This intentionally
excludes spaced brackets, superscript Unicode digits, and full citation parsing.
All hooks remain opt-in and work with `compose_hooks(...)`.

## Development

```sh
python -m pip install -e .
python -m unittest discover -s tests -v
python -m pip wheel --no-deps . -w dist
```

Tests cover case sensitivity, custom journal names, offsets, repeated application, composition order, empty text, and real YASBD segmentation for both examples from issue #412. GitHub Actions runs the suite on Python 3.10–3.14.

## Package structure

Each hook factory has a dedicated module under `src/yasbd_hooks/`:

- `chemical_notation.py`: scientific tokens and their matching defaults.
- `academic_citations.py`: journal matching and its default catalogue.
- `clause_boundaries.py`: clause splitting and punctuation defaults.
- `ocr_artifacts.py`: missing-space and flattened citation boundary recovery.
- `bracketed_citations.py`: attached bracketed numeric citation boundaries.
- `compose_hooks.py`: callback composition.
- `_types.py`: shared `Hook` and `HookContext` types.
- `_add.py`: shared in-place boundary insertion.
- `__init__.py`: public exports, preserving existing imports.

Continue using `from yasbd_hooks import chemical_notation` (and the other
public names) without changes. Callback closures stay with their factories;
private helpers and types are internal implementation details.

## Contributing

Bug reports should include input, expected segments, actual segments, Python/YASBD versions and the configured hooks. Include a regression test with fixes. Run the test suite before opening a pull request. Additional scientific examples and journal abbreviations are welcome.

[Issue #6](https://github.com/brunnojob/yasbd-hooks/issues/6) is the ongoing
hook backlog and remains open. Propose small, single-purpose, opt-in hooks there
with input, expected segments, scope limits, and positive/negative regression
cases. The citation hooks above are initial additions; future ideas include
structured-text boundary restorers and domain-specific scientific notation guards.

## Credits

Maintained by [brunnojob](https://github.com/brunnojob) · [brunnodev.store](https://brunnodev.store). YASBD is maintained by [speedyk-005](https://github.com/speedyk-005); this separate companion package implements the hook ecosystem proposed in issue #412. MIT license applies to this package; YASBD retains its own license.
