#!/usr/bin/env python3
"""Rebuild the MyST edition from the preserved Lardbucket HTML archive (requires pandoc)."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

from figure_replacements import prepare_figures, figure_node, asset_record

from bs4 import BeautifulSoup
import yaml

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = 'https://2012books.lardbucket.org/books/introduction-to-chemistry-general-organic-and-biological/'
REVISION = 'Lardbucket archive, preserved 2012-12-29; retrieved 2026-11-02'
WRITER = 'markdown+tex_math_dollars+pipe_tables-simple_tables-multiline_tables-grid_tables-subscript-superscript'


def label(value):
    return 'src-' + re.sub(r'[^a-zA-Z0-9-]', '-', value).lower()


def pandoc(html):
    result = subprocess.run(['pandoc', '-f', 'html-native_divs-native_spans', '-t', WRITER,
                             '--wrap=none'], input=html, text=True, capture_output=True, check=True)
    if result.stderr:
        raise RuntimeError(result.stderr)
    return result.stdout.strip()


def clean_math(match):
    value = match[0]
    symbols = {'·': r'\cdot ', '∣': r'\mid ', '≡': r'\equiv ',
               '→': r'\rightarrow ', 'µ': r'\mu ', '‾': r'\overline{\phantom{M}}'}
    # Symbols embedded in a MathML text run must leave TeX's text mode.
    def text_run(m):
        content = m[1]
        for symbol, command in symbols.items():
            content = content.replace(symbol, '}' + command + r'\text{')
        return r'\text{' + content + '}'
    value = re.sub(r'\\text\{([^{}]*)\}', text_run, value)
    for symbol, command in symbols.items():
        value = value.replace(symbol, command)
    # Pandoc sometimes emits a TeX spacing backslash at the end of a block.
    value = re.sub(r'(?<!\\)\\\s*(?=\$\$$)', '', value)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='Extracted upstream repository')
    args = parser.parse_args()
    source = args.source.resolve()
    index = BeautifulSoup((source / 'index.html').read_text(), 'html.parser')
    entries = []
    for item in index.select('#toc-top-ul > li'):
        link = item.select_one('h3 a')
        number = re.match(r'Chapter (\d+):', link.get_text())
        slug = re.sub(r'^s\d+-', '', Path(link['href']).stem)
        if number:
            output = f'chapters/ch-{int(number[1]):02d}-{slug}.md'
        elif link.get_text().startswith('Appendix') or 'Credits' in link.get_text():
            output = f'appendices/{slug}.md'
        else:
            output = f'front/{slug}.md'
        entries.append({'source': link['href'], 'file': output, 'title': link.get_text(),
                        'body': BeautifulSoup((source / link['href']).read_text(), 'html.parser').select_one('#book-content')})

    replacements_ledger = prepare_figures(source, entries)

    # The upstream exposes both combined chapters and section pages. Map both
    # URL forms, plus the original publisher's identifier-based links.
    ids = {tag['id']: entry['file'] for entry in entries for tag in entry['body'].select('[id]')}
    urls = {entry['source']: entry['file'] for entry in entries}
    for item in index.select('#toc-top-ul > li'):
        parent = item.select_one('h3 a')['href']
        for link in item.select('a[href]'):
            urls[link['href']] = urls[parent]
    referenced = set()
    fallbacks = []
    for entry in entries:
        for a in entry['body'].select('a[href]'):
            href = a['href']
            parsed = urlsplit(href)
            if parsed.scheme or parsed.netloc:
                continue
            fragment = unquote(parsed.fragment)
            if fragment in ids:
                a['href'] = '/' + ids[fragment] + '#' + label(fragment)
                referenced.add(fragment)
            elif parsed.path in urls and not fragment:
                a['href'] = '/' + urls[parsed.path]
            elif parsed.path == 'index.html':
                a['href'] = '/index.md'
            else:
                # Keep a traceable source link for defects already in the source.
                target = parsed.path if parsed.path.endswith('.html') else entry['source']
                a['href'] = UPSTREAM + target + ('#' + fragment if fragment else '')
                fallbacks.append({'page': entry['file'], 'href': href, 'fallback': a['href']})

    manifest = {'upstream': UPSTREAM, 'revision': REVISION,
                'archive_sha256': '47dd229428df6206601a9ebd8fdf0cce789a9d60da0951ad99b94cb3da46c329',
                'index_sha256': hashlib.sha256((source / 'index.html').read_bytes()).hexdigest(),
                'pages': [], 'assets': {},
                'source_link_fallbacks': fallbacks}
    for entry in entries:
        body = entry['body']
        counts = {name: len(body.select(selector)) for name, selector in
                  [('images', 'img'), ('math', 'math'), ('tables', 'table'),
                   ('questions', '.question'), ('answers', '.answer')]}
        # Two source MathML nodes are empty layout placeholders.
        counts['math'] = sum(bool(node.get_text(strip=True)) for node in body.select('math'))
        # Publisher HTML places introductory paragraphs directly inside lists.
        # Move those outside so pandoc cannot count them as extra problems.
        for listing in list(body.select('ol, ul')):
            for child in list(listing.children):
                if child.name and child.name != 'li':
                    child.extract()
                    listing.insert_before(child)
        replacements = {}

        def token(value, block=False):
            key = f'CHEMISTRYTOKEN{len(replacements):06d}END'
            replacements[key] = value
            tag = BeautifulSoup('<p></p>' if block else '<span></span>', 'html.parser').find()
            tag.string = key
            return tag

        # Keep definitions and source notes out of running sentences.
        footnotes = []
        for note in list(body.select('.glossdef, .footnote')):
            if not note.get_text(strip=True) and not note.find(['img', 'math']):
                note.decompose()
                continue
            key = f'chem-{len(footnotes) + 1}'
            content = BeautifulSoup('<div></div>', 'html.parser').div
            for child in list(note.contents):
                content.append(child.extract())
            footnotes.append((key, content))
            note.replace_with(token(f'[^{key}]'))
        for key, content in footnotes:
            p = BeautifulSoup('<p></p>', 'html.parser').p
            p.string = f'CHEMISTRYFOOTNOTE{key}END'
            body.append(p)
            body.append(content)

        # Render figures as MyST directives, substituting restricted assets
        # before any file copy. Original restricted image bytes never enter the book.
        for figure in list(body.select('.figure, .informalfigure')):
            if figure.find_parent(class_=lambda c: c and ('figure' in c)):
                continue
            figure.replace_with(token(figure_node(figure, source, entry, replacements_ledger, manifest), block=True))
        for image in body.select('img'):
            record = asset_record(image, source, entry, replacements_ledger, manifest)
            image['src'] = '/' + record['path']
            image['alt'] = record['alt']

        # MathML in this edition occasionally uses typographic dashes as minus
        # signs and bullet glyphs as multiplication dots. Use TeX-safe forms.
        for math in body.select('math'):
            for string in list(math.find_all(string=True)):
                value = str(string).replace('–', '-').replace('−', '-').replace('—', '-')
                value = value.replace('•', '·').replace('⋅', '·').replace('¯', '‾')
                string.replace_with(value)

        # Source heading levels flatten nested sections; restore the DOM hierarchy.
        if entry['file'].startswith('appendices/'):
            heading = body.find('h1')
            if heading:
                heading.clear()
                heading.string = entry['title']
        for heading in body.find_all(re.compile(r'^h[1-6]$')):
            sections = len([p for p in heading.parents if 'section' in p.get('class', [])])
            if heading.name in ('h1', 'h2'):
                heading.name = f'h{min(6, max(1, sections + 1))}'

        for tag in list(body.select('[id]')):
            if tag['id'] in referenced:
                anchor = token(f'({label(tag["id"])})=', block=True)
                # Labels attach to block nodes; inline source targets attach to
                # the containing paragraph, keeping prose readable.
                block = tag
                while block.name not in ('div', 'p', 'table', 'h1', 'h2', 'h3', 'h4', 'li') and block.parent != body:
                    block = block.parent
                block.insert_before(anchor)

        # List tables keep equations and multiline cell content in MyST's
        # parser. Expand source spans into an explicit rectangular grid.
        for table in reversed(list(body.select('table'))):
            rows = table.find_all('tr', recursive=False)
            if not rows:
                rows = [r for section in table.find_all(['thead', 'tbody', 'tfoot'], recursive=False)
                        for r in section.find_all('tr', recursive=False)]
            if not rows:
                continue
            grid = {}
            width = 0
            for row_index, row in enumerate(rows):
                column = 0
                for cell in row.find_all(['td', 'th'], recursive=False):
                    while (row_index, column) in grid:
                        column += 1
                    for dr in range(int(cell.get('rowspan', 1))):
                        for dc in range(int(cell.get('colspan', 1))):
                            grid[row_index + dr, column + dc] = str(cell)
                    column += int(cell.get('colspan', 1))
                width = max(width, column)
            replacement = BeautifulSoup('<div><ul></ul></div>', 'html.parser').div
            outer = replacement.ul
            for row_index in range(len(rows)):
                row_item = BeautifulSoup('<li><ul></ul></li>', 'html.parser').li
                for column in range(width):
                    cell_item = BeautifulSoup('<li></li>', 'html.parser').li
                    cell = BeautifulSoup(grid.get((row_index, column), '<td></td>'), 'html.parser').find()
                    for child in list(cell.contents):
                        cell_item.append(child.extract())
                    if not cell_item.get_text(strip=True) and not cell_item.find(['img', 'math']):
                        cell_item.string = '\u00a0'
                    row_item.ul.append(cell_item)
                outer.append(row_item)
            headers = len(table.thead.find_all('tr', recursive=False)) if table.thead else (1 if rows[0].find('th') else 0)
            # Nested source tables receive a shorter fence than their container.
            depth = len(table.find_parents('table'))
            fence = '`' * (8 - min(depth, 1))
            table.insert_before(token(f'{fence}{{list-table}}\n:header-rows: {headers}', block=True))
            table.insert_after(token(fence, block=True))
            table.replace_with(replacement)

        for callout in list(body.select('.learning_objectives, .key_takeaways, .callout')):
            heading = callout.find(re.compile(r'^h[1-6]$'), recursive=False)
            title = heading.get_text(' ', strip=True) if heading else ''
            if not title:
                continue
            kind = 'note' if 'learning_objectives' in callout.get('class', []) else 'important'
            if title.startswith('Example'):
                kind = 'admonition'
            depth = len([p for p in callout.parents if set(p.get('class', [])) & {'learning_objectives', 'key_takeaways', 'callout'}])
            fence = '`' * (12 - min(depth, 2))
            callout.insert_before(token(f'{fence}{{{kind}}} {title}', block=True))
            callout.insert_after(token(fence, block=True))
            heading.decompose()

        # Strip publisher layout attributes; math and table geometry stay intact.
        for tag in list(body.find_all()):
            if tag.find_parent('math') or tag.name == 'math':
                continue
            tag.attrs = {k: v for k, v in tag.attrs.items() if k in ('href', 'src', 'alt', 'rowspan', 'colspan', 'start')}
            if tag.name in ('div', 'span', 'a') and not tag.get('href') and not (tag.name == 'span' and tag.string and tag.string.startswith('CHEMISTRYTOKEN')):
                tag.unwrap()
        text = pandoc(body.decode_contents())
        for key, value in replacements.items():
            # A table inside a numbered problem must keep every line of its
            # options at the indentation pandoc assigned to that problem.
            def substitute(m):
                prefix = text[text.rfind('\n', 0, m.start()) + 1:m.start()]
                indentation = ' ' * len(prefix) if re.fullmatch(r'\s*(?:(?:\d+[.)]|[-+*])\s+)*', prefix) else ''
                return value.replace('\n', '\n' + indentation)
            text = re.sub(key, substitute, text)
        # Adjacent block equations must be separate Markdown blocks.
        def separate_equations(m):
            prefix = text[text.rfind('\n', 0, m.start()) + 1:m.start()]
            indentation = re.match(r'[ \t]*', prefix)[0]
            return '$$\n\n' + indentation + '$$'
        text = re.sub(r'\$\$[ \t]+\$\$', separate_equations, text)
        text = re.sub(r'\$\$.*?\$\$|(?<!\\)\$(?!\$)[^$]*(?<!\\)\$', clean_math, text, flags=re.S)
        # A source em dash emitted as --- must not become a thematic break
        # inside a table cell. Nonbreaking spaces keep empty cells explicit.
        text = re.sub(r'(?m)^([ \t]*(?:- )?- )---[ \t]*$', r'\1&mdash;', text)
        for key, _ in footnotes:
            marker = f'CHEMISTRYFOOTNOTE{key}END'
            start = text.index(marker)
            end = text.find('CHEMISTRYFOOTNOTE', start + len(marker))
            if end < 0:
                end = len(text)
            content = text[start + len(marker):end].strip()
            definition = f'[^{key}]: ' + content.replace('\n', '\n    ')
            text = text[:start] + definition + '\n\n' + text[end:]
        text = re.sub(r'\n{3,}', '\n\n', text).strip() + '\n'
        # The license page's source starts at h3; give every document an H1.
        if not re.search(r'^# ', text, re.M):
            text = '# ' + entry['title'] + '\n\n' + text
        if entry['file'].startswith('appendices/'):
            notice = ('```{note} Historical source data\n'
                      'The table below preserves the source edition’s atomic-weight data and provisional '
                      'element names. It is a historical reference, not a current IUPAC data table. '
                      'The replacement diagram uses all 118 official element symbols and CIAAW abridged '
                      '2024 atomic weights. Consult [CIAAW](https://www.ciaaw.org/abridged-atomic-weights.htm) '
                      'for the published weights and uncertainties.\n```\n\n')
            text = re.sub(r'(^# [^\n]+\n\n)', lambda m: m[0] + notice, text, count=1, flags=re.M)
        text = '\n'.join(line.rstrip() for line in text.splitlines()).rstrip() + '\n'
        target = ROOT / entry['file']
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        archive = ROOT / 'source' / entry['source']
        archive.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / entry['source'], archive)
        manifest['pages'].append({k: entry[k] for k in ('source', 'file', 'title')} | counts |
                                 {'source_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
                                  'markdown_sha256': hashlib.sha256(text.encode()).hexdigest()})
        print(f'Converted {entry["file"]}', flush=True)

    shutil.copy2(source / 'index.html', ROOT / 'source' / 'index.html')
    (ROOT / 'source' / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    config = yaml.safe_load((ROOT / 'myst.yml').read_text())
    config['project']['toc'] = [{'file': 'index.md'}, {'title': 'Front matter', 'children': [{'file': 'front/license.md'}] + [{'file': e['file']} for e in entries if e['file'].startswith('front/')]},
                                {'title': 'Chapters', 'children': [{'file': e['file']} for e in entries if e['file'].startswith('chapters/')]},
                                {'title': 'Appendices and credits', 'children': [{'file': e['file']} for e in entries if e['file'].startswith('appendices/')]}, {'file': 'SOURCES.md'}, {'file': 'image-credits.md'}, {'file': 'FIGURE-AUDIT.md'}]
    (ROOT / 'myst.yml').write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True))
    # Credits and replacement records are regenerated by prepare_figures().
    print(f'Imported {len(entries)} pages and {len(manifest["assets"])} assets; {len(fallbacks)} upstream link defects recorded.')


if __name__ == '__main__':
    main()
