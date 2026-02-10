import pdfplumber
import requests
from io import BytesIO

def extract_pdf_text(pdf_url):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/pdf",
    }

    r = requests.get(pdf_url, headers=headers, timeout=10)
    r.raise_for_status()

    text = ""
    with pdfplumber.open(BytesIO(r.content)) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""

    return text.strip()

def clean_text(text, max_chars=12000):
    text = text.replace("\n", " ")
    text = " ".join(text.split())
    return text[:max_chars]

def gdf(url):
    cleaned_text=""
    try:
        text = extract_pdf_text(url)
        cleaned_text=clean_text(text)
    except:
        pass
    return cleaned_text
