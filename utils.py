from shapely.geometry import LineString, Point

# def segment_lines(lines):
#     segmented_lines = []
#     for i in range(len(lines)):
#         for j in range(i + 1, len(lines)):
#             line1 = LineString([(lines[i]['x0'], lines[i]['y0']), (lines[i]['x1'], lines[i]['y1'])])
#             line2 = LineString([(lines[j]['x0'], lines[j]['y0']), (lines[j]['x1'], lines[j]['y1'])])
#             if line1.intersects(line2):
#                 intersection_point = line1.intersection(line2)
#                 if intersection_point.is_empty:
#                     continue
#                 intersection_coords = list(intersection_point.coords)[0]
#                 if lines[i]['orientation'] == 'h':
#                     new_line1 = {'x0': min(lines[i]['x0'], intersection_coords[0]),
#                                  'y0': lines[i]['y0'],
#                                  'x1': max(lines[i]['x1'], intersection_coords[0]),
#                                  'y1': lines[i]['y1'],
#                                  'orientation': 'h'}
#                     new_line2 = {'x0': min(lines[j]['x0'], intersection_coords[0]),
#                                  'y0': lines[j]['y0'],
#                                  'x1': max(lines[j]['x1'], intersection_coords[0]),
#                                  'y1': lines[j]['y1'],
#                                  'orientation': 'h'}
#                 else:
#                     new_line1 = {'x0': lines[i]['x0'],
#                                  'y0': min(lines[i]['y0'], intersection_coords[1]),
#                                  'x1': lines[i]['x1'],
#                                  'y1': max(lines[i]['y1'], intersection_coords[1]),
#                                  'orientation': 'v'}
#                     new_line2 = {'x0': lines[j]['x0'],
#                                  'y0': min(lines[j]['y0'], intersection_coords[1]),
#                                  'x1': lines[j]['x1'],
#                                  'y1': max(lines[j]['y1'], intersection_coords[1]),
#                                  'orientation': 'v'}
#                 segmented_lines.append(new_line1)
#                 segmented_lines.append(new_line2)
#             else:
#                 segmented_lines.append(lines[i])
#                 segmented_lines.append(lines[j])
#     return segmented_lines

def segment_lines(horizontal_lines, vertical_lines):
    segmented_horizontal_lines = []
    
    for h_line in horizontal_lines:
        h_segment = LineString([(h_line['x0'], h_line['y0']), (h_line['x1'], h_line['y1'])])
        start_x0 = h_line['x0']
        segments = []
        
        for v_line in vertical_lines:
            v_segment = LineString([(v_line['x0'], v_line['y0']), (v_line['x1'], v_line['y1'])])
            intersection = h_segment.intersection(v_segment)
            if intersection.is_empty:
                continue
                
            if isinstance(intersection, Point):
                segments.append({'x0': start_x0, 'y0': intersection.y,
                                 'x1': intersection.x, 'y1': intersection.y, 'orientation': 'h'})
                start_x0 = intersection.x
            # if isinstance(intersection, LineString):
            #     segments.append({'x0': intersection.coords[0][0], 'y0': intersection.coords[0][1], 
            #                      'x1': intersection.coords[1][0], 'y1': intersection.coords[1][1]})
            # elif isinstance(intersection, (tuple, list)):
            #     for i in range(len(intersection) - 1):
            #         segments.append({'x0': intersection[i][0], 'y0': intersection[i][1], 
            # 
            #                          'x1': intersection[i+1][0], 'y1': intersection[i+1][1]})

        if start_x0 != h_line['x1']:
            segments.append({'x0': start_x0, 'y0': h_line['y0'],
                             'x1': h_line['x1'], 'y1': h_line['y0'], 'orientation': 'h'})
        
        if len(segments) > 0:
            segmented_horizontal_lines.extend(segments)
        else:
            segmented_horizontal_lines.append(h_line)
    
    return segmented_horizontal_lines
