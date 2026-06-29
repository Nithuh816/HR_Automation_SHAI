"""Document analysis: text extraction (OCR/PDF, graceful) and ID parsing.

OCR (pytesseract + Tesseract binary) and PDF text (pdfplumber) are optional —
when the libraries/binary are absent we simply skip extraction and route the
document to the manual-review queue. Aadhaar/PAN parsing runs on whatever text
we can recover and never auto-rejects a document.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from app.models.enums import DocumentStatus, DocumentType

_AADHAAR_RE = re.compile(r"(?<!\d)(\d{4}\s?\d{4}\s?\d{4})(?!\d)")
_PAN_RE = re.compile(r"\b([A-Z]{5}[0-9]{4}[A-Z])\b")

# Documents whose value is an ID number we try to auto-extract.
_ID_TYPES = {DocumentType.AADHAAR, DocumentType.PAN}


@dataclass
class Analysis:
    status: DocumentStatus
    aadhaar: str | None = None
    pan: str | None = None
    extracted: dict[str, Any] = field(default_factory=dict)


def ocr_available() -> bool:
    try:
        import pytesseract  # noqa: F401
        from PIL import Image  # noqa: F401
    except ImportError:
        return False
    return True


def _text_from(content_type: str, body: bytes) -> str | None:
    """Best-effort plain text from an upload, or ``None`` if not recoverable."""
    if content_type.startswith("text/"):
        return body.decode("utf-8", errors="ignore")
    if content_type == "application/pdf":
        try:
            import io

            import pdfplumber

            with pdfplumber.open(io.BytesIO(body)) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages)
        except Exception:  # missing dep or unreadable PDF -> manual review
            return None
    if content_type.startswith("image/"):
        try:
            import io

            import pytesseract
            from PIL import Image

            return str(pytesseract.image_to_string(Image.open(io.BytesIO(body))))
        except Exception:  # missing dep/binary or unreadable image -> manual review
            return None
    return None


def _find_aadhaar(text: str) -> str | None:
    m = _AADHAAR_RE.search(text)
    if not m:
        return None
    digits = re.sub(r"\s", "", m.group(1))
    return digits if len(digits) == 12 else None


def _find_pan(text: str) -> str | None:
    m = _PAN_RE.search(text.upper())
    return m.group(1) if m else None


def analyze(document_type: DocumentType, content_type: str, body: bytes) -> Analysis:
    """Extract what we can; decide the document's initial status."""
    text = _text_from(content_type, body)
    if text is None:
        # Nothing machine-readable — a human must check it.
        return Analysis(status=DocumentStatus.NEEDS_REVIEW, extracted={"text_found": False})

    aadhaar = _find_aadhaar(text)
    pan = _find_pan(text)
    extracted: dict[str, Any] = {"text_found": True}

    if document_type in _ID_TYPES:
        wanted = aadhaar if document_type == DocumentType.AADHAAR else pan
        status = DocumentStatus.EXTRACTED if wanted else DocumentStatus.NEEDS_REVIEW
    else:
        # Non-ID docs just need a human to verify; extraction is a bonus.
        status = DocumentStatus.EXTRACTED
    return Analysis(status=status, aadhaar=aadhaar, pan=pan, extracted=extracted)


def dump_extracted(extracted: dict[str, Any]) -> str:
    return json.dumps(extracted)


def storage_key(candidate_id: int, document_id: int, filename: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", filename)[-80:] or "file"
    return f"candidates/{candidate_id}/documents/{document_id}_{safe}"


def mask(value: str | None) -> str | None:
    """Mask all but the last four characters of an ID number."""
    if not value:
        return value
    tail = value[-4:]
    return f"{'•' * max(0, len(value) - 4)}{tail}"
