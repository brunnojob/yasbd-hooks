import unittest
from yasbd_hooks import academic_citations, chemical_notation, clause_boundaries, compose_hooks, ocr_artifacts


def context(text, boundaries=None):
    return dict(text=text, lang='en', paragraph_index=0,
                boundaries=[0, len(text)] if boundaries is None else boundaries)


class HookTests(unittest.TestCase):
    def test_chemical_case_and_offsets(self):
        for token in ('Br', 'Ca', 'Sc', 'Sr', 'Co', 'CO', 'LC-MS'):
            text = f'The film was doped with {token}. Selectivity was high.'
            ctx = context(text)
            original = ctx['boundaries']
            chemical_notation()(ctx)
            self.assertIn(text.index('. ') + 1, ctx['boundaries'])
            self.assertIs(original, ctx['boundaries'])
        for text in ('ca. five samples', 'ca. Five samples', 'xBr. Selectivity', 'Br. lower case'):
            ctx = context(text)
            chemical_notation()(ctx)
            self.assertEqual(ctx['boundaries'], [0, len(text)])

    def test_expanded_scientific_defaults(self):
        tokens = (
            'Fe', 'Cu', 'Zn', 'Mg', 'Mn', 'Ni', 'Cd', 'Pb', 'Hg', 'Al',
            'Si', 'Cl', 'Na', 'Li', 'GC-MS', 'LC-MS/MS', 'GC-MS/MS',
            'HPLC', 'UHPLC', 'NMR', 'FTIR', 'UV-Vis', 'XRD', 'XRF',
            'ICP-MS', 'ICP-OES', 'HRMS',
        )
        hook = chemical_notation()
        for token in tokens:
            with self.subTest(token=token):
                text = f'The sample was analyzed using {token}. Results followed.'
                ctx = context(text)
                boundaries = ctx['boundaries']
                hook(ctx)
                self.assertEqual(boundaries, [0, text.index('. ') + 1, len(text)])
                self.assertIs(boundaries, ctx['boundaries'])
                self.assertEqual(ctx['text'], text)
                hook(ctx)
                self.assertEqual(boundaries, [0, text.index('. ') + 1, len(text)])

    def test_scientific_context_guards(self):
        hook = chemical_notation()
        for text in (
            'Measured by nmr. Results followed.',
            'Measured by uv-vis. Results followed.',
            'Measured by xHPLC. Results followed.',
            'Measured by ΔNMR. Results followed.',
            'Measured by NMRx. Results followed.',
            'Measured by HPLC.Results followed.',
            'Measured by HPLC. results followed.',
            'Measured by HPLC. 2026 results followed.',
            'Measured by HPLC, Results followed.',
        ):
            with self.subTest(text=text):
                ctx = context(text)
                hook(ctx)
                self.assertEqual(ctx['boundaries'], [0, len(text)])

    def test_custom_tokens_replace_expanded_defaults(self):
        for tokens in (['Only'], ('Only',), iter(['Only'])):
            ctx = context('Only. Results from NMR. Results from Br. Results.')
            chemical_notation(tokens=tokens)(ctx)
            self.assertEqual(ctx['boundaries'], [0, 5, len(ctx['text'])])
        for tokens in ([], (), iter(())):
            ctx = context('NMR. Results from Br. Results.')
            chemical_notation(tokens=tokens)(ctx)
            self.assertEqual(ctx['boundaries'], [0, len(ctx['text'])])
        ctx = context('X+. Results. nmr. Results.')
        chemical_notation(tokens=['X+', 'nmr'])(ctx)
        self.assertEqual(ctx['boundaries'], [0, 3, 17, len(ctx['text'])])

    def test_journal_year(self):
        text = 'Smith, A.; Jones, B. J. Am. Chem. Soc. 2020, 142, 1234-1240.'
        ctx = context(text, [0] + [i+1 for i, c in enumerate(text) if c == '.'])
        academic_citations()(ctx)
        self.assertEqual(ctx['boundaries'], [0, 9, 20, len(text)])
        text = 'See J. Am. Chem. Soc. Next sentence.'
        ctx = context(text, [0, 20, len(text)])
        academic_citations()(ctx)
        self.assertEqual(ctx['boundaries'], [0, 20, len(text)])

    def test_custom_journal_and_whitespace(self):
        text = 'Custom\tJ. 2024, 1, 2.'
        ctx = context(text, [0, 9, 10, len(text)])
        academic_citations(journals=['Custom J.'])(ctx)
        self.assertEqual(ctx['boundaries'], [0, len(text)])

    def test_compose_order_and_reassignment(self):
        ctx = context('Alpha, beta: gamma.')
        compose_hooks(lambda c: c.update(boundaries=[0, len(c['text'])]), clause_boundaries())(ctx)
        self.assertEqual(ctx['boundaries'], [0, 6, 12, 19])
        compose_hooks()(ctx)
        with self.assertRaises(TypeError):
            compose_hooks(None)

    def test_ocr(self):
        ctx = context('Finished.Next step!Another one. 3.14 U.S.A.')
        ocr_artifacts()(ctx)
        self.assertEqual(ctx['boundaries'], [0, 9, 19, len(ctx['text'])])

    def test_empty_and_repeat(self):
        hook = compose_hooks(chemical_notation(), academic_citations(), clause_boundaries(), ocr_artifacts())
        for text in ('', '   ', 'No punctuation', 'Δ Br. Selectivity improved.'):
            ctx = context(text)
            hook(ctx)
            result = ctx['boundaries'][:]
            hook(ctx)
            self.assertEqual(ctx['boundaries'], result)
            self.assertEqual(ctx['text'], text)
            self.assertTrue(all(0 <= p <= len(text) for p in result))


class IntegrationTests(unittest.TestCase):
    def test_expanded_scientific_segmentation(self):
        from yasbd import BoundaryDetector
        detector = BoundaryDetector(lang='en', hook=chemical_notation())
        for token in ('Fe', 'NMR', 'HPLC', 'LC-MS/MS', 'ICP-OES', 'UV-Vis'):
            with self.subTest(token=token):
                first = f'The sample was analyzed using {token}.'
                text = first + ' Results followed.'
                self.assertEqual(list(detector.segment(text)), [first, 'Results followed.'])
                self.assertEqual(''.join(detector.segment(text, preserve_whitespace=True)), text)

    def test_issue_412(self):
        from yasbd import BoundaryDetector
        text = 'The film was doped with Br. Selectivity was high.'
        detector = BoundaryDetector(lang='en', hook=chemical_notation())
        self.assertEqual(list(detector.segment(text)), ['The film was doped with Br.', 'Selectivity was high.'])
        citation = 'Smith, A.; Jones, B. J. Am. Chem. Soc. 2020, 142, 1234-1240.'
        detector = BoundaryDetector(lang='en', hook=academic_citations())
        self.assertEqual(list(detector.segment(citation)), [citation])
        combined = BoundaryDetector(lang='en', hook=compose_hooks(chemical_notation(), academic_citations()))
        self.assertEqual(list(combined.segment(text + '\n\n' + citation)), ['The film was doped with Br.', 'Selectivity was high.', citation])
        self.assertEqual(''.join(combined.segment(text, preserve_whitespace=True)), text)


if __name__ == '__main__':
    unittest.main()
