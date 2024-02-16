import pdfquery

pdf = pdfquery.PDFQuery('files/ldAK6023.pdf')
pdf.load()

# page = pdf.get_page(1)
page = pdf.extract()
print(page)