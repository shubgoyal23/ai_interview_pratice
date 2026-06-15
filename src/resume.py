import re
from pathlib import Path

import pypdf

_EMAIL_RE = re.compile(r'[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}')
_PHONE_RE = re.compile(
    r'(?:\+?1[\s.-]?)?'        # optional country code
    r'(?:\(?\d{3}\)?[\s.-]?)'  # area code
    r'\d{3}[\s.-]?\d{4}'       # number
)


def redact_pii(text: str) -> str:
    text = _EMAIL_RE.sub('[email redacted]', text)
    text = _PHONE_RE.sub('[phone redacted]', text)
    return text


def parse_resume(pdf_path: Path) -> str:
    reader = pypdf.PdfReader(pdf_path)
    pages = [page.extract_text() or "" for page in reader.pages]
    raw = "\n".join(pages).strip()
    return redact_pii(raw)
