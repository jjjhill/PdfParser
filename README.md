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




LATEST FROM CLIENT:
Yes parser works fine and we start using it, and found more problems on different PDF files. These files from other manufacturer and we want to continue with you contract. We have two options:
1. Try to update existing parser to support new file formats. It's best for us
2. add parameters to parser and based on PDF source we can use different params for parser. For example corteva* -> one parser params, syngenta3 -> another parser params

Here's list of problems:
1. Problems with missing text. I think problem in text_lines_without_tables. is it possible to work only based on bboxes? For example in file corteva5-super-bad.pdf missing entire "Table 2" and content of result text file is very short. It's very dangerous and important to do not miss any data.
2. Problem in special symbols. For example in file corteva5-super-bad.pdf we have 0�018 instead of 0.018
3. Tables with line borders. see file corteva8-table-without-borders.pdf
4. Tables without borders. see file corteva6-wrong-positions. It's not big problem. if it's hard we can leave it as is
5. Do not repeat cell's content if there is only one cell in row. For example in file syngenta1-do-not-repeat.pdf we have cell USE RESTRICTIONS and if possible better to do not repeat it
6. Problem with table parsing. files syngenta2-wrong-table.pdf, syngenta3-wrong-table.pdf, syngenta4-wrong-table.pdf

Also maybe it will be simple to copy (fork) library to same repo and have it near your script as module? i think you are making a lot of changes in library and i don't think they are goindg to merge it to main repo. In that case if will be easy to send code back to us and us to maintenant it in the future. 

^ Library is open source: Client can fork it and maintain their own if needed. Here's my version that works with the script: https://github.com/jjjhill/pdfplumber. Its downloaded for using in the script, by installing `requirements.txt`.