#loop through to_correct/ directory
#for each file, loop through each page
#for each page, take edges from table_edges directory
#invoke edit.py and pass the initial edges
#output of edit is the new edges
#scrape pdf with new explicit edges

import os
import pdfplumber
import json
import pprint
from edit import edit 
import asyncio
from scrape import scrape_page

pp = pprint.PrettyPrinter(indent=4)

directory = "to_correct/" 
edges_directory = "table_edges"

async def main():
    for filename in os.listdir(directory):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(directory, filename)

            with pdfplumber.open(pdf_path) as pdf:
                for page_number in range(len(pdf.pages)):
                    edges_file = os.path.join(edges_directory, os.path.splitext(filename)[0] + '-page' + str(page_number + 1) + ".json")
                    with open(edges_file, "r") as json_file:
                        initial_edges = json.load(json_file)
                        # pp.pprint(initial_edges)
                        
                        new_lines = await edit(pdf, page_number, initial_edges)
                        scrape_page(pdf, filename, page_number, new_lines)


asyncio.run(main())
