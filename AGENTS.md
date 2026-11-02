# AGENTS.md

## Standard

Follow the [QuadriviumPress MyST baseline](https://github.com/QuadriviumPress/bindery/blob/main/doc/myst-baseline.md) and [presentation skill](https://github.com/QuadriviumPress/bindery/blob/main/skills/quadrivium-myst-presentation/SKILL.md). This edition starts from `opiniatedMystmdBookTemplate` and adapts the General Chemistry importer.

## Commands

```bash
npm ci
npm run start
npm run verify
npm run build
npm run check
npm run import:source -- /path/to/introduction-to-chemistry-general-organic-and-biological
npm run render:figures
```

## Intentional differences

- All 20 source chapters live in `chapters/ch-NN-*.md`; three front-matter pages live in `front/`, and the periodic-table appendix lives in `appendices/`.
- The importer requires Python 3, Beautiful Soup, PyYAML, Pillow, and pandoc. Normal verification and builds need Node and Python's standard library.
- Original combined HTML pages and their SHA-256 hashes are preserved in `source/`. Restricted source image bytes are excluded. `source/manifest.json` records every source page and its table, equation, image, question, and answer counts.
- Source numbering is literal, so automatic numbering is disabled.
- `figure-replacements.json` is the authoritative replacement ledger. `scripts/render_figures.py` regenerates original SVG diagrams; `scripts/figure_replacements.py` installs approved replacements before copying assets and generates `image-credits.md` and `FIGURE-AUDIT.md`. Keep captions, alt text, credits, and hashes aligned.
- `verify` checks source coverage, checksums, local links, cross-references, and image rights records. `verify_rendered.py`, included in `build` and `check`, checks table, image, and equation coverage and rejects prose parsed as code. `check` also performs the template's PWA setup after a strict HTML build.
- Content retains CC BY-NC-SA 3.0. Template code retains its MIT notice in `LICENSE-CODE`. Independently sourced images retain their component licenses.
- Imports overwrite converted Markdown; document substantive edits in `SOURCES.md` and preserve them in the importer.

## Presentation gap

Learning objectives, key takeaways, and source callouts become MyST admonitions. Source question and answer groups retain their original numbering and order: the HTML does not always pair individual questions with answers, so the conversion preserves that pedagogy. Glossary definitions become footnotes; tables become MyST list tables. Every figure has alternative text, drawn from its title or surrounding source context for retained instructional artwork and written explicitly for replacements. An import is not a new scientific or medical edition; source-era statements remain except for documented figure-related corrections.
