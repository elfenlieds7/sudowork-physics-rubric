"""Catch structured observed-outcome exports in the current public Git tree.

This is a publication guard, not proof that arbitrary prose/images contain no data.
It prints paths and field names only, never example records or observed values.
"""
import argparse
import csv
import io
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent.parent
FIELDS = {'score_rate', 'actual', 'actual_score_rate', 'actual_total_pp', 'xicheng_rate', 'beijing_rate'}


def observed_json(value):
    if isinstance(value, dict):
        return any((key in FIELDS and isinstance(item, (int, float)) and not isinstance(item, bool)) or observed_json(item)
                   for key, item in value.items())
    if isinstance(value, list):
        return any(observed_json(item) for item in value)
    return False


def inspect(name, raw):
    suffix = Path(name).suffix.lower()
    if suffix == '.csv':
        reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
        fields = FIELDS.intersection(reader.fieldnames or [])
        return any(row.get(key) not in ('', None, 'nan', 'NaN', 'null') for row in reader for key in fields)
    if suffix == '.json':
        return observed_json(json.loads(raw))
    if suffix in ('.html', '.js'):
        return bool(re.search(r'''["'](?:actual|actual_score_rate|score_rate)["']\s*:\s*-?(?:\d|\.\d)''', raw.decode('utf-8')))
    if suffix == '.xlsx':
        import openpyxl
        workbook = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
        try:
            for sheet in workbook:
                rows = sheet.iter_rows(values_only=True)
                columns = [i for i, field in enumerate(next(rows, ())) if str(field) in FIELDS or '得分率' in str(field)]
                if any(i < len(row) and row[i] is not None for row in rows for i in columns):
                    return True
        finally:
            workbook.close()
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--staged', action='store_true')
    args = parser.parse_args()
    command = ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACMR', '-z'] if args.staged else ['git', 'ls-files', '-z']
    names = filter(None, subprocess.check_output(command, cwd=ROOT).decode().split('\0'))
    failures = []
    checked = 0
    for name in names:
        if Path(name).suffix.lower() not in ('.csv', '.json', '.html', '.js', '.xlsx'):
            continue
        raw = subprocess.check_output(['git', 'show', ':' + name], cwd=ROOT) if args.staged else (ROOT / name).read_bytes()
        checked += 1
        if inspect(name, raw):
            failures.append(name)
    print(json.dumps({'checked_files': checked, 'observed_data_files': failures}, ensure_ascii=False))
    raise SystemExit(1 if failures else 0)


if __name__ == '__main__':
    main()
