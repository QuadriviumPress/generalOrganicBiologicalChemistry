"""Install approved figures before copying source assets; generate reader credits."""
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = 'https://2012books.lardbucket.org/books/introduction-to-chemistry-general-organic-and-biological/'
CONTENT_LICENSE = 'https://creativecommons.org/licenses/by-nc-sa/3.0/'

# These separately credited figures have explicit open licenses or are US
# federal works. All other separately credited imagery is replaced.
OPEN_SOURCE_IMAGES = {
    'fe38a48d': ('US Department of Agriculture', 'Public domain', 'https://www.myplate.gov/resources/graphics/myplate-graphics', 'https://creativecommons.org/publicdomain/mark/1.0/'),
    '9f27960f': ('US Navy', 'Public domain', 'https://commons.wikimedia.org/wiki/File:Hindenburg_burning.jpg', 'https://creativecommons.org/publicdomain/mark/1.0/'),
    '578a01b5': ('Chemicalinterest', 'Public domain', 'https://commons.wikimedia.org/wiki/File:Zn_reaction_with_HCl.JPG', 'https://creativecommons.org/publicdomain/mark/1.0/'),
    'b924b2d4': ('Myohan at English Wikipedia', 'CC BY 3.0', 'https://commons.wikimedia.org/wiki/File:Thyroid_scan.jpg', 'https://creativecommons.org/licenses/by/3.0/'),
    '72b9e9bb': ('NASA Goddard / MODIS Rapid Response Team', 'Public domain', 'https://earthobservatory.nasa.gov/images/44026/oil-slick-in-the-gulf-of-mexico', 'https://creativecommons.org/publicdomain/mark/1.0/'),
    '3d69a9fb': ('NASA Ozone Watch', 'Public domain', 'https://ozonewatch.gsfc.nasa.gov/daily.php?date=2006-09-24', 'https://creativecommons.org/publicdomain/mark/1.0/'),
    '50cc254b': ('Ernest Board (circa 1920), via Wellcome / Wikimedia Commons', 'Public domain', 'https://commons.wikimedia.org/wiki/File:Morton_Ether_1846.jpg', 'https://creativecommons.org/publicdomain/mark/1.0/'),
    '3e6a269d': ('US National Institutes of Health', 'Public domain', 'https://commons.wikimedia.org/wiki/File:Geneticcounseling.jpg', 'https://creativecommons.org/publicdomain/mark/1.0/'),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def key_for(src):
    return Path(src).stem[:8]


def label(value):
    return 'src-' + re.sub(r'[^a-zA-Z0-9-]', '-', value).lower()


def md(html):
    return subprocess.run(['pandoc', '-f', 'html', '-t', 'markdown+tex_math_dollars-subscript-superscript', '--wrap=none'],
                          input=str(html), text=True, capture_output=True, check=True).stdout.strip()


def prepare_figures(source, entries):
    ledger_path = ROOT / 'figure-replacements.json'
    ledger = json.loads(ledger_path.read_text())
    plans = ledger['entries']
    found = set()
    for entry in entries:
        for image in entry['body'].select('img'):
            key = key_for(image['src'])
            figure = image.find_parent(class_=lambda c: c and 'figure' in c)
            text = figure.get_text(' ', strip=True) if figure else ''
            # Capture context before figures are replaced with conversion tokens.
            # Later figures in a question list must never inherit token alt text.
            title_node = figure.select_one('.title') if figure else None
            paragraph = image.find_previous('p')
            context = (title_node.get_text(' ', strip=True) if title_node else
                       paragraph.get_text(' ', strip=True) if paragraph else '')
            image['alt'] = image.get('alt') or 'Chemical illustration: ' + (context or entry['title'])[:350]
            if any(word in text for word in ('Thinkstock', 'permission', 'RCSB', 'Silvering.jpg', 'Inzul')) and key not in plans:
                raise ValueError(f'Unresolved third-party figure: {image["src"]}')
            if key not in plans:
                continue
            found.add(key)
            plan = plans[key]
            plan['original_asset'] = image['src']
            plan['original_sha256'] = sha(source / image['src'])
            # When the visual audit adds a replacement after a first import,
            # remove only the previously generated copy, never an edited file.
            previous_asset = ROOT / 'images' / image['src']
            if previous_asset.exists():
                previous_manifest = json.loads((ROOT / 'source/manifest.json').read_text())
                known = previous_manifest['assets'].get('images/' + image['src'], {})
                if sha(previous_asset) not in (plan['original_sha256'], known.get('sha256')):
                    raise ValueError(f'Previously copied source asset was edited: {previous_asset}')
                previous_asset.unlink()
            plan['page'] = entry['file']
            title = figure.select_one('.title') if figure else None
            plan['source_title'] = title.get_text(' ', strip=True) if title else ''
            plan['source_id'] = figure.get('id') if figure else None
            for asset in plan['assets']:
                path = ROOT / asset['path']
                if not path.is_file() or sha(path) != asset['sha256']:
                    raise ValueError(f'Replacement missing or modified: {path}')
    if found != set(plans):
        raise ValueError(f'Replacement ledger contains unused entries: {set(plans) - found}')
    ledger_path.write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + '\n')
    credits = ['# Image credits\n',
               'The textbook text and its original instructional drawings are adapted under '
               '[CC BY-NC-SA 3.0](https://creativecommons.org/licenses/by-nc-sa/3.0/). '
               'Openly licensed components retain their own licenses. Restricted source photographs '
               'are replaced before assets are copied into this edition.\n',
               '## Replacement illustrations\n']
    audit = ['# Figure audit\n',
             'The audit covers every image in all 20 combined source chapters, the three front-matter pages, '
             'and the appendix. The 2012 Lardbucket archive supplies the original chemical structure drawings; '
             'its stock photographs are present, rather than omitted-image placeholders.\n',
             'Each replacement is installed during import, with its source slot, source SHA-256, local assets, '
             'credit, license, caption, alternative text, and output SHA-256 recorded in '
             '`figure-replacements.json`. Restricted original image bytes are not included in this repository.\n',
             '| Source page | Source figure or image | Replacement |\n| --- | --- | --- |']
    for key, p in plans.items():
        title = p['source_title'] or p['assets'][0]['title']
        credits += [f'### {title}\n', f'Used in [{Path(p["page"]).stem}]({p["page"]}). {p["caption"]}\n']
        for a in p['assets']:
            credits += [f'- **{a["title"]}** — {a["credit"]}; [{a["license"]}]({a["license_url"]}). '
                        f'[Source]({a["source"]}). {a["changes"]} '
                        f'Local asset: `{a["path"]}`.\n']
        audit += [f'| [{Path(p["page"]).stem}]({p["page"]}) | {title} | '
                  + ', '.join(a['title'] for a in p['assets']) + ' |']
    credits += ['## Retained separately credited open images\n']
    for key, (creator, license_name, url, license_url) in OPEN_SOURCE_IMAGES.items():
        credits += [f'- {creator}; [{license_name}]({license_url}). [Source and rights information]({url}). '
                    'Source-edition reproduction retained; converted to RGB or resized where needed.\n']
    audit += ['\n## Scope and editorial notes\n',
              '- All Thinkstock images and the BIPM and Citrasolv permission-only images have replacements.\n',
              '- Undocumented portraits become typographic author cards; these cards do not portray the authors.\n',
              '- Original diagrams are schematic, with scientific labels and descriptive alternative text. '
              'Photographic replacements retain their individual licenses and visible credit lines.\n',
              '- The original hemoglobin molecular rendering becomes an explicitly conceptual tetramer diagram.\n',
              '- The source periodic table in Figure 2.7 and the appendix become a modern table with all 118 named elements. '
              'Other source diagrams and the historical atomic-weight data table remain source-era material.\n',
              '- Captions are rewritten where the image changes. The kilogram caption distinguishes the historical artifact '
              'from the SI definition since 2019. Dialysis distinguishes diffusion of waste solutes from water removal. '
              'Ascorbic acid is described as an acidic lactone rather than a carboxylic acid.\n',
              '- No claim of a full scientific or medical content revision is made. The text represents a 2012 introductory textbook.\n']
    (ROOT / 'image-credits.md').write_text('\n'.join(credits).rstrip() + '\n')
    (ROOT / 'FIGURE-AUDIT.md').write_text('\n'.join(audit).rstrip() + '\n')
    return plans


