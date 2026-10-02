#!/usr/bin/env python3
"""Check that every file referenced by the site exists and that no file under assets/ or data/ is unused.

References are collected from index.html, style.css, app.js and data/*.json (any string that
looks like a relative path into assets/ or data/). JSON clip entries without an extension
(e.g. "assets/clips/x/seedance_2_0") stand for the .mp4 video plus its .webp poster, as app.js
loads them. Exit status 1 on any missing or unused file.
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = [ROOT / 'index.html', ROOT / 'style.css', ROOT / 'app.js'] + sorted((ROOT / 'data').glob('*.json'))
PAT = re.compile(r'''(?:assets|data)/[A-Za-z0-9_./-]+''')

refs = set()
for f in SRC:
    for m in PAT.findall(f.read_text(encoding='utf-8')):
        m = m.rstrip('.')
        if pathlib.PurePath(m).suffix:
            refs.add(m)
        else:  # extensionless clip base used by app.js media()
            refs.update({m + '.mp4', m + '.webp'})

missing = sorted(r for r in refs if not (ROOT / r).is_file())
files = {p.relative_to(ROOT).as_posix() for d in ('assets', 'data') for p in (ROOT / d).rglob('*') if p.is_file()}
unused = sorted(files - refs)

for r in missing: print('MISSING', r)
for r in unused: print('UNUSED ', r)
print(f'{len(refs)} referenced, {len(files)} files, {len(missing)} missing, {len(unused)} unused')
sys.exit(1 if missing or unused else 0)
