from PyPDF2 import PdfReader
import docx
import re
import unicodedata

def extract_text_from_pdf(fpath_or_fileobj):
    try:
        reader = PdfReader(fpath_or_fileobj)
        return "\n".join([p.extract_text() or "" for p in reader.pages])
    except Exception:
        return ""

def extract_text_from_docx(fpath_or_fileobj):
    try:
        doc = docx.Document(fpath_or_fileobj)
        return "\n".join([p.text for p in doc.paragraphs])
    except Exception:
        return ""


def sanitize_text(text: str) -> str:
    """Clean extracted text: remove control characters, normalize whitespace,
    and replace non-printable characters with a placeholder or space.
    This helps when PDF extraction returns garbled binary-like output.
    """
    if not text:
        return ""
    # Normalize unicode to NFC
    text = unicodedata.normalize("NFC", text)
    # Remove C0 control characters except newline and tab
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]+", "", text)
    # Replace any remaining non-printable (rare) with a space
    text = "".join(ch if (ch.isprintable() or ch in "\n\t") else " " for ch in text)
    # Normalize repeated whitespace to single space, preserve paragraphs
    text = re.sub(r"[ \t]+", " ", text)
    # Trim spaces on each line
    lines = [ln.strip() for ln in text.splitlines()]
    # Remove empty leading/trailing lines
    while lines and lines[0] == "":
        lines.pop(0)
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)
