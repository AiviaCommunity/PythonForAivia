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
import re

max_char_len = 150


# [INPUT Name:inputImagePath Type:string DisplayName:'Any channel']
# [OUTPUT Name:resultPath Type:string DisplayName:'Dummy to delete']
def run(params):
    # Choose file
    file_path = pick_file('')

    # Read the file
    raw_text = open(file_path, 'r+').read()

    # Split description from processing steps
    main_parts = raw_text.split('"Entities":[')

    # Split processing steps
    block_end_pattern = re.compile(r'},{\"[^(RecipeName|Name)]')
    step_blocks = re.split(block_end_pattern, main_parts[1])

    # Prepare displayed table
    app = wx.App()
    frame = wx.Frame(parent=None, title='TIF tags', size=(1000, 1000))

    table = wx.ListCtrl(frame, size=(-1, 100), style=wx.LC_REPORT)
    table.InsertColumn(0, 'Info', width=200)
    table.InsertColumn(1, 'Value', width=1600)

    # Write first part
    r = 0
    table.InsertItem(r, 'Description')
    table.SetItem(r, 1, main_parts[0].replace(',', ',\n'))
    r += 1

    # Split values in each block
    for i in range(len(step_blocks)):
        # Writing a line to separate blocks
        table.InsertItem(r, '----- Step ' + str(i) + ' ---')
        table.SetItem(r, 1, '---------------------------------')
        r += 1

        lines = step_blocks[i].split(',')

        for l in lines:
            split_line = l.split(':')

            # Repair some broken text
            filtered_tag = split_line[0].replace('ackupPath"',
                                                 '"BackupPath"').replace('ixelClassifierID"',
                                                                         '"PixelClassifierID"')

            # Insert tag name
            table.InsertItem(r, filtered_tag)

            # Set value because some can be very long
            final_val = str(split_line[1:])

            # Removing some characters from value
            filtered_value = re.sub('[}\[\]\"\']', '', final_val)

            # Insert value
            table.SetItem(r, 1, filtered_value)

            r += 1

    frame.Show()
    app.MainLoop()


def wrap(string, length):
    return '\n'.join(textwrap.wrap(string, length))


def pick_file(default_dir):
    print('Starting wxPython app')
    app = wx.App()

    # Create open file dialog
    openFileDialog = wx.FileDialog(None, "Select a Aivia Workflow file",
                                   default_dir, "", "Workflow files (*.workflow)|*.workflow",
                                   wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

    openFileDialog.ShowModal()
    filename = openFileDialog.GetPath()
    print("Selected file: ", filename)
    openFileDialog.Destroy()
    return filename


if __name__ == '__main__':
    params = {}
    run(params)

# CHANGELOG
# v1.00: - First version
# v1.01: - New virtual env code for auto-activation
