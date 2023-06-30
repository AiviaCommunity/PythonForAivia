# -------- Activate virtual environment -------------------------
import os
import ctypes
import sys
from pathlib import Path

def search_activation_path():
    for i in range(5):
        final_path = str(Path(__file__).parents[i]) + '\\env\\Scripts\\activate_this.py'
        if os.path.exists(final_path):
            return final_path
    return ''

activate_path = search_activation_path()
if os.path.exists(activate_path):
    exec(open(activate_path).read(), {'__file__': activate_path})
    print(f'Aivia virtual environment activated\nUsing python: {activate_path}')
else:
    error_mess = f'Error: {activate_path} was not found.\n\nPlease check that:\n' \
                 f'   1/ The \'FirstTimeSetup.py\' script was already run in Aivia,\n' \
                 f'   2/ The current python recipe is in one of the "\\PythonEnvForAivia\\" subfolders.'
    ctypes.windll.user32.MessageBoxW(0, error_mess, 'Error', 0)
    sys.exit(error_mess)
# ---------------------------------------------------------------

import tifffile
import wx
import textwrap

max_char_len = 150


# [INPUT Name:inputImagePath Type:string DisplayName:'Any channel']
# [OUTPUT Name:resultPath Type:string DisplayName:'Dummy to delete']
def run(params):
    # Choose file
    img_path = pick_file('')

    # Read tags
    with tifffile.TiffFile(img_path[0]) as tif:
        tif_tags = {}
        for tag in tif.pages[0].tags.values():
            name, value = tag.name, tag.value
            tif_tags[name] = value
            print(name, ': ', value)

    # Display tags in table, preparing table
    app = wx.App()
    frame = wx.Frame(parent=None, title='TIF tags', size=(1000, 800))
    # table = grid.Grid(frame)
    # table.CreateGrid(len(tif_tags) + 1, 2)
    table = wx.ListCtrl(frame, size=(-1, 100), style=wx.LC_REPORT)
    table.InsertColumn(0, 'Tag name', width=200)
    table.InsertColumn(1, 'Value', width=800)

    # Insert values
    i = 0
    for tag_name, tag_val in tif_tags.items():
        # Insert tag name
        table.InsertItem(i, tag_name)

        # Set value because some can be very long
        final_val = str(tag_val)

        # Replace returns
        final_val = final_val.replace('\n', '_')

        if len(final_val) > max_char_len:
            final_val_list = final_val.split('<')
            for v in range(0, len(final_val_list)):
                i += 1
                table.InsertItem(i, tag_name)
                stri = final_val_list[v]
                if len(stri) > 0:
                    if len(final_val_list) > 1:
                        stri = '<' + stri
                    if len(stri) < max_char_len:
                        table.SetItem(i, 1, stri)
                    else:
                        final_val_list2 = [stri[i:i + max_char_len] for i in range(0, len(stri), max_char_len)]
                        for w in range(0, len(final_val_list2)):
                            i += 1
                            table.InsertItem(i, tag_name)
                            table.SetItem(i, 1, final_val_list2[w])
        else:
            table.SetItem(i, 1, final_val)

        i += 1

    frame.Show()
    app.MainLoop()


def wrap(string, length):
    return '\n'.join(textwrap.wrap(string, length))


def pick_file(default_dir):
    print('Starting wxPython app')
    app = wx.App()

    # Create open file dialog
    openFileDialog = wx.FileDialog(None, "Select an image",
                                   default_dir, "", "Image files (*.tif)|*.tif",
                                   wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

    openFileDialog.ShowModal()
    filename = openFileDialog.GetPaths()
    print("Selected image: ", filename)
    openFileDialog.Destroy()
    return filename


if __name__ == '__main__':
    params = {}
    run(params)

# CHANGELOG
# - v1.00: - Using tkinter to choose file and display results
# - v1.10: - Using wxpython to choose file and display results
# - v1.11: - New virtual env code for auto-activation
