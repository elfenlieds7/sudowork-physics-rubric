"""Validate the teacher's year-by-year workbook and keep all rates local.

The public summary contains coverage counts only. It never contains rates,
question identifiers, workbook rows, or a path to the private source file.
"""
import argparse
import csv
import hashlib
import json
import math
import re
import shutil
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent


def normalize_question_id(value):
    if isinstance(value, bool):
        raise ValueError('Boolean question identifier')
    if isinstance(value, (int, float)):
        if not math.isfinite(value) or int(value) != value:
            raise ValueError('Question identifier is not an integer')
        value = str(int(value))
    value = str(value).strip()
    if not re.fullmatch(r'\d+(?:[_-]\d+)*', value):
        raise ValueError(f'Unsupported question identifier: {value}')
    return '-'.join(str(int(part)) for part in re.split('[_-]', value))


def number(value, name, allow_zero=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{name} must be numeric')
    if not math.isfinite(value) or value < 0 or (value == 0 and not allow_zero):
        raise ValueError(f'{name} is outside its valid range')
    return float(value)


def parse_workbook(path):
    workbook = openpyxl.load_workbook(path, data_only=True, read_only=True)
    normalized = []
    reports = []
    years = set()
    try:
        for sheet in workbook:
            match = re.fullmatch(r'(20\d{2})北京西城', sheet.title)
            if not match:
                raise ValueError(f'Unrecognized sheet: {sheet.title}')
            year = int(match[1])
            if year in years:
                raise ValueError(f'Duplicate year: {year}')
            years.add(year)
            values = list(sheet.values)
            if len(values) < 2 or len(values[0]) < 7:
                raise ValueError(f'Incomplete sheet: {sheet.title}')
            headers = values[0]
            if headers[0] not in ('题号', '题目') or headers[1] not in ('分值', '满分值') or headers[2] not in ('得分率', '西城得分率'):
                raise ValueError(f'Unexpected column headings: {sheet.title}')
            rows = []
            seen = set()
            for row_number, row in enumerate(values[1:], 2):
                if row[0] is None:
                    if any(v is not None for v in row[1:3]):
                        raise ValueError(f'Missing identifier: {sheet.title}, row {row_number}')
                    continue
                qid = normalize_question_id(row[0])
                if qid in seen:
                    raise ValueError(f'Duplicate normalized identifier: {sheet.title}, {qid}')
                seen.add(qid)
                points = number(row[1], 'points')
                rate = number(row[2], 'score_rate', allow_zero=True)
                if rate > 1:
                    raise ValueError(f'Rate must be in [0, 1]: {sheet.title}, row {row_number}')
                rows.append({'year': year, 'paper_id': f'gaokao_{year}', 'population': '西城',
                             'question_id': qid, 'source_question_id': str(row[0]),
                             'points': points, 'actual_score_rate': rate,
                             'source_sheet': sheet.title, 'source_row': row_number})
            # Parent totals and their descendant rows cannot both be counted.
            for qid in seen:
                if any(other.startswith(qid + '-') for other in seen):
                    raise ValueError(f'Parent and child both included: {sheet.title}, {qid}')
            coverage = sum(row['points'] for row in rows)
            declared = number(values[1][5], 'declared coverage')
            if coverage > 100 or abs(coverage - declared) > 1e-8:
                raise ValueError(f'Points do not match declared coverage: {sheet.title}')
            declared_rate = number(values[1][6], 'declared total rate', allow_zero=True)
            if declared_rate > 1:
                raise ValueError(f'Invalid declared total rate: {sheet.title}')
            weighted_rate = sum(row['points'] * row['actual_score_rate'] for row in rows) / coverage
            reports.append({'year': year, 'observed_rows': len(rows), 'covered_points': coverage,
                            'declared_covered_points': declared, 'full_paper_points': 100,
                            'unobserved_points': 100 - coverage,
                            'unique_ids': True, 'parent_child_overlap': False,
                            'declared_total_rate': declared_rate,
                            'computed_observed_weighted_rate': weighted_rate,
                            'total_rate_difference': weighted_rate - declared_rate})
            normalized.extend(rows)
    finally:
        workbook.close()
    return normalized, sorted(reports, key=lambda row: row['year'])


def public_summary(reports):
    return {'received_date': '2026-11-02', 'population': '西城', 'exam': '北京高考物理',
            'observed_rows': sum(row['observed_rows'] for row in reports),
            'year_count': len(reports),
            'years': [{key: row[key] for key in ('year', 'observed_rows', 'covered_points',
                       'full_paper_points', 'unobserved_points')} for row in reports],
            'status': '表格结构与分值核验完成；题目、参考答案及小问映射待逐项核对；尚未训练。',
            'scope': '仅报告各年已提供的统计范围；未列出的得分率保持缺失，不填零，不推断完整试卷均分。',
            'validation': '七年均属历史数据；2026年已用于误差分析，最终有效性仍需独立或前瞻试卷确认。'}


def ensure_private_directory(path):
    private_root = (ROOT / 'data/private').resolve()
    result = path.resolve()
    if result != private_root and private_root not in result.parents:
        raise ValueError('Outputs with actual rates must stay inside data/private')
    result.mkdir(parents=True, exist_ok=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--private-dir', type=Path, default=ROOT / 'data/private/gaokao_2020_2026_20261102')
    parser.add_argument('--coverage-summary', type=Path)
    args = parser.parse_args()
    rows, reports = parse_workbook(args.source)
    if {row['year'] for row in reports} != set(range(2020, 2027)):
        raise ValueError('This intake expects exactly 2020–2026')
    out = ensure_private_directory(args.private_dir)
    digest = hashlib.sha256(args.source.read_bytes()).hexdigest()
    raw = out / args.source.name
    if raw.exists() and hashlib.sha256(raw.read_bytes()).hexdigest() != digest:
        raise ValueError('Source changed; create a separate versioned intake directory')
    if raw.resolve() != args.source.resolve():
        shutil.copy2(args.source, raw)
    with (out / 'observed_rates.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    audit = {'source_sha256': digest, 'source_file': str(args.source.resolve()),
             'years': reports, 'row_count': len(rows),
             'missing_policy': 'Use observed records only; no zero filling or missing-rate inference.'}
    (out / 'intake_audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
    summary = public_summary(reports)
    if args.coverage_summary:
        args.coverage_summary.parent.mkdir(parents=True, exist_ok=True)
        args.coverage_summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
