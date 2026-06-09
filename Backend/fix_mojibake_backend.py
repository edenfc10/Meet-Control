from pathlib import Path

ROOT = Path('app')
FILES = list(ROOT.rglob('*.py')) + [Path('main.py'), Path('logger.py')]

MARKERS = ('×', 'â', '�')

def recover_text(s: str) -> str:
    # Recover UTF-8 text that was decoded as cp1252/latin-1 then re-encoded.
    for enc in ('cp1252', 'latin-1'):
        try:
            candidate = s.encode(enc, errors='strict').decode('utf-8', errors='strict')
            return candidate
        except Exception:
            continue
    return s

changed_files = []
for path in FILES:
    if not path.exists():
        continue
    text = path.read_text(encoding='utf-8', errors='replace')
    lines = text.splitlines(keepends=True)
    out_lines = []
    changed = False

    for line in lines:
        if any(m in line for m in MARKERS):
            fixed = recover_text(line)
            if fixed != line:
                changed = True
                out_lines.append(fixed)
            else:
                out_lines.append(line)
        else:
            out_lines.append(line)

    if changed:
        path.write_text(''.join(out_lines), encoding='utf-8', newline='')
        changed_files.append(str(path))

print(f'changed_files={len(changed_files)}')
for f in changed_files:
    print(f)
