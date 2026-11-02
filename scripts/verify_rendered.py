#!/usr/bin/env python3
"""Ensure the rendered MyST tree retains source tables, figures, and equations."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def count_nodes(node):
    counts = Counter()
    if isinstance(node, dict):
        if 'type' in node:
            counts[node['type']] += 1
        for value in node.values():
            counts.update(count_nodes(value))
    elif isinstance(node, list):
        for child in node:
            counts.update(count_nodes(child))
    return counts


manifest = json.loads((ROOT / 'source/manifest.json').read_text())
rendered = {}
for path in (ROOT / '_build/site/content').glob('*.json'):
    article = json.loads(path.read_text())
    if 'mdast' in article and 'location' in article:
        rendered[article['location'].lstrip('/')] = count_nodes(article['mdast'])

errors = []
totals = Counter()
for page in manifest['pages']:
    counts = rendered.get(page['file'])
    if counts is None:
        errors.append(f'No rendered page for {page["file"]}')
        continue
    totals.update(counts)
    if counts['table'] != page['tables']:
        errors.append(f'{page["file"]}: expected {page["tables"]} tables, rendered {counts["table"]}')
    if counts['image'] < page['images']:
        errors.append(f'{page["file"]}: source figures lost during rendering')
    if counts['math'] + counts['inlineMath'] < page['math']:
        errors.append(f'{page["file"]}: source equations lost during rendering')
    if counts['code']:
        errors.append(f'{page["file"]}: textbook content accidentally rendered as code')

if errors:
    raise SystemExit('\n'.join(errors))
print(f'Rendered content verified: {totals["table"]} tables, {totals["image"]} figures, '
      f'{totals["math"] + totals["inlineMath"]} math expressions; no accidental code blocks.')
