import asyncio
import tkinter as tk
from tkinter import Canvas, Frame, Button
from PIL import Image, ImageTk
import fitz
import pprint
from utils import segment_lines
from threading import Event, Thread
import queue

pp = pprint.PrettyPrinter(indent=4)

result_queue = queue.Queue()


lines = []
x0, y0, x1, y1 = 0, 0, 0, 0
mouse_moved = False
selected_line = None
deleted_lines = []

# {type: 'create' | 'delete', line: int}
user_events = []
submit_pressed = Event()

# Function to convert PDF to image
def pdf_to_image(pdf_path, page):
    doc = fitz.open(pdf_path)
    page = doc.load_page(page) # Get the page
    zoom = 1
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return image

current = None

# def submit():
#     # return lines list to the script that invoked the gui
#     return list

def draw_initial_lines(canvas, initial_lines):
    # print(len(initial_lines))
    formatted_lines = list(map(lambda line: { 'x0': line['x0'], 'x1': line['x1'], 'y0': line['top'], 'y1': line['top'] if line['orientation'] == 'h' else line['top'] + line['height'], 'orientation': line['orientation'] }, initial_lines))
    horizontal_lines = list(filter(lambda line: line['orientation'] == 'h', formatted_lines))
    vertical_lines = list(filter(lambda line: line['orientation'] == 'v', formatted_lines))
    segmented_horizontal_lines = segment_lines(horizontal_lines, vertical_lines)
    # print(segmented_horizontal_lines)
    segmented_initial_lines = vertical_lines + segmented_horizontal_lines
    # print(len(segmented_initial_lines))
    # Draw initial lines on the canvas
    print(f'lines before: {len(segmented_initial_lines)}')
    for line in segmented_initial_lines:
        drawn_line = canvas.create_line(line['x0'], line['y0'], line['x1'], line['y1'], fill="red")
        lines.append(drawn_line)
    
def run_tkinter_loop(pdf, page_number, initial_lines):
    global current, lines, submit_pressed, result_queue, selected_line, deleted_lines, user_events

    root = tk.Tk()
    
    current = None
    lines = []
    selected_line = None
    deleted_lines = []
    user_events = []
    # Convert PDF to image
    pdf_image = pdf_to_image(pdf.path, page_number)
    root.geometry(f'{pdf_image.width + 150}x{pdf_image.height}')

    # Convert PIL Image to PhotoImage
    photo = ImageTk.PhotoImage(pdf_image)

    canvas = Canvas(root, width=pdf_image.width, height=pdf_image.height + 100)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    canvas.create_image(0, 0, image=photo, anchor='nw')
    draw_initial_lines(canvas, initial_lines)

    def map_coord_to_dict(coord): 
        x0 = min([coord[0], coord[2]])
        y0 = min([coord[1], coord[3]])
        x1 = max([coord[0], coord[2]])
        y1 = max([coord[1], coord[3]])
        return {
            'x0': x0,
            'x1': x1,
            "object_type": "curve_edge",
            'top': y0,
            "doctop": y0,
            "bottom": y1,
            "width": abs(x1 - x0),
            "height": abs(y1 - y0),
            "orientation": "v" if x1 == x0 else ("h" if y1 == y0 else None),
        }

    def submit():
        min_line_length = 3
        line_coords = list(
            # filter(lambda line: not (line['orientation'] == 'h' and line['width'] < min_line_length) and not (line['orientation'] == 'v' and line['height'] < min_line_length),
            map(map_coord_to_dict
            ,map(lambda line: canvas.coords(line), lines)))
        result_queue.put(line_coords)
        submit_pressed.set()
        root.destroy()


    # Create a frame to hold the buttons
    button_frame = Frame(root)
    button_frame.pack(side=tk.RIGHT, fill=tk.Y)
    undo_button = Button(button_frame, text="Undo", command=lambda: undo(canvas))
    reset_button = Button(button_frame, text="Reset", command=lambda: reset(canvas, initial_lines))
    undo_button.pack(side=tk.TOP)
    reset_button.pack(side=tk.TOP)
    submit_button = Button(button_frame, text="Submit", command=submit)
    submit_button.pack(side=tk.TOP)

    # canvas.bind("<Escape>", lambda event: reset(canvas))
    canvas.bind("<Motion>", lambda event: motion(event, canvas))
    canvas.bind("<ButtonPress-1>", lambda event: Mousedown(event, canvas))
    canvas.bind("<ButtonRelease-1>", lambda event: Mouseup(event, canvas))
    canvas.bind("<Control-z>", lambda event: undo(canvas))
    canvas.bind("<Delete>", lambda event: delete_selected_line(canvas))

    root.mainloop()
    # Run the Tkinter event loop in a loop that checks for submit_pressed
    # while not submit_pressed == True:
    #     try:
    #         root.update()
    #     except tk.TclError:
    #         break

