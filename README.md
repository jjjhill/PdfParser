# PdfParser

## Install

`git clone git@github.com:jjjhill/PdfParser.git`
`cd PdfParser`
`python -m venv venv`

### Activate virtual environment

Windows: `venv\Scripts\activate`
Linux: `source venv/Scripts/activate`

`pip install -r requirements.txt`

## Download pdf files if needed

Open downloadPDFs.py and put the pdf links into the `pdf_urls` array

`py downloadPDFs.py`

## Scrape PDFs

Ensure all pdf files are in the `input_files` folder

Run script:
`py scrape.py`

## Correct PDFs with bad table parsing

- First make sure `scrape.py` was run on the PDFs, to generate approximate lines
- Put PDFs in `to_correct/` folder
- run `py correct_tables.py`

^ Library is open source: Client can fork it and maintain their own if needed. Here's my version that works with the script: https://github.com/jjjhill/pdfplumber. Its downloaded for using in the script, by installing `requirements.txt`.
