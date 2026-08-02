"""
rag/document_processor.py – Extract text from medical documents and split into chunks.
Supports PDF, DOCX, and TXT formats.
"""

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

CHUNK_SIZE    = 500   # characters per chunk
CHUNK_OVERLAP = 60    # overlapping chars between chunks


# ── Text Extraction ───────────────────────────────────────────────────────────

def extract_text_pdf(file_path: str) -> str:
    """Extract text from a PDF file using pdfplumber (primary) + PyMuPDF (fallback)."""
    text = ""
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
        if text.strip():
            logger.info("PDF extracted with pdfplumber: %s chars", len(text))
            return text
    except Exception as exc:
        logger.warning("pdfplumber failed (%s), trying PyMuPDF", exc)

    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
        logger.info("PDF extracted with PyMuPDF: %s chars", len(text))
    except Exception as exc:
        logger.error("PyMuPDF also failed: %s", exc)

    return text


def extract_text_docx(file_path: str) -> str:
    """Extract text from a DOCX file."""
    try:
        from docx import Document
        doc  = Document(file_path)
        text = "\n".join(para.text for para in doc.paragraphs if para.text.strip())
        logger.info("DOCX extracted: %s chars", len(text))
        return text
    except Exception as exc:
        logger.error("DOCX extraction failed: %s", exc)
        return ""


def extract_text_txt(file_path: str) -> str:
    """Read plain text file."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        logger.info("TXT read: %s chars", len(text))
        return text
    except Exception as exc:
        logger.error("TXT read failed: %s", exc)
        return ""


def extract_text(file_path: str) -> str:
    """Route to the right extractor based on file extension."""
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return extract_text_pdf(file_path)
    elif ext in (".docx", ".doc"):
        return extract_text_docx(file_path)
    elif ext in (".txt", ".text", ".md"):
        return extract_text_txt(file_path)
    else:
        logger.warning("Unsupported file type: %s", ext)
        return ""


# ── Cleaning ──────────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """Normalise whitespace and remove junk characters."""
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"[^\x20-\x7E\n\u00A0-\uFFFF]", " ", text)
    return text.strip()


# ── Chunking ──────────────────────────────────────────────────────────────────

def chunk_text(text: str, filename: str = "",
               chunk_size: int = CHUNK_SIZE,
               overlap: int = CHUNK_OVERLAP) -> list[dict]:
    """
    Split text into overlapping chunks with metadata.

    Returns a list of dicts::

        {"text": str, "source": str, "chunk_index": int}
    """
    text    = clean_text(text)
    chunks  = []
    start   = 0
    idx     = 0

    while start < len(text):
        end   = start + chunk_size
        chunk = text[start:end]

        # Try to break at sentence boundary
        if end < len(text):
            last_dot = chunk.rfind(". ")
            if last_dot > chunk_size // 2:
                chunk = chunk[: last_dot + 1]

        chunk = chunk.strip()
        if chunk:
            chunks.append({
                "text":        chunk,
                "source":      filename,
                "chunk_index": idx,
            })
            idx += 1

        start += len(chunk) - overlap if len(chunk) > overlap else len(chunk)

    logger.info("Chunked '%s' → %s chunks", filename, len(chunks))
    return chunks


# ── Main processing pipeline ──────────────────────────────────────────────────

def process_document(file_path: str, filename: str = "") -> list[dict]:
    """
    Full pipeline: extract → clean → chunk.
    Returns list of chunk dicts ready for embedding.
    """
    fname = filename or Path(file_path).name
    text  = extract_text(file_path)
    if not text.strip():
        logger.warning("No text extracted from: %s", fname)
        return []
    return chunk_text(text, fname)
