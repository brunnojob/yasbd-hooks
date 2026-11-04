import unittest

from yasbd import BoundaryDetector
from yasbd_hooks import academic_citations, bracketed_citations, compose_hooks, ocr_artifacts


def context(text):
    return dict(text=text, lang='en', paragraph_index=0,
                boundaries=sorted({0, len(text), *(i + 1 for i, c in enumerate(text) if c in '.!?')}))


class CitationTests(unittest.TestCase):
    def test_flattened_citations(self):
        for marker in ('12', '12,13', '40–46', '40-46', '12,40–46'):
            for punctuation in '.!?':
                with self.subTest(marker=marker, punctuation=punctuation):
                    first = f'This was reported previously{punctuation}{marker}'
                    text = first + ' However, it is debated.'
                    ctx = context(text)
                    boundaries = ctx['boundaries']
                    ocr_artifacts()(ctx)
                    self.assertEqual(boundaries, [0, len(first), len(text)])
                    self.assertIs(ctx['boundaries'], boundaries)
                    ocr_artifacts()(ctx)
                    self.assertEqual(boundaries, [0, len(first), len(text)])
                    self.assertEqual(ctx['text'], text)
                    detector = BoundaryDetector(lang='en', hook=ocr_artifacts())
                    self.assertEqual(list(detector.segment(text)), [first, 'However, it is debated.'])
                    self.assertEqual(''.join(detector.segment(text, preserve_whitespace=True)), text)

    def test_flattened_negative_cases(self):
        for text in ('Value 3.14 However', 'U.S.A.12 However', 'A.12 However',
                     'previously.12 however', 'previously.12However', 'previously.0 However',
                     'previously.12345 However', 'previously.12, However',
                     'previously.12.13 However', 'previously.12\nHowever',
                     'previously.12a However'):
            with self.subTest(text=text):
                ctx = context(text)
                before = ctx['boundaries'][:]
                ocr_artifacts()(ctx)
                self.assertEqual(ctx['boundaries'], before)

    def test_general_journals(self):
        for journal in ('J. Am. Chem. Soc.', 'Proc. Natl. Acad. Sci.', 'Phys. Rev. Lett.'):
            for year in ('1800', '2021', '2099'):
                with self.subTest(journal=journal, year=year):
                    prefix = 'Earlier sentence. '
                    text = prefix + journal.replace(' ', '\t') + ' ' + year + '. Next sentence.'
                    ctx = context(text)
                    start, end = len(prefix), text.index(year)
                    expected = [p for p in ctx['boundaries'] if not start < p <= end]
                    original = ctx['boundaries']
                    academic_citations()(ctx)
                    self.assertEqual(ctx['boundaries'], expected)
                    self.assertIs(ctx['boundaries'], original)
                    academic_citations()(ctx)
                    self.assertEqual(ctx['boundaries'], expected)
                    self.assertEqual(ctx['text'], text)

    def test_general_guards_and_exact_override(self):
        for text in ('Phys. Rev. Lett. Next', 'Phys. Rev. Lett. 1799',
                     'Phys. Rev. Lett. 2100', 'Phys. Rev. Lett. 20210',
                     'phys. rev. lett. 2021', 'Phys. Rev. Lett.\n2021',
                     'Finished. Next sentence. 2024', 'Dr. Smith. 2024'):
            with self.subTest(text=text):
                ctx = context(text)
                before = ctx['boundaries'][:]
                academic_citations()(ctx)
                self.assertEqual(ctx['boundaries'], before)
        text = 'Custom J. 2024. Phys. Rev. Lett. 2021.'
        ctx = context(text)
        academic_citations(journals=iter(['Custom J.']), general=False)(ctx)
        self.assertNotIn(len('Custom J.'), ctx['boundaries'])
        self.assertIn(text.index('Phys.') + len('Phys.'), ctx['boundaries'])
        ctx = context(text)
        before = ctx['boundaries'][:]
        academic_citations(journals=[], general=False)(ctx)
        self.assertEqual(ctx['boundaries'], before)
        for invalid in ('Custom J.',):
            with self.assertRaises(TypeError):
                academic_citations(journals=invalid)
        with self.assertRaises(ValueError):
            academic_citations(journals=[''])

    def test_bracketed_citations_and_composition(self):
        for marker in ('[12]', '[12,13]', '[40–46]', '[40-46]'):
            first = 'This was reported previously.' + marker
            text = first + ' However, it is debated.'
            ctx = context(text)
            original = ctx['boundaries']
            hook = compose_hooks(ocr_artifacts(), bracketed_citations())
            hook(ctx)
            hook(ctx)
            self.assertEqual(original, [0, len(first), len(text)])
            self.assertIs(original, ctx['boundaries'])
            detector = BoundaryDetector(lang='en', hook=hook)
            self.assertEqual(list(detector.segment(text)), [first, 'However, it is debated.'])
            self.assertEqual(''.join(detector.segment(text, preserve_whitespace=True)), text)

    def test_bracketed_guards(self):
        for text in ('See [12] However', 'previously.[x] However',
                     'previously.[12] however', 'previously.[0] However',
                     'previously.[12,] However', 'previously.[12345] However',
                     'previously.[12]\nHowever', 'previously. [12] However'):
            ctx = context(text)
            before = ctx['boundaries'][:]
            bracketed_citations()(ctx)
            self.assertEqual(ctx['boundaries'], before)
        for hook in (ocr_artifacts(), academic_citations(), bracketed_citations()):
            for text in ('', '   ', 'No punctuation'):
                ctx = context(text)
                hook(ctx)
                self.assertEqual(ctx['boundaries'], sorted({0, len(text)}))
