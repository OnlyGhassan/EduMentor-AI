import io
import PyPDF2
import docx
from fastapi import UploadFile

def extract_text_from_file(file: UploadFile) -> str:
    try:
        filename = (file.filename or "").lower()
        file.file.seek(0)

        if filename.endswith(".pdf"):
            reader = PyPDF2.PdfReader(file.file)
            return "\n".join([page.extract_text() or "" for page in reader.pages])

        if filename.endswith(".docx"):
            bio = io.BytesIO(file.file.read())
            d = docx.Document(bio)
            return "\n".join(p.text for p in d.paragraphs)

        if filename.endswith(".txt"):
            return file.file.read().decode("utf-8", errors="ignore")

        return ""
    except Exception:
        return ""
