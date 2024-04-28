import pdfplumber
import pprint
from operator import itemgetter
from functools import cmp_to_key
import os
import traceback
import json
from pdfplumber.table import snap_edges

pp = pprint.PrettyPrinter(indent=4)

# directory = "input_files" 
directory = "test_input_files/current/current" 
output_directory = "output_files"
corrected_directory = "output_files/corrected"
edges_directory = "table_edges"

if not os.path.exists(output_directory):
    os.makedirs(output_directory)
if not os.path.exists(corrected_directory):
    os.makedirs(corrected_directory)
if not os.path.exists(edges_directory):
    os.makedirs(edges_directory)


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
    for y0_cluster in by_y0:
        by_x0 = pdfplumber.utils.clustering.cluster_objects(list(y0_cluster), itemgetter('x0'), 3)
        for x0_cluster in by_x0:
            objects = pdfplumber.utils.geometry.snap_objects(x0_cluster, 'top', 2)
            new_lines.append(objects[0])
            # for object in objects:
            # line = pdfplumber.utils.merge_bboxes(map(pdfplumber.utils.obj_to_bbox, x0_cluster))
            # new_lines.append({
            #     "object_type": "line",
            #     "top": line[1],
            #     "x0": line[0],
            #     "x1": line[2],
            #     "width": line[2] - line[0],
            #     "orientation": "h",
            # })

    return new_lines

def extend_bbox(bbox, value):
    return (bbox[0] - value, bbox[1] - value, bbox[2] + value, bbox[3] + value)


def contains_consecutive_horizontal_lines(line_clusters_by_x0, count):
    for j, cluster in enumerate(line_clusters_by_x0):
        consecutive = 1
        prev_y_diff = None
        prev_width = None
        for i, line in enumerate(cluster):
            if i == 0:
                continue
            y_diff = float(abs(cluster[i-1]['top'] - line['top']))
            if y_diff < 50 and y_diff > 6 and (prev_y_diff is None or abs(y_diff - prev_y_diff) < 3):
                consecutive += 1
            else:
                consecutive = 1
            prev_y_diff = y_diff

            if prev_width is not None and abs(line['width'] - prev_width) > 6:
                consecutive = 1

            prev_width = line['width']
            if consecutive >= count:
                print(f'At least {count} consecutive lines')
                return True
    
    # print('no consecutive lines')
    return False

def get_lines_outside_tables(page_horiz_lines, tables_bboxes):
    # pp.pprint(page_horiz_lines)
    # pp.pprint(tables_bboxes[0].bbox)
    outside_lines = []

    for line in page_horiz_lines:
        if all(pdfplumber.utils.geometry.get_bbox_overlap(pdfplumber.utils.geometry.obj_to_bbox(line), extend_bbox(table_bbox.bbox, 1)) is None for table_bbox in tables_bboxes):
            outside_lines.append(line)

    return outside_lines


def not_within_bboxes(obj, bboxes):
    def obj_in_bbox(_bbox):
        v_mid = (obj["top"] + obj["bottom"]) / 2
        h_mid = (obj["x0"] + obj["x1"]) / 2
        x0, top, x1, bottom = _bbox
        return (h_mid >= x0) and (h_mid < x1) and (v_mid >= top) and (v_mid < bottom)
    return not any(obj_in_bbox(__bbox) for __bbox in bboxes)

def sort_tables(item1, item2):
    x_diff = item1[1].bbox[0] - item2[1].bbox[0]
    y_diff = item1[1].bbox[1] - item2[1].bbox[1]
    if abs(x_diff) < 10:
        return y_diff
    else:
        return x_diff
    
    
# this does not yet account for tables with no lines
def predict_open_table_exists(lines_outside_tables):
    by_top = pdfplumber.utils.clustering.cluster_objects(lines_outside_tables, itemgetter('top'), 3)
    merged_lines = []
    for cluster in by_top:
        lines_in_row = pdfplumber.utils.geometry.merge_edges(cluster)
        merged_lines = merged_lines + lines_in_row
    
    by_x0 = pdfplumber.utils.clustering.cluster_objects(merged_lines, itemgetter('x0'), 5)
    
    return contains_consecutive_horizontal_lines(by_x0, 3)
   

