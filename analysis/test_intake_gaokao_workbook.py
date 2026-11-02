"""Synthetic workbooks: catch joins and aggregation that would corrupt labels."""
import tempfile
import unittest
from pathlib import Path

import openpyxl

from intake_gaokao_workbook import parse_workbook, public_summary


class IntakeTests(unittest.TestCase):
    def fixture(self, rows, total):
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = '2020北京西城'
        sheet.append(['题号', '分值', '西城得分率', None, '2020年', '总分', '得分率'])
        for i, row in enumerate(rows):
            sheet.append(list(row) + [None, None, total if i == 0 else None, .5 if i == 0 else None])
        path = Path(self.temp.name) / 'synthetic.xlsx'
        workbook.save(path)
        workbook.close()
        return path

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp.cleanup()

    def test_partial_coverage_keeps_real_zero_and_does_not_fill_gaps(self):
        rows, reports = parse_workbook(self.fixture([(1, 3, 0), ('15_2-1', 2, .5)], 5))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['actual_score_rate'], 0)
        self.assertEqual(rows[1]['question_id'], '15-2-1')
        summary = public_summary(reports)
        self.assertEqual(summary['years'][0]['unobserved_points'], 95)
        self.assertNotIn('declared_total_rate', summary['years'][0])
        self.assertNotIn('actual_score_rate', str(summary))

    def test_identifier_alias_collision_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate normalized'):
            parse_workbook(self.fixture([('15_2', 2, .5), ('15-2', 2, .5)], 4))

    def test_parent_and_child_double_count_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Parent and child'):
            parse_workbook(self.fixture([('15', 4, .5), ('15_1', 2, .5)], 6))

    def test_mismatched_points_and_missing_rate_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Points do not match'):
            parse_workbook(self.fixture([(1, 3, .5)], 4))
        with self.assertRaisesRegex(ValueError, 'score_rate must be numeric'):
            parse_workbook(self.fixture([(1, 3, None)], 3))


if __name__ == '__main__':
    unittest.main()
