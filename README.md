# Introduction to Chemistry: General, Organic, and Biological

A complete MyST Markdown adaptation of the 2012 version 1.0 textbook: **20 chapters, three front-matter pages, and the periodic-table appendix**. Built from QuadriviumPress's `opiniatedMystmdBookTemplate`, following the `introductoryChemistry` and `generalChemistry` editions.

The text covers general chemistry, organic compounds, carbohydrates, lipids, proteins, enzymes, nucleic acids, and metabolism. Stock photographs and permission-only images are replaced with credited open images and original SVG teaching diagrams. See [the figure audit](FIGURE-AUDIT.md), [image credits](image-credits.md), and [validation report](QA-REPORT.md).

## Build

Requires Node >=26, npm 11, and Python 3.

```bash
npm ci
npm run start
npm run verify
npm run build
npm run check
```

The HTML book is written to `_build/html/`. `check` validates source coverage and image provenance, builds with strict internal-link checks, checks rendered tables and mathematics, and installs the PWA shell. Offline support caches pages after visits; it does not download the entire textbook automatically.

To test a GitHub Pages project path:

```bash
BASE_URL=/generalOrganicBiologicalChemistry npm run build
```

## Source and license

Adapted from [Introduction to Chemistry: General, Organic, and Biological, v1.0](https://2012books.lardbucket.org/books/introduction-to-chemistry-general-organic-and-biological/), preserved by **Andy Schmitz** on December 29, 2012, under [CC BY-NC-SA 3.0](https://creativecommons.org/licenses/by-nc-sa/3.0/). The source requests omission of customary attribution to the original author and publisher; its notice is reproduced in [license.md](front/license.md). The source's biographical front matter is preserved as supplied.

This edition retains the textbook license. Openly licensed images retain their individual licenses, with visible credit lines and a machine-readable ledger. Template code remains under [MIT](LICENSE-CODE). See [SOURCES.md](SOURCES.md), [LICENSE](LICENSE), and [image-credits.md](image-credits.md).

## Repeat the import

Download and extract the [original archive](https://2012books.lardbucket.org/zips/introduction-to-chemistry-general-organic-and-biological.zip). Its SHA-256 is `47dd229428df6206601a9ebd8fdf0cce789a9d60da0951ad99b94cb3da46c329`.

Install conversion dependencies with `python3 -m pip install -r scripts/requirements-import.txt` and install pandoc. Then:

```bash
npm run render:figures
npm run import:source -- /path/to/introduction-to-chemistry-general-organic-and-biological
npm run check
```

The approved photographs and generated diagrams are included locally. Reimporting requires no image searches or downloads. The importer checks replacement hashes and excludes restricted original assets before copying any source images.

## Layout and publication

- `chapters/`, `front/`, `appendices/`: complete converted content.
- `source/`: source HTML, checksums, coverage manifest; no restricted original photographs.
- `images/`: open instructional artwork and approved replacements.
- `scripts/`: importer, SVG generator, structural and rendered-content checks, PWA setup.
- `.github/`: CI and Pages deployment configuration.

The [GitHub repository](https://github.com/QuadriviumPress/generalOrganicBiologicalChemistry) publishes the [online textbook](https://quadriviumpress.com/generalOrganicBiologicalChemistry/) through GitHub Pages. The deployment workflow validates the complete book before publishing each update to `main`. The book is registered in bindery’s catalog.
