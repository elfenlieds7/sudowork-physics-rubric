"""Build a private, checksum-verified handoff outside the public repository."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess

from verify_private_handoff import digest, verify, within

ROOT = Path(__file__).resolve().parent.parent


def build(output):
    output = output.resolve()
    if output == ROOT or ROOT in output.parents:
        raise ValueError('Build the private bundle outside the public repository')
    if output.exists():
        raise ValueError('Output exists; use a new versioned directory')
    names = {p.relative_to(ROOT).as_posix() for p in (ROOT / 'data/private').rglob('*')
             if p.is_file() and p.name != '.DS_Store'}
    legacy = ROOT / 'data/private/handoff_20261109/removed_from_public_tracking.json'
    if legacy.exists():
        names.update(json.loads(legacy.read_text(encoding='utf-8'))['paths'])
    tracked = set(subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0'))
    sources = []
    for name in sorted(names):
        source = within(ROOT, name)
        if name in tracked or not source.is_file():
            raise ValueError('Private source is tracked or missing: ' + name)
        if subprocess.run(['git', 'check-ignore', '-q', '--', name], cwd=ROOT).returncode != 0:
            raise ValueError('Private source is not Git ignored: ' + name)
        sources.append((name, source))
    output.mkdir(parents=True, mode=0o700)
    entries = []
    for name, source in sources:
        destination = output / 'payload' / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        entries.append({'path': name, 'bytes': destination.stat().st_size,
                        'sha256': digest(destination), 'source_machine': 'Mac',
                        'source_path': str(source), 'windows_receipt': 'unconfirmed',
                        'training_machine_presence': 'UNKNOWN'})
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    manifest = {'schema_version': 1, 'created_utc': datetime.now(timezone.utc).isoformat(),
                'code_repository': 'https://github.com/elfenlieds7/sudowork-physics-rubric',
                'code_commit': commit, 'source_machine': 'Mac', 'files': entries,
                'training_machine_status': 'UNKNOWN; no successful SSH inventory or transfer by this workline',
                'missing_legacy_private_inputs': ['data/private/2026_validation/2026_teacher_actuals.xlsx',
                                                  'data/private/cohort_calibration.csv']}
    (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    manifest_sha = digest(output / 'manifest.json')
    (output / 'manifest.sha256').write_text(manifest_sha + '  manifest.json\n', encoding='utf-8')
    lines = ['# 私密接续包 · 2026-11-09', '', '仅通过用户自己的 Dropbox 交接；不创建公开分享链接。', '',
             '代码提交：`' + commit + '`。文件均已在 Mac 确认；Windows 收到后须重新校验。训练机上的副本状态 UNKNOWN，本工作线未向其传输。', '',
             '先在新代码仓库运行：', '', '```text',
             'python scripts/verify_private_handoff.py --bundle <本目录>',
             'python scripts/verify_private_handoff.py --bundle <本目录> --restore-to <仓库根目录>', '```', '',
             '恢复只写受 Git 忽略的非跟踪路径；已有不同版本时停止。不要覆盖 Windows 自己的独有成果。', '',
             '旧单年 2026 工作簿与 cohort_calibration.csv 当前 Mac 没有，未伪造或补造。此包含旧页面的完整私密备份，不得重新公开发布。', '',
             '公开仓库继续阅读 docs/windows-handoff-20261109.md。', '',
             '## 文件清单（完整 SHA-256）', '', '| 相对恢复路径 | 字节 | SHA-256 |', '|---|---:|---|']
    lines += [f"| `{e['path']}` | {e['bytes']} | `{e['sha256']}` |" for e in entries]
    (output / 'README_PRIVATE.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    verify(output)
    (output / 'READY').write_text('manifest_sha256=' + manifest_sha + '\n', encoding='utf-8')
    return {'files': len(entries), 'bytes': sum(e['bytes'] for e in entries), 'manifest_sha256': manifest_sha,
            'code_commit': commit, 'integrity': 'verified'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.output), ensure_ascii=False))


if __name__ == '__main__':
    main()
