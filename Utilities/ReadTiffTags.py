import tifffile
from tkinter import filedialog
import tkinter as tk
from tkinter import ttk
import textwrap

"""
Simple script to read TIFF tags and display them in a tkinter window.
Run this with the commandline and a file dialog window will pop up.

Note: XML parts are broken into pieces (rows), which are themselves broken
if still longer than specified "max_char_len" value.

Requirements
------------
tifffile (comes with Aivia installer)
tkinter (needs the standard version of python)
textwrap

"""

max_char_len = 150

def run(params):
    # Retrieve file
    root = tk.Tk()
    root.withdraw()
    img_path = filedialog.askopenfilename(title='Select TIF file to read tags',
                                          filetype=[('TIF files', '.tif .tiff')])

    # Read tags
    with tifffile.TiffFile(img_path) as tif:
        tif_tags = {}
        for tag in tif.pages[0].tags.values():
            name, value = tag.name, tag.value
            tif_tags[name] = value
            print(name, ': ', value)

    # Display tags in table
    master = tk.Tk()
    master.bind('<Escape>', lambda e: master.quit())     # Press Esc to stop mainloop
    tk.Label(master, text="Tiff Tags", font=("Arial", 14)).grid(row=0, column=0)
    tk.Label(master, text="press Esc to close window", font=("Arial", 8)).grid(row=1, column=0)
    cols = ('Tag name', 'Value')
    tree = ttk.Treeview(master, columns=cols, show='headings')
    for col in cols:
        tree.heading(col, text=col)
    tree.grid(row=2, column=0)
    for tag_name, tag_val in tif_tags.items():
        final_val = str(tag_val)
        if len(final_val) > max_char_len:
            final_val_list = final_val.split('<')
            for v in range(0, len(final_val_list)):
                stri = final_val_list[v]
                if len(stri) > 0:
                    if len(final_val_list) > 1:
                        stri = '<' + stri
                    if len(stri) < max_char_len:
                        tree.insert("", "end", values=(tag_name, stri))
                    else:
                        final_val_list2 = [stri[i:i + max_char_len] for i in range(0, len(stri), max_char_len)]
                        for w in range(0, len(final_val_list2)):
                            tree.insert("", "end", values=(tag_name, final_val_list2[w]))

        else:
            tree.insert("", "end", values=(tag_name, final_val))
    tree.column(cols[1], width=1000, stretch=tk.YES)

    master.mainloop()


def wrap(string, lenght):
    return '\n'.join(textwrap.wrap(string, lenght))


if __name__ == '__main__':
    params = {}
    run(params)
