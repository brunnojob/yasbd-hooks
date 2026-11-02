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
| `academic_citations()` | Removes boundaries within configured journal abbreviations immediately followed by a year from 1800–2099 | Small literal catalogue, case-sensitive, flexible spaces/tabs. It does not parse arbitrary citations or author lists. |
| `clause_boundaries(punctuation=",;:")` | Adds boundaries after selected punctuation followed by whitespace | Clause segmentation, not grammatical sentence detection. Can split quoted text. |
| `ocr_artifacts()` | Recovers missing spaces, e.g. `Finished.Next` | Conservative ASCII heuristic. May split domains/identifiers; does not rewrite or clean OCR text. |
| `compose_hooks(*hooks)` | Applies callbacks in order | Later callbacks can undo earlier boundary decisions. |

Default scientific tokens (exact case):

- Chemical symbols: `Br`, `Ca`, `Sc`, `Sr`, `Co`, `Fe`, `Cu`, `Zn`, `Mg`, `Mn`, `Ni`, `Cd`, `Pb`, `Hg`, `Al`, `Si`, `Cl`, `Na`, `Li`.
- Analytical notation: `CO`, `LC-MS`, `GC-MS`, `LC-MS/MS`, `GC-MS/MS`, `HPLC`, `UHPLC`, `NMR`, `FTIR`, `UV-Vis`, `XRD`, `XRF`, `ICP-MS`, `ICP-OES`, `HRMS`.

The hook is explicitly opt-in for scientific corpora; it does not infer the domain from surrounding prose. It requires a token boundary, a literal period, whitespace and an ASCII uppercase continuation. Lowercase variants, embedded word fragments, numeric continuations and missing spaces do not trigger a new boundary. Ambiguous chemical symbols can still represent names or titles, so select a custom list for mixed-domain text.

Custom `tokens=` **replaces** the defaults rather than extending them. Existing custom lists, generators and empty lists retain their behavior.

Customize the scientific corpus explicitly:

```python
chemistry = chemical_notation(tokens=["Br", "Ca", "LC-MS", "Eg"])
citations = academic_citations(journals=["J. Am. Chem. Soc.", "Custom J."])
```

Empty token/journal collections create no-op callbacks. Add validated journal names and real regression examples rather than broad abbreviation patterns. These initial heuristics do not claim universal scientific-text accuracy.

## Development

```sh
python -m pip install -e .
python -m unittest discover -s tests -v
python -m pip wheel --no-deps . -w dist
```

Tests cover case sensitivity, custom journal names, offsets, repeated application, composition order, empty text, and real YASBD segmentation for both examples from issue #412. GitHub Actions runs the suite on Python 3.10–3.14.

## Contributing

Bug reports should include input, expected segments, actual segments, Python/YASBD versions and the configured hooks. Include a regression test with fixes. Run the test suite before opening a pull request. Additional scientific examples and journal abbreviations are welcome.

## Credits

Maintained by [brunnojob](https://github.com/brunnojob) · [brunnodev.store](https://brunnodev.store). YASBD is maintained by [speedyk-005](https://github.com/speedyk-005); this separate companion package implements the hook ecosystem proposed in issue #412. MIT license applies to this package; YASBD retains its own license.
