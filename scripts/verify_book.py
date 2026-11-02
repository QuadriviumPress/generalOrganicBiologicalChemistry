#!/usr/bin/env python3
"""Verify complete source coverage, rights records, and local references."""
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SourceIndex(HTMLParser):
    def __init__(self):
        super().__init__()
        self.heading = False
        self.pages = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'h3':
            self.heading = True
        if tag == 'a' and self.heading and attrs.get('href', '').endswith('.html'):
            self.pages.add(attrs['href'])

    def handle_endtag(self, tag):
        if tag == 'h3':
            self.heading = False


def image_paths(text):
    return set(re.findall(r'!\[[^\n]*?\]\(([^\s)]+)', text) +
               re.findall(r'\{figure\}\s+([^\s]+)', text))


def main():
    manifest = json.loads((ROOT / 'source/manifest.json').read_text())
    plans = json.loads((ROOT / 'figure-replacements.json').read_text())['entries']
    errors = []
    index = SourceIndex()
    index.feed((ROOT / 'source/index.html').read_text())
    if sha(ROOT / 'source/index.html') != manifest['index_sha256']:
        errors.append('Source table of contents checksum mismatch.')
    pages = manifest['pages']
    source_pages = {p['source'] for p in pages}
    if source_pages != index.pages or len(pages) != 24:
        errors.append('Import must cover all 24 top-level source pages exactly once.')
    chapters = [p for p in pages if p['file'].startswith('chapters/')]
    numbers = {int(re.match(r'Chapter (\d+):', p['title'])[1]) for p in chapters}
    if numbers != set(range(1, 21)) or len(chapters) != 20:
        errors.append('All 20 chapters must be present, in order.')
    documents = {}
    for p in pages:
        source = ROOT / 'source' / p['source']
        if not source.is_file() or sha(source) != p['source_sha256']:
            errors.append(f'Source missing or modified: {source}')
        path = ROOT / p['file']
        if not path.is_file():
            errors.append(f'Missing imported page: {path}')
            continue
        text = path.read_text()
        documents[p['file']] = text
        if not re.search(r'^# ', text, re.M):
            errors.append(f'Missing H1: {p["file"]}')
        if 'CHEMISTRYTOKEN' in text or 'CHEMISTRYFOOTNOTE' in text:
            errors.append(f'Unexpanded conversion marker: {p["file"]}')
        original_images = re.findall(r'<img\b[^>]*src="([^"]+)"', source.read_text())
        active = image_paths(text)
        for image in original_images:
            if image.startswith('shared/'):
                continue
            plan = plans.get(Path(image).stem[:8])
            expected = ['/' + a['path'] for a in plan['assets']] if plan else ['/images/' + image]
            if not all(path in active for path in expected):
                errors.append(f'Lost source image or replacement: {p["file"]}: {image}')
        if re.search(r'!\[\]\(', text):
            errors.append(f'Empty image alternative text: {p["file"]}')
        for figure in re.finditer(r'^(`{3,})\{figure\}[^\n]*\n(.*?)(?=^\1\s*$)', text, re.M | re.S):
            if not re.search(r'^:alt: .+', figure[2], re.M):
                errors.append(f'Missing figure alternative text: {p["file"]}')
    for name in ('index.md', 'SOURCES.md', 'front/license.md', 'image-credits.md', 'FIGURE-AUDIT.md'):
        documents[name] = (ROOT / name).read_text()
    labels = {}
    for name, text in documents.items():
        found = re.findall(r'^\s*\(([^()\n]+)\)=$', text, re.M) + re.findall(r'^\s*:(?:name|label):\s*(\S+)', text, re.M)
        labels[name] = set(found)
        if len(found) != len(set(found)):
            errors.append(f'Duplicate labels: {name}')
        used = set(re.findall(r'\[\^(chem-\d+)\]', re.sub(r'^\[\^chem-\d+\]:', '', text, flags=re.M)))
        defined = set(re.findall(r'^\[\^(chem-\d+)\]:', text, re.M))
        if used != defined:
            errors.append(f'Footnote mismatch: {name}')
    for name, text in documents.items():
        prose = re.sub(r'\$\$.*?\$\$|(?<!\\)\$[^$\n]*(?<!\\)\$', '', text, flags=re.S)
        hrefs = re.findall(r'(?<!\\)\]\(([^\s)]+)\)', prose) + list(image_paths(text))
        for href in hrefs:
            url = urlsplit(href)
            if url.scheme or url.netloc:
                continue
            raw = unquote(url.path)
            target = ((ROOT / raw.lstrip('/')) if raw.startswith('/') else ROOT / name / '..' / raw).resolve() if raw else ROOT / name
            if not target.is_file():
                errors.append(f'Broken local link: {name}: {href}')
            elif url.fragment and target.suffix == '.md':
                if url.fragment not in labels.get(str(target.relative_to(ROOT)), set()):
                    errors.append(f'Broken local fragment: {name}: {href}')
    restricted_hashes = {p['original_sha256'] for p in plans.values()}
    for key, plan in plans.items():
        text = documents[plan['page']]
        if '/images/' + plan['original_asset'] in text:
            errors.append(f'Replaced original is still referenced: {key}')
        if (ROOT / 'images' / plan['original_asset']).exists():
            errors.append(f'Replaced original bytes are still shipped: {key}')
        for a in plan['assets']:
            for field in ('path', 'title', 'alt', 'credit', 'license', 'license_url', 'source', 'sha256'):
                if not a.get(field):
                    errors.append(f'Incomplete replacement provenance: {key}: {field}')
            if a['license_url'] not in text or a['credit'] not in text:
                errors.append(f'Replacement credit not visible: {key}')
            if not (ROOT / a['path']).is_file() or sha(ROOT / a['path']) != a['sha256']:
                errors.append(f'Replacement missing or modified: {a["path"]}')
    for name, asset in manifest['assets'].items():
        path = ROOT / name
        if not path.is_file() or sha(path) != asset['sha256']:
            errors.append(f'Missing or modified book asset: {name}')
        for field in ('credit', 'license', 'source', 'alt'):
            if not asset.get(field):
                errors.append(f'Missing asset {field}: {name}')
    for path in (ROOT / 'images').rglob('*'):
        if path.is_file() and sha(path) in restricted_hashes:
            errors.append(f'Restricted/replaced source bytes found: {path}')
    toc = (ROOT / 'myst.yml').read_text()
    for name in documents:
        if name not in toc:
            errors.append(f'Page missing from TOC: {name}')
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'Verified all {len(pages)} source pages (20 chapters, three front pages, appendix), '
          f'{len(manifest["assets"])} assets, {len(plans)} replacements, '
          f'{sum(map(len, labels.values()))} targets; no restricted originals shipped.')


if __name__ == '__main__':
    main()