#NEW
async def edit(pdf, page_number, initial_lines):
    global result_queue, submit_pressed
    # Create a new thread to run the Tkinter event loop
    t = Thread(target=run_tkinter_loop, args=(pdf, page_number, initial_lines))
    t.start()

    submit_pressed.wait()
    submit_pressed.clear()
    # Wait for the result from the queue
    new_lines = result_queue.get()
    
    print(f'lines after: {len(new_lines)}')
    t.join()

    return new_lines


def remove_all_lines(canvas):
    global lines
    for line in lines:
        canvas.delete(line)
    lines.clear()

def reset(canvas, initial_lines):
    global current, selected_line, deleted_lines
    current = None
    selected_line = None
    remove_all_lines(canvas)
    draw_initial_lines(canvas, initial_lines)
    deleted_lines.clear()

def undo(canvas):
    global selected_line, deleted_lines, user_events

    if len(user_events) > 0:
        last_event = user_events.pop()
        print(last_event)
        if last_event['type'] == 'create':
            # print('created')
            # Remove the last line drawn from the canvas
            lines.pop()
            canvas.delete(last_event['line'])
        elif last_event['type'] == 'delete':
            # print('deleted')
            # last_deleted = deleted_lines.pop()
            coords = last_event['line']['coords']
            drawn_line = canvas.create_line(coords[0], coords[1], coords[2], coords[3], fill="red")
            lines.append(drawn_line)

def Mousedown(event, canvas):
    global current, mouse_moved, x0, y0
    mouse_moved = False
    event.widget.focus_set() # so escape key will work
    if current is None:
        # the new line starts where the user clicked
        x0 = event.x
        y0 = event.y

def motion(event, canvas):
    global current, mouse_moved, x0, y0
    if x0 > 0 and y0 > 0:
        # Get the current line's start coordinates
        # coords = event.widget.coords(current)
        # x0, y0 = coords[0], coords[1]

        # Calculate the difference between the start and current mouse positions
        dx = event.x - x0
        dy = event.y - y0

        #line
        if abs(dx) + abs(dy) > 5:
            mouse_moved = True
            if current is None:
                current = event.widget.create_line(x0, y0, event.x, event.y, fill="red")

            # Determine if the line should be vertical or horizontal
            if abs(dx) > abs(dy):
                # If the horizontal distance is greater, make the line horizontal
                event.widget.coords(current, x0, y0, event.x, y0)
            else:
                # If the vertical distance is greater, make the line vertical
                event.widget.coords(current, x0, y0, x0, event.y)
        #click
        else:
            mouse_moved = False

def Mouseup(event, canvas):
    global current, selected_line, user_events, mouse_moved, x0, y0
    if mouse_moved and current:
        print('moved')
        lines.append(current)
        
        user_events.append({
            'type': 'create',
            'line': current
        })
    else:
        print('click')
        # Find the closest line item
        closest_lines = canvas.find_closest(event.x, event.y, 2)
        closest_line = closest_lines[0]
        # Select the line if it exists in the lines list
        if selected_line is not None:
            canvas.itemconfig(selected_line, fill="red") # Change color to indicate selection 
        # print(lines)
        if closest_line in lines:
            selected_line = closest_line
            canvas.itemconfig(selected_line, fill="blue") # Change color to indicate selection

    mouse_moved = False

    # Finalize the line when the mouse button is released
    current = None
    x0, y0 = 0, 0

def delete_selected_line(canvas):
    global selected_line, deleted_lines, user_events
    if selected_line:
        lines.remove(selected_line)
        deleted_lines.append(selected_line)
        user_events.append({
            'type': 'delete',
            'line': {
                'id': selected_line,
                'coords': canvas.coords(selected_line)
            }
        })
        canvas.delete(selected_line)
        selected_line = None



