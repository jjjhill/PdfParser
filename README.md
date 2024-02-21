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