def extract_tables(pdf, page, explicit_lines=[], write_edges=None):
    p = pdf.pages[page]
    merged_edges = snap_edges(
        explicit_lines,
        x_tolerance=5,
        y_tolerance=5,
    )

    if explicit_lines and len(explicit_lines) > 1:
        table_settings = {
            "vertical_strategy": "explicit",
            "horizontal_strategy": "explicit",
            "explicit_vertical_lines": merged_edges,
            "explicit_horizontal_lines": merged_edges,
            "intersection_x_tolerance": 12,
            "intersection_y_tolerance": 8,
            "join_y_tolerance": 5,
            "snap_y_tolerance": 4,
            "snap_x_tolerance": 4,
            "text_vertical_ttb": False,
            "min_columns": 2,
        }
    else:
        table_settings = {
            "explicit_vertical_lines": p.edges,
            "explicit_horizontal_lines": p.edges,
            "intersection_y_tolerance": 3,
            "snap_y_tolerance": 5,
            "text_vertical_ttb": False,
            "min_columns": 2,
        }
    print('table strategy 1 used')
    
    img = p.to_image(resolution=400)
    img.draw_lines(list(map(lambda line: ((line['x0'], line['top']), (line['x1'], line['bottom'])), merged_edges)), stroke_width=6)
    img.save('lines.png')
    
    img = p.to_image(resolution=400)
    img.debug_tablefinder(table_settings)
    img.save('debug.png')

    tables = p.extract_tables(table_settings)
    tables_bboxes, edges = p.find_tables(table_settings)
    page_horiz_lines = get_horizontal_lines(p)
            

    # if there are consecutive horizontal lines outside of the current tables,
    # then there's probably more undetected tables
    lines_outside_tables = get_lines_outside_tables(page_horiz_lines, tables_bboxes)
    

    if len(tables) > 0:
        if write_edges is not None:
            write_edges(edges)

    elif len(tables) == 0 and predict_open_table_exists(lines_outside_tables):
        table_settings = {
            "vertical_strategy": "text_and_horizontal_line_vertices",
            "horizontal_strategy": "lines",
            "min_words_vertical": 5,
        }
        print('table strategy 2 used')

        img = p.to_image(resolution=400)
        img.debug_tablefinder(table_settings)
        img.save('debug.png')

        tables = p.extract_tables(table_settings)
        tables_bboxes, edges = p.find_tables(table_settings)
        if write_edges is not None:
            write_edges(edges)

    elif len(tables) == 0 and not predict_open_table_exists(lines_outside_tables):
        table_settings = {
            "vertical_strategy": "text",
            "horizontal_strategy": "text",
            "min_words_vertical": 7,
        }
        print('table strategy 3 used to extract possible edges')
        
        possible_tables_bboxes, possible_edges = p.find_tables(table_settings)
        if write_edges is not None:
            write_edges(possible_edges)
    
    tables_with_bboxes = tuple(zip(tables, tables_bboxes))
    sorted_items = sorted(tables_with_bboxes, key=cmp_to_key(sort_tables))
    sorted_tables = list(map(lambda x: x[0], sorted_items))
    sorted_bboxes = list(map(lambda x: x[1], sorted_items))

    # Get the bounding boxes of the tables on the page.
    bboxes = [table.bbox for table in sorted_bboxes]

    text_outside_tables = p.filter(lambda obj: not_within_bboxes(obj, bboxes)).extract_text(use_text_flow=True, x_tolerance=3).split('\n')
    text_outside_tables_boxes = p.filter(lambda obj: not_within_bboxes(obj, bboxes)).extract_words(use_text_flow=True, x_tolerance=3)
    return sorted_tables, text_outside_tables, bboxes, text_outside_tables_boxes, edges
    
def extract_text(pdf, page):
    p = pdf.pages[page]
    text = p.extract_text(use_text_flow=True, x_tolerance=3)
    print(text)
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

