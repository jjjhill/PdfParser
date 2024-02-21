import pdfplumber
import pprint
from operator import itemgetter
from functools import cmp_to_key
import os

pp = pprint.PrettyPrinter(indent=4)

def curves_to_edges(cs):
    edges = []

    for c in cs:
        if ('y0' in c and 'y1' in c and 'x0' in c and 'x1' in c):
            edges += pdfplumber.utils.rect_to_edges(c)
    return edges

def get_horizontal_lines(page):
    horiz_lines = filter(lambda x: x['orientation'] == 'h' and "y0" in x, page.edges)
    by_y0 = pdfplumber.utils.clustering.cluster_objects(list(horiz_lines), itemgetter('y0'), 1)
    new_lines = []
    for cluster in by_y0:
        line = pdfplumber.utils.merge_bboxes(map(pdfplumber.utils.obj_to_bbox, cluster))
        new_lines.append(line)

    return new_lines

def extract_tables(pdf, page):
    p = pdf.pages[page]

    table_settings = {
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
        # "explicit_vertical_lines": curves_to_edges(p.curves + p.edges),
        # "explicit_horizontal_lines": curves_to_edges(p.curves + p.edges),
        "intersection_y_tolerance": 2,
        "snap_y_tolerance": 5,
    }
    
    img = p.to_image(resolution=400)
    img.debug_tablefinder(table_settings)
    img.save('debug.png')

    tables = p.extract_tables(table_settings)
    tables_bboxes = p.find_tables(table_settings)

    p1 = p.crop((0, 0, p.bbox[2]/2, p.bbox[3]))
    p2 = p.crop((p.bbox[2]/2, 0, p.bbox[2], p.bbox[3]))
    lines_p1 = get_horizontal_lines(p1)
    lines_p2 = get_horizontal_lines(p2)

    def contains_consecutive_horizontal_lines(lines, count):
        consecutive = 1
        prev_y_diff = None
        for i, line in enumerate(lines):
            if i == 0:
                continue
            y_diff = lines[i-1][1] - line[1]
            if y_diff < 50 and (prev_y_diff is None or abs(y_diff - prev_y_diff) < 1):
                consecutive += 1
                prev_y_diff = y_diff
            else:
                consecutive = 1
            if consecutive >= count:
                # print(f'At least {count} consecutive lines')
                return True
        
        # print('no consecutive lines')
        return False

    if len(tables) == 0 and (contains_consecutive_horizontal_lines(lines_p1, 3) or contains_consecutive_horizontal_lines(lines_p2, 3)):
        table_settings = {
            "vertical_strategy": "text_and_horizontal_line_vertices",
            "horizontal_strategy": "lines",
            "min_words_vertical": 5,
        }
        p1 = p.crop((0, 0, p.bbox[2]/2, p.bbox[3]))
        p2 = p.crop((p.bbox[2]/2, 0, p.bbox[2], p.bbox[3]))

        img = p1.to_image(resolution=400)
        img.debug_tablefinder(table_settings)
        img.save('debug.png')

        p1tables = p1.extract_tables(table_settings)
        p2tables = p2.extract_tables(table_settings)
        tables = p1tables + p2tables
        tables_bboxes = p1.find_tables(table_settings) + p2.find_tables(table_settings)

    
    def sort_tables(item1, item2):
        x_diff = item1[1].bbox[0] - item2[1].bbox[0]
        y_diff = item1[1].bbox[1] - item2[1].bbox[1]
        if abs(x_diff) < 10:
            return y_diff
        else:
            return x_diff
        
        
    
    tables_with_bboxes = tuple(zip(tables, tables_bboxes))
    sorted_items = sorted(tables_with_bboxes, key=cmp_to_key(sort_tables))
    sorted_tables = list(map(lambda x: x[0], sorted_items))
    sorted_bboxes = list(map(lambda x: x[1], sorted_items))

    # Get the bounding boxes of the tables on the page.
    bboxes = [table.bbox for table in sorted_bboxes]

    def not_within_bboxes(obj):
        def obj_in_bbox(_bbox):
            v_mid = (obj["top"] + obj["bottom"]) / 2
            h_mid = (obj["x0"] + obj["x1"]) / 2
            x0, top, x1, bottom = _bbox
            return (h_mid >= x0) and (h_mid < x1) and (v_mid >= top) and (v_mid < bottom)
        return not any(obj_in_bbox(__bbox) for __bbox in bboxes)

    text_outside_tables = p.filter(not_within_bboxes).extract_text(use_text_flow=True, x_tolerance=3).split('\n')

    return sorted_tables, text_outside_tables, bboxes
    
def extract_text(pdf, page):
    p = pdf.pages[page]
    text = p.extract_text(use_text_flow=True, x_tolerance=3)

    return text

def get_table_indexes(full_text, text_without_tables):
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

def list_to_table(list):
    def count_cells(row):
        count = 0
        for cell in row:
            if cell is not None:
                count += 1

        return count

    # Single column tables, treat as text
    output = []
    
    for row_index, row in enumerate(list):
        if count_cells(row) == 1:
            output.append(format_for_text_line(row[0]))
            continue
            
        elif count_cells(row) > 1 and row_index > 0 and count_cells(list[row_index - 1]) == 1:
            output.append('------------------------')

        if any(cell.strip() != '' for cell in list[row_index]):
            output.append(format_for_text_line((' | ').join(list[row_index]).replace('\n','<br>')))

    return ('\n').join(output)

def table_is_consecutive(bboxes, table_num):
    return abs(bboxes[table_num][0] - bboxes[table_num-1][0]) < 5 and bboxes[table_num][1] - bboxes[table_num-1][3] < 20

def format_for_text_line(line):
    return line.replace(' .','.').replace('(cid:129)', '•')

def main():
    directory = "input_files"  # Replace with the directory containing your PDF files
    output_directory = "output_files"  # Replace with the directory where you want to save the TXT files

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    for filename in os.listdir(directory):
        # try:
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(directory, filename)

            with pdfplumber.open(pdf_path) as pdf:
                for page_number in range(len(pdf.pages)):
                    print(f'parsing page {page_number} of {pdf_path}')
                    page_text_by_column = extract_text(pdf, page_number).split('\n')
                    page_tables, page_text_without_tables, table_bboxes = extract_tables(pdf, page_number)

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

                    txt_path = os.path.join(output_directory, os.path.splitext(filename)[0] + '-page' + str(page_number + 1) + ".txt")
                    with open(txt_path, 'w', encoding='utf-8') as file:
                        table_num = 0
                        for i, line in enumerate(text_lines_without_tables):
                            # insert formatted table into correct location
                            if (i in table_indexes):
                                file.write(list_to_table(page_tables[table_num]))
                                file.write('\n')
                                table_num += 1
                                while table_num < len(page_tables) and table_is_consecutive(table_bboxes, table_num):
                                    file.write('------------------------\n')
                                    file.write(list_to_table(page_tables[table_num]))
                                    file.write('\n')
                                    table_num += 1

                            file.write(format_for_text_line(line) + '\n')
                        
                        while table_num < len(page_tables):
                            file.write(list_to_table(page_tables[table_num]))
                            file.write('\n')
                            table_num += 1
        # except:
        #     print(f'SCRAPE FAILED ON FILE: {filename}')
        #     continue

if __name__ == "__main__":
    main()



