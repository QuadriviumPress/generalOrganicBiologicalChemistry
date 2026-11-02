# Onboarding validation

Validated 2026-11-02 with Node 26.13.0, npm 11.20.0, and MyST 1.12.0.

- All 24 top-level source pages imported: 20 chapters, three front-matter pages, and one appendix. The new license page and attribution pages are additional editorial front/back matter.
- Source inventory: 108 tables, 942 image placements, 228 MathML expressions, 1,817 question blocks, and 1,524 answer blocks.
- `npm run verify`: passes; checks source checksums and index coverage, all local assets, 383 reference targets, footnotes, replacement provenance, visible credits, and absence of replaced original image bytes.
- `BASE_URL=/generalOrganicBiologicalChemistry npm run check`: passes; strict HTML and internal-link checks, rendered-content audit, and PWA setup.
- Rendered audit: 108 tables, 953 images (including repeated spanning-table content and multi-image replacements), and 228 mathematical expressions; no prose parsed as code.
- All retained source images were inspected in a visual contact-sheet inventory. A credit-line audit and the visual inventory produced 58 replaced source-image slots. Replacements include original educational SVG diagrams, individually credited open photographs, and a current periodic table. No pending replacement entries remain.
- All original SVG replacements were rasterized and visually inspected for layout, labels, and consistency with their captions. These are scientific schematics, explicitly distinguished from photographs or specimen images.
- Import repeatability: reimporting the same archive produced byte-identical output for all 30 generated content, configuration, manifest, ledger, and credit files checked.
- Headless Chromium browser audit: all 20 chapter routes plus the home page, appendix, source attribution, and image credits load with no broken images and no KaTeX rendering errors. The PWA registers at `/generalOrganicBiologicalChemistry/`, and its manifest resolves under the same scope. A previously visited carbohydrate chapter reloaded successfully with the browser offline; all 69 chapter images loaded. Desktop and mobile layouts were visually inspected.
- Bindery catalog schema and repository compliance checks pass with no failures or warnings. The catalog entry and generated landing page are maintained in bindery; publication status and the live URL are recorded there.

Source-era scientific and medical prose has not undergone a comprehensive editorial revision. Specific figure-related updates and the historical appendix data are documented in SOURCES.md.
