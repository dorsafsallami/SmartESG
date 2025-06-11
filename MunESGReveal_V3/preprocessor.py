# preprocessor.py
import os

import pytesseract
from pdf2image import convert_from_path
from PyPDF2 import PdfReader


class ReportPreprocessor:
    """
    Extrait le texte d'un fichier PDF.
    Utilise PyPDF2 pour extraire le texte numérique et effectue de l'OCR si nécessaire.
    """
    def __init__(self, ocr_language='fra'):
        self.ocr_language = ocr_language

    def extract_text_from_pdf(self, pdf_path):
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Fichier introuvable: {pdf_path}")
        reader = PdfReader(pdf_path)
        full_text = ""
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text and page_text.strip():
                full_text += page_text + "\n"
            else:
                images = convert_from_path(pdf_path, first_page=i+1, last_page=i+1, dpi=300)
                for img in images:
                    ocr_text = pytesseract.image_to_string(img, lang=self.ocr_language)
                    full_text += ocr_text + "\n"
        return full_text

    def build_knowledge_base(self, text_content):
        """
        Structure le texte extrait en une base de connaissances.
        """
        kb = {"full_text": text_content, "text_chunks": []}
        paragraphs = [p.strip() for p in text_content.split("\n\n") if p.strip()]
        kb["text_chunks"] = paragraphs
        return kb

    def process_report(self, pdf_path):
        text = self.extract_text_from_pdf(pdf_path)
        return self.build_knowledge_base(text)
