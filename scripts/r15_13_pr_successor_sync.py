from pathlib import Path

paths = (
    Path('docs/roadmap/R15_PLAN.md'),
    Path('docs/roadmap/R15_13_ACCEPTANCE.md'),
    Path('docs/continuity/KODEPOIA_CONTINUITY.md'),
)
for path in paths:
    text = path.read_text(encoding='utf-8')
    if 'PR #321' not in text and path.name != 'R15_13_ACCEPTANCE.md':
        raise SystemExit(f'expected PR #321 marker not found in {path}')
    text = text.replace('PR #321', 'PR #322')
    if path.name == 'R15_13_ACCEPTANCE.md':
        marker = '**Implementation PR:** #322'
        if marker not in text:
            raise SystemExit('acceptance implementation PR marker not found')
        text = text.replace(
            marker,
            '**Implementation PR:** #322 (non-draft successor; draft PR #321 was closed unmerged because the connected ready-for-review mutation was incompatible with GitHub current GraphQL schema)',
            1,
        )
    path.write_text(text, encoding='utf-8')
