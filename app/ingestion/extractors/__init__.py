"""Source readers: bytes and JSON:API responses -> text.

``drupal_extractor`` walks the CMS; ``attachment`` downloads a node's PDF;
``pdf_extractor`` routes each page between ``pymupdf_local`` (text),
``camelot_tables`` (tables) and Azure Document Intelligence (OCR);
``text_normalize`` strips layout boilerplate from the result.
"""
