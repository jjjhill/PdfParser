import pdfplumber

with pdfplumber.open("files/ldAK6023.pdf") as pdf:
    first_page = pdf.pages[1]
    text = first_page.extract_text()
    tables = first_page.extract_tables()
    print(text)
    print("\n\n")
    print(tables[0])