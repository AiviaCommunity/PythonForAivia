# -------- Activate virtual environment -------------------------
import os
import ctypes
from pathlib import Path
parentFolder = str(Path(__file__).parent.parent)
activate_path = parentFolder + '\\env\\Scripts\\activate_this.py'
if os.path.exists(activate_path):
    exec(open(activate_path).read(), {'__file__': activate_path})
    print(f'Aivia virtual environment activated\nUsing python: {activate_path}')
else:
    # Attempt to still run the script with main Aivia python interpreter
    error_mess = '\n'.join(['#' * 40,
                     f'### Error: {activate_path} was not found.',
                     '### Please run the \'FirstTimeSetup.py\' script in Aivia first.',
                     '### Now trying to fallback on python environment specified in Aivia options > Advanced.',
                     '#' * 40])
    ctypes.windll.user32.MessageBoxW(0, error_mess, 'Error', 0)
    print(error_mess)
# ---------------------------------------------------------------

import pandas as pd
import wx
import concurrent.futures

"""
Convert multiple Excel spreadsheets (in the same input folder) exported from Aivia into a single Excel file.

WARNING: This currently works only under the following conditions:
    - The file were exported from Aivia as Excel files (not CSV)
    - There is no time dimension
    - The default row/column ordering was not changed at export.

The converted file will be saved with the same name as the original but with
"..._grouped" appended to the end.

Requirements
------------
pandas
openpyxl
xlrd
wxPython

(openpyxl and xlrd are Pandas requirements, but are not always
installed with it. Install them explicitly if you receive errors.)

Parameters
----------
aivia_excel_file : string
    Path to the Excel file exported from Aivia.

Returns
-------
DataFrame  
    Data from the spreadsheet converted to a Pandas DataFrame.

"""


# [INPUT Name:inputPath Type:string DisplayName:'Any channel']
# [OUTPUT Name:resultPath Type:string DisplayName:'Dummy to delete']
def run(params):
    # Pick the file
    input_folder = pick_folder()

    # Preparing file list
    all_files = os.listdir(input_folder)
    indiv_list = [f for f in all_files if f.endswith('.xlsx')]

    if len(indiv_list) < 1:
        error_msg = 'No Excel file found in the selected folder:\n{}\nTry to select another folder'.format(input_folder)
        Mbox('Error', error_msg, 0)
        sys.exit(error_msg)

    # Prompt for user to see how many tables will be processed
    with concurrent.futures.ThreadPoolExecutor() as executor:
        mess = '{} Excel files were detected.\nPress OK to continue.'.format(len(indiv_list)) + \
               '\nA confirmation popup message will inform you when the process is complete.'
        future = executor.submit(Mbox, 'Detected tables', mess, 1)
        ans = future.result()

    if ans == 2:
        sys.exit('Process terminated by user')

    # defining output name
    output_basename = '{}_grouped.xlsx'.format(os.path.basename(indiv_list[0]).split('.')[0])
    output_file = os.path.join(os.path.abspath(input_folder), output_basename)

    # Reading first file to collect tab names
    xl_file_1 = os.path.join(os.path.abspath(input_folder), indiv_list[0])
    df_raw_1 = pd.read_excel(xl_file_1, sheet_name=None)
    tab_names_ref = df_raw_1.keys()

    # Processing the first file and renaming column headers
    df_grouped = df_raw_1
    for t in tab_names_ref:
        df_grouped[t].rename(columns={df_grouped[t].columns[-1]: indiv_list[0]}, inplace=True)

    # Loop
    for f in indiv_list[1:]:
        xl_file = os.path.join(os.path.abspath(input_folder), f)
        df_raw = pd.read_excel(xl_file, sheet_name=None)
        tab_names = df_raw.keys()

        if tab_names == tab_names_ref:
            # Start looping over the different sheets
            for t in tab_names:
                df_grouped[t] = pd.concat([df_grouped[t], df_raw[t].iloc[:, 1]], axis=1)
                df_grouped[t].rename(columns={df_grouped[t].columns[-1]: f}, inplace=True)

    # Writing sheets to excel
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        for sh in df_grouped.keys():
            df_grouped[sh].to_excel(writer, sheet_name=sh, index=False)

    # Message box to confirm table processing
    print('Your new table was saved here:\n{}'.format(output_file))
    Mbox('Table processed', 'Your new table was saved here:\n{}'.format(output_file), 0)


def pick_folder():
    print('Starting wxPython app')
    app = wx.App()

    # Create open file dialog
    openDirDialog = wx.DirDialog(None, "Select a folder containing Excel tables to combine",
                                 defaultPath=os.environ['HOMEPATH'], style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
    openDirDialog.ShowModal()
    fname = openDirDialog.GetPath()
    openDirDialog.Destroy()

    print("Selected folder: ", fname)
    return fname


def Mbox(title, text, style):
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)


if __name__ == '__main__':
    params = {}
    run(params)

# Changelog:
# v1.00: - using wxPython for the file picker, multiple sheets stored as dictionary of DataFrames (keys = sheet names)
