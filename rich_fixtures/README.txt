RICH INGESTION FIXTURES

12 digital PDFs, 8 Word DOCX files, 11 page-scan PNGs, 1 relationship-diagram PNG, and 4 image-only scanned PDFs.

All are synthetic alternate representations of DOC-00001 through DOC-00012. Use them to test parsers/OCR/previews separately or replace a canonical source in an ingestion run. Do not count each format as independent corroborating evidence. The relationship diagram includes only statements S01-S03.

manifest.json records canonical IDs, checksums, format and purpose. Base manifests do not automatically ingest these files. No embeddings or simulation output are precomputed.

Regenerate using: python3 generate_rich_fixtures.py --root .
Requires python-docx, reportlab, PyMuPDF and Pillow in the development environment. The corpus generator itself uses only Python standard libraries.
