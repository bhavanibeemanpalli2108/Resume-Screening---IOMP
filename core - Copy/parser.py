import pdfplumber
from docx import Document

def extract_text_from_pdf(file):
    text = ""

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            words = page.extract_words()
            words_sorted = sorted(words, key=lambda w: (round(w['top'], 1), w['x0']))

            current_line = []
            last_top = None

            for word in words_sorted:
                if last_top is None:
                    last_top = word['top']

                if abs(word['top'] - last_top) < 5:
                    current_line.append(word['text'])
                else:
                    text += " ".join(current_line) + "\n"
                    current_line = [word['text']]
                    last_top = word['top']

            text += " ".join(current_line) + "\n"

    return text


def extract_text_from_docx(file):
    document = Document(file)
    return "\n".join([para.text for para in document.paragraphs])


def parse_resume(uploaded_file):
    if uploaded_file.name.endswith(".pdf"):
        return extract_text_from_pdf(uploaded_file)
    elif uploaded_file.name.endswith(".docx"):
        return extract_text_from_docx(uploaded_file)
    else:
        return None