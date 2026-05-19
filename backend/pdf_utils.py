import pdfplumber
from io import BytesIO


def extract_text_from_pdf(file_bytes: bytes) -> str:
    text_parts = []
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text.strip())
    return "\n\n".join(text_parts)


def extract_text_from_multiple(files: list[tuple[str, bytes]]) -> str:
    combined = []
    for filename, file_bytes in files:
        try:
            text = extract_text_from_pdf(file_bytes)
            if text.strip():
                combined.append(f"--- {filename} ---\n{text}")
        except Exception as e:
            combined.append(f"--- {filename} (extraction failed: {e}) ---")
    return "\n\n".join(combined)