def list_to_text_file_table(list):
    def count_cells(row):
        count = 0
        for cell in row:
            if cell is not None and cell.strip() != '':
                count += 1

        return count
    
    def is_title_row(row):
        return count_cells(row) == 1 and row[0] is not None and row[0].strip() != ''

    # Single column tables, treat as text
    output = []
    
    for row_index, row in enumerate(list):
        if is_title_row(row):
            output.append(format_for_text_line(row[0]))

            if row_index < len(list) - 1 and not is_title_row(list[row_index + 1]):
                output.append('------------------------')

        elif any(cell.strip() != '' for cell in list[row_index]):
            output.append(format_for_text_line((' | ').join(list[row_index]).replace('\n','<br>')))

    return ('\n').join(output)

def table_is_consecutive(bboxes, table_num, text_bboxes_outside_tables):
    # check if theres any text between the table and the previous table
    for word in text_bboxes_outside_tables:
        # text = word['text']
        x0 = word['x0']
        y0 = word['top']
        curr_table_x0 = bboxes[table_num][0]
        curr_table_x1 = bboxes[table_num][2]
        prev_table_x0 = bboxes[table_num-1][0]
        prev_table_x1 = bboxes[table_num-1][2]
        curr_table_y0 = bboxes[table_num][1]
        prev_table_y1 = bboxes[table_num-1][3]

        if y0 > prev_table_y1 and y0 < curr_table_y0:
            # Word found between tables
            if x0 >= curr_table_x0 and x0 <= curr_table_x1:
                # its not on the other column in a 2 column page
                return False
            
        if prev_table_y1 > curr_table_y0:
            #new table on 2nd column
            if y0 > prev_table_y1 and x0 >= prev_table_x0 and x0 <= prev_table_x1:
                # text is after previous table and within same column as it
                return False
            
    return True

def format_for_text_line(line):
    return line.replace(' .','.').replace('(cid:129)', '•').replace('\ufffd', '.')

def write_edges(json_edges_path, edges):
    with open(json_edges_path, 'w', encoding='utf-8') as file:
        json.dump(edges, file, indent=4)

def scrape_page(pdf, filename, page_number, new_lines=[], output_dir=output_directory):
    print(f'parsing page {page_number} of {pdf.path}')

    json_edges_path = os.path.join(edges_directory, os.path.splitext(filename)[0] + '-page' + str(page_number + 1) + ".json")

    page_text_by_column = extract_text(pdf, page_number).split('\n')
    page_tables, page_text_without_tables, table_bboxes, text_outside_tables_boxes, edges = extract_tables(pdf, page_number, new_lines, lambda edges: write_edges(json_edges_path, edges))

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
    txt_path = os.path.join(output_dir, os.path.splitext(filename)[0] + '-page' + str(page_number + 1) + ".txt")
    # print('tableidx')
    # print(table_indexes)

    # pp.pprint(page_tables[-1])
    with open(txt_path, 'w', encoding='utf-8') as file:
        table_num = 0
        for i, line in enumerate(text_lines_without_tables):
            # print(i)
            # print(line)
            # insert formatted table into correct location
            if i in table_indexes:
                # print('INSERT TABLE')
                file.write(list_to_text_file_table(page_tables[table_num]))
                file.write('\n')
                table_num += 1
                while table_num < len(page_tables) and table_is_consecutive(table_bboxes, table_num, text_outside_tables_boxes):
                    file.write('------------------------\n')
                    file.write(list_to_text_file_table(page_tables[table_num]))
                    file.write('\n')
                    table_num += 1

            file.write(format_for_text_line(line) + '\n')
        
        while table_num < len(page_tables):
            file.write(list_to_text_file_table(page_tables[table_num]))
            file.write('\n')
            table_num += 1

    # write_edges(json_edges_path, edges)

def main():
    for filename in os.listdir(directory):
        try:
            if filename.endswith(".pdf"):
                pdf_path = os.path.join(directory, filename)

                with pdfplumber.open(pdf_path) as pdf:
                    for page_number in range(len(pdf.pages)):
                        scrape_page(pdf, filename, page_number)

        except Exception as error:
            print(f'SCRAPE FAILED ON FILE: {filename}')
            print(error)
            traceback.print_exc()
            
            continue

if __name__ == "__main__":
    main()