def asset_record(image, source, entry, ledger, manifest):
    src = image['src']
    key = key_for(src)
    if key in ledger:
        raise ValueError(f'Restricted or replaced image outside a figure: {src}')
    original = (source / src).resolve()
    if not original.is_relative_to(source.resolve()):
        raise ValueError(f'Unsafe image path: {src}')
    dest = ROOT / 'images' / src
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(original, dest)
    # Web image encoders require RGB. Very large source scans are downsized
    # without changing the text's chemistry; both original and output hashes
    # are recorded, so normalization is explicit.
    if dest.suffix.lower() in ('.jpg', '.jpeg'):
        from PIL import Image
        with Image.open(dest) as im:
            if im.mode == 'CMYK' or dest.stat().st_size > 1_000_000:
                rgb = im.convert('RGB')
                rgb.thumbnail((2400, 2400))
                rgb.save(dest, 'JPEG', quality=87, optimize=True)
    figure = image.find_parent(class_=lambda c: c and 'figure' in c)
    title = figure.select_one('.title') if figure else None
    paragraph = image.find_previous('p')
    context = (title.get_text(' ', strip=True) if title else
               paragraph.get_text(' ', strip=True) if paragraph else entry['title'])
    alt = image.get('alt') or ('Chemical illustration: ' + context[:350])
    result = {'path': 'images/' + src, 'alt': alt, 'source_sha256': sha(original),
              'sha256': sha(dest), 'source': UPSTREAM + entry['source'],
              'credit': 'Source textbook instructional artwork', 'license': 'CC BY-NC-SA 3.0',
              'license_url': CONTENT_LICENSE}
    if key in OPEN_SOURCE_IMAGES:
        creator, lic, url, lic_url = OPEN_SOURCE_IMAGES[key]
        result.update(credit=creator, license=lic, source=url, license_url=lic_url)
    manifest['assets'][result['path']] = result
    return result


