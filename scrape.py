# from pypdf import PdfReader
import pdfplumber
import pprint
from prettytable import PrettyTable
import copy

pp = pprint.PrettyPrinter(indent=4)

def curves_to_edges(cs):
    edges = []

    for c in cs:
        if ('y0' in c and 'y1' in c and 'x0' in c and 'x1' in c):
            edges += pdfplumber.utils.rect_to_edges(c)
    return edges

def extract_tables(path, page):
    with pdfplumber.open(path) as pdf:
        p = pdf.pages[page]

        # Table settings.
        ts = {
            "vertical_strategy": "explicit",
            "horizontal_strategy": "explicit",
            "explicit_vertical_lines": curves_to_edges(p.curves + p.edges),
            "explicit_horizontal_lines": curves_to_edges(p.curves + p.edges),
            "intersection_y_tolerance": 10,
        }

        # Get the bounding boxes of the tables on the page.
        bboxes = [table.bbox for table in p.find_tables(
            table_settings=ts
        )]

        def not_within_bboxes(obj):
            def obj_in_bbox(_bbox):
                v_mid = (obj["top"] + obj["bottom"]) / 2
                h_mid = (obj["x0"] + obj["x1"]) / 2
                x0, top, x1, bottom = _bbox
                return (h_mid >= x0) and (h_mid < x1) and (v_mid >= top) and (v_mid < bottom)
            return not any(obj_in_bbox(__bbox) for __bbox in bboxes)

        text_outside_tables = p.filter(not_within_bboxes).extract_text(use_text_flow=True).split('\n')
        tables = p.extract_tables()
        table_positions = p.find_tables()
        word_positions = p.extract_words()

        return tables, text_outside_tables, word_positions, table_positions

# def extract_text(path, page):
#     with open(path, 'rb') as file:
#         reader = PdfReader(file)
#         page_text = reader.pages[page].extract_text()

#         return page_text
    
def extract_text(path, page):
    with pdfplumber.open(path) as pdf:
        p = pdf.pages[page]
        text = p.extract_text(use_text_flow=True)

        return text

# Tables: Table[]
# Table: Row[]
# Row: Cell[]
# Cell: string | None
def part_of_table(text, tables, table_positions):
    stripped_text = text.strip()

    for i, table in enumerate(tables):
        for row in table:
            row_text = ''.join(filter(lambda x: x is not None, row))

            if stripped_text in row_text:
                return table_positions[i]
            
    return None

def part_of_document(text, page_text_without_tables):
    # pp.pprint(text + '\n')
    # pp.pprint(page_text_without_tables)

    if text in page_text_without_tables:
        return 

    return text

def get_table_indexes(full_text, text_without_tables):
    # pp.pprint(full_text)
    # print('\n')
    # pp.pprint(text_without_tables)
    missing_indices = []
    i = 0
    j = 0
    while i < len(text_without_tables):
        current_line = text_without_tables[i]
        if i == len(text_without_tables) - 1 and j < len(full_text) - 1:
            missing_indices.append(i + 1)
            break
        elif j < len(full_text) and full_text[j] != current_line:
            missing_indices.append(i)

            while j < len(full_text) and full_text[j] != current_line:
                j += 1
        else:
            i += 1
            j += 1

    return missing_indices

def list_to_table(original_list):

    # Single column tables, treat as text
    text_output = ''
    if len(original_list[0]) == 1:
        for row in original_list:
            text_output += row[0].replace('\n', '<br>') + '\n'
        return text_output

    list = copy.deepcopy(original_list)
    
    for row_index, row in enumerate(original_list):
        for cell_index, cell in enumerate(row):
            if (cell is None):
                if row_index == 0 and cell_index == 0:
                    list[row_index][cell_index] = ''
                elif row_index == 0:
                    list[row_index][cell_index] = row[cell_index - 1]
                elif cell_index == 0:
                    list[row_index][cell_index] = list[row_index - 1][cell_index]
                else:
                    left_cell = row[cell_index - 1]
                    up_cell = list[row_index - 1][cell_index]
                    # row merge, get from left
                    if up_cell is None or left_cell[2] >= up_cell[2]:
                        list[row_index][cell_index] = left_cell
                    # column merge, get from above
                    elif left_cell is None or up_cell[3] >= left_cell[3]:
                        list[row_index][cell_index] = up_cell
                    else:
                        list[row_index][cell_index] = ''

    seen = {}
    headers = []
    if len(set(list[0])) != len(list[0]):
        for field in list[0]:
            if field in seen:
                headers.append(field + ' ')
                seen[field + ' '] = True
            else:
                headers.append(field)
                seen[field] = True
    else:
        headers = list[0]

    pt = PrettyTable()
    pt.field_names = headers
    pt.add_rows(list[1:None])

    return str(pt)



page_number = 1
pdf_path = 'files/ldAK6023.pdf'  # Replace 'example.pdf' with the path to your PDF file
page_text_by_column = extract_text(pdf_path, page_number).split('\n')
page_tables, page_text_without_tables, word_positions, table_positions = extract_tables(pdf_path, page_number)

try:
    page_number_test = int(page_text_by_column[0])
    ## if the page starts with page number ( if not, next line will throw )
    page_number_test + 1
    text_lines = page_text_by_column[1:None]
    text_lines_without_tables = page_text_without_tables[1:None]
except:
    text_lines = page_text_by_column
    text_lines_without_tables = page_text_without_tables

table_indexes = get_table_indexes(text_lines, text_lines_without_tables)

pp.pprint(table_indexes)

with open('output.txt', 'w') as file:
    table_num = 0
    for i, line in enumerate(text_lines_without_tables):
        # print(page_tables[table_num])
        if (i in table_indexes):
            file.write(list_to_table(page_tables[table_num]))
            file.write('\n')
            table_num += 1
        else:
            file.write(line + '\n')
    
    while table_num < len(page_tables):
        file.write(list_to_table(page_tables[table_num]))
        file.write('\n')
        table_num += 1




# pp.pprint(text_order)

# pp.pprint('\n\n')
# pp.pprint('table_positions')
# pp.pprint(table_positions)
# pp.pprint('\n\n')
# pp.pprint('word_positions')
# pp.pprint(word_positions)
# pp.pprint('\n\n')
# pp.pprint('page_tables')
# pp.pprint(page_tables)
# pp.pprint('\n\n')
