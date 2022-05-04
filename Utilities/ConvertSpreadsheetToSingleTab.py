import os
import pandas as pd
import ctypes
import wx
import threading

"""
Convert a multi-tab spreadsheet exported from Aivia into a single tab.

WARNING: This currently works only under the following conditions:
    - The file was exported from Aivia as an Excel file (not CSV)
    - There is no time dimension
    - The default row/column ordering was not changed at export.

The converted file will be saved with the same name as the original but with
"..._formatted" appended to the end.

Requirements
------------
pandas      (comes with Aivia installer)
openpyxl    (comes with Aivia installer)
xlrd        (comes with Aivia installer)
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
    aivia_excel_file = pick_file()

    xl_file = os.path.abspath(aivia_excel_file)
    output_basename = '{}_formatted.xlsx'.format(os.path.basename(xl_file).split('.')[0])
    output_file = os.path.join(os.path.dirname(xl_file), output_basename)
    
    df_raw = pd.read_excel(xl_file, sheet_name=None)
    df_grouped = {}
    df_temp = pd.DataFrame()
    object_name = ''

    for k in df_raw.keys():
        # Don't need the summary tab if included
        if k == 'Summary':
            df_grouped = {k: df_raw[k]}

        # First iteration with detailed objects
        elif k != 'Summary' and df_temp.empty is True:
            # Determines what type of Aivia objects (i.e. Mesh, Slice of Cell, etc.) and measurement
            meas_name, object_name = get_split_name(k)
            if meas_name == '--incomplete--':
                meas_name = df_raw[k].columns[0]

            # Copying the sheet
            df_temp = df_raw[k]

            # Writing headers for the 1st and 2nd column
            df_temp.columns = [object_name, meas_name]

        # Fill the dataframe
        else:
            # Determines what type of Aivia objects (i.e. Mesh, Slice of Cell, etc.) and measurement
            meas_name, object_name_temp = get_split_name(k)
            if meas_name == '--incomplete--':
                meas_name = df_raw[k].columns[0]

            # Check if object name changed or not
            if object_name_temp != object_name and object_name_temp != '':
                # Adding prepared sheet to main series to create a new sheet
                df_grouped[object_name] = df_temp

                # Now using new name as the new reference
                object_name = object_name_temp

                # Copying the current read sheet to be a new one
                df_temp = df_raw[k]

                # Writing headers for the 1st and 2nd column
                df_temp.columns = [object_name, meas_name]

            else:
                # Adding the new column to existing temp sheet
                df_temp = pd.concat([df_temp, df_raw[k].iloc[:, 1]], axis=1)

                # Adding the measurement name as a header
                df_temp.rename(columns={df_temp.columns[-1]: meas_name}, inplace=True)

    # Adding a generic name to objects if none
    if object_name == '':
        object_name = 'Object Set 1'

    # Adding last prepared sheet to main series to create a new sheet
    df_grouped[object_name] = df_temp

    # Writing sheets to excel
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        for sh in df_grouped.keys():
            df_grouped[sh].to_excel(writer, sheet_name=sh, index=False)

    # Message box to confirm table processing
    print('Your new table was saved here:\n{}'.format(output_file))
    Mbox('Table processed', 'Your new table was saved here:\n{}'.format(output_file), 0)


def get_split_name(txt: str):
    # First check if text doesn't end with ...
    if txt.endswith('...'):
        txt = txt[:-3]
        meas_name = '--incomplete--'        # name can't be retrieved from here
    else:
        meas_name = txt.split('.')[-1]

    obj_name = '.'.join(txt.split('.')[:-1])

    return meas_name, obj_name


def pick_file():
    print('Starting wxPython app')
    app = wx.App()
    frame = wx.Frame(None, -1, 'File picker')
    # frame.SetSize(0, 0, 200, 50)

    # Create open file dialog
    openFileDialog = wx.FileDialog(frame, "Select a results table (xlsx) to process", ".\\", "",
                                   "Excel files (*.xlsx)|*.xlsx", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

    openFileDialog.ShowModal()
    fname = openFileDialog.GetPath()
    print("Selected table: ", fname)
    openFileDialog.Destroy()
    return fname


def Mbox(title, text, style):
    threading.Thread(
        target=lambda: ctypes.windll.user32.MessageBoxW(0, text, title, style)
    ).start()


if __name__ == '__main__':
    params = {}
    run(params)

# Changelog:
# v1.00: - using wxPython for the file picker, multiple sheets stored as dictionary of DataFrames (keys = sheet names)
