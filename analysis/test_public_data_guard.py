"""Synthetic examples verify that public exports cannot contain observed values."""
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location('public_guard', Path(__file__).resolve().parents[1] / 'scripts/check_public_data.py')
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


class PublicGuardTests(unittest.TestCase):
    def test_csv_observed_values_and_blank_targets(self):
        self.assertTrue(guard.inspect('data.csv', b'question_id,score_rate\nfixture,0\n'))
        self.assertFalse(guard.inspect('data.csv', b'question_id,score_rate\nfixture,\n'))
        self.assertFalse(guard.inspect('data.csv', b'question_id,predicted_score_rate\nfixture,0.5\n'))

    def test_nested_json_and_public_coverage(self):
        self.assertTrue(guard.inspect('data.json', b'{"items": [{"actual": 0.5}]}'))
        self.assertFalse(guard.inspect('data.json', b'{"observed_rows": 219, "covered_points": 95}'))

    def test_embedded_outcomes_are_blocked_but_field_contracts_allowed(self):
        self.assertTrue(guard.inspect('page.html', b'<script>const data = [{"actual": 0.5}];</script>'))
        self.assertFalse(guard.inspect('page.html', b'<p>actual_score_rate: fraction in [0, 1]</p>'))


if __name__ == '__main__':
    unittest.main()