def figure_node(figure, source, entry, ledger, manifest):
    images = figure.select('img')
    if not images:
        return md(figure)
    title_node = figure.select_one('.title')
    title = title_node.get_text(' ', strip=True) if title_node else ''
    # Remove third-party credit text only after it has been classified. Approved
    # rights are rendered explicitly below; the archive HTML remains unchanged.
    captions = [md(p) for p in figure.find_all('p', recursive=False) if p != title_node]
    original_caption = '\n\n'.join(captions)
    result = []
    first = True
    for image in images:
        key = key_for(image['src'])
        if key in ledger:
            plan = ledger[key]
            assets = plan['assets']
            caption = plan['caption']
            for a in assets:
                manifest['assets'][a['path']] = a
        else:
            assets = [asset_record(image, source, entry, ledger, manifest)]
            caption = original_caption
        for a in assets:
            options = [f':alt: {a["alt"].replace(chr(10), " ")}']
            if first and figure.get('id'):
                options += [':name: ' + label(figure['id'])]
            if a['path'].endswith('.svg'):
                options += [':width: 100%']
            body = ('**' + re.sub(r'^\*\*|\*\*$', '', title) + '**\n\n' if title and first else '')
            body += caption + '\n\n'
            if key in ledger or key in OPEN_SOURCE_IMAGES:
                source_link = a['source']
                if source_link.startswith('scripts/'):
                    source_link = 'https://github.com/QuadriviumPress/generalOrganicBiologicalChemistry/blob/main/' + source_link
                body += f'Credit: {a["credit"]}; [{a["license"]}]({a["license_url"]}). [Source]({source_link}).'
            # A long fence safely encloses any table/list markup in a caption.
            result.append('``````````{figure} /' + a['path'] + '\n' + '\n'.join(options) + '\n\n' + body.strip() + '\n``````````')
            first = False
    return '\n\n'.join(result)
