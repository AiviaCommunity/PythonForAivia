# -------- Activate virtual environment -------------------------
import os
import ctypes
import sys
from pathlib import Path
parentFolder = str(Path(__file__).parent.parent)
activate_path = parentFolder + '\\env\\Scripts\\activate_this.py'
if os.path.exists(activate_path):
    exec(open(activate_path).read(), {'__file__': activate_path})
    print(f'Aivia virtual environment activated\nUsing python: {activate_path}')
else:
    # Attempt to still run the script with main Aivia python interpreter
    error_mess = f'Error: {activate_path} was not found.\nPlease run the \'FirstTimeSetup.py\' script in Aivia first.'
    ans = ctypes.windll.user32.MessageBoxW(0, error_mess, 'Error', 1)
    if ans == 2:
        sys.exit(error_mess)
    print('\n'.join(['#' * 40, error_mess,
                     'Now trying to fallback on python environment specified in Aivia options > Advanced.',
                     '#' * 40]))
# ---------------------------------------------------------------

import pandas as pd
import wx
import concurrent.futures
import openpyxl.utils.cell

# Folder to quickly run the script on all Excel files in it
DEFAULT_FOLDER = ''         # Example: r'D:\Aivia Working Directory\'

# Combining measurement tabs into one (for the same object subset)
do_combine_tabs = True

# Default action when combining multiple spreadsheets (see scenario A and B below). True = B
do_multiple_cols = False

# Scenario D: tables processed separately
do_separated_processing = True
if do_separated_processing:
    do_combine_tabs = True
    do_multiple_cols = False


"""
Warning: BETA VERSION, only scenario D was tested, with no timepoints.

Convert multiple Excel spreadsheets (in the same input folder) exported from Aivia into a single Excel file.
Options:
    A - Multiple files selected, spreadsheets do not contain timepoints, data is combined in the same column (stacked data)
    B - Multiple files selected, spreadsheets do not contain timepoints, data is combined in multiple columns 
        (1 column = data from 1 spreadsheet)
    C - Multiple files selected, spreadsheets do CONTAIN timepoints, data is combined in the same column
        (1 column = 1 timepoint)
    D - Single OR MULTIPLE files selected, spreadsheet does not contain timepoints, measurement tabs are combined as multiple columns 
        (1 column = 1 measurement, 1 tab = 1 object subset), each table is processed SEPARATELY

WARNING: This currently works only under the following conditions:
    - The file were exported from Aivia as Excel files (not CSV)
    - There is no time dimension
    - The default row/column ordering was not changed at export.
    - Filenames do not contain '.' characters

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
    global do_combine_tabs, do_multiple_cols, do_separated_processing

    add_summary = False     # Used to know if the tab is missing from the beginning

    # Choose files (or rely on an hard coded default folder)
    input_folder = DEFAULT_FOLDER
    if input_folder != "":
        # Preparing file list
        all_files = os.listdir(input_folder)
        indiv_list = [os.path.join(os.path.abspath(input_folder), f) for f in all_files
                      if (f.endswith('.xlsx') and not f.startswith('~') and not f.endswith('combined-tab.xlsx'))]

    else:
        indiv_list = pick_files()
        input_folder = os.path.dirname(indiv_list[0])

    if len(indiv_list) < 1:
        error_msg = 'No Excel file found in the selected folder:\n{}\nTry to select another folder'.format(input_folder)
        Mbox('Error', error_msg, 0)
        sys.exit(error_msg)

    # Prompt for user to see how many tables will be processed
    mess = '{} Excel files were detected.\nPress OK to continue.'.format(len(indiv_list)) + \
           '\nA confirmation popup message will inform you when the process is complete.'
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(Mbox, 'Detected tables', mess, 1)
        ans = future.result()

    print(mess)  # for log

    if ans == 2:
        sys.exit('Process terminated by user')

    # Starting point for scenario D for multiple files
    final_input_list = []
    if do_separated_processing:
        final_input_list = indiv_list                   # To prepare loop to process files independently
    else:
        final_input_list = indiv_list[0]                # Dummy entry which is 1 item to run the process once

    # Main LOOP -----------------------------------------------------------------------------------------------
    for input_file in final_input_list:
        if len(final_input_list) > 1:
            indiv_list = input_file         # List of tables is trimmed down to one item to invoke scenario D

        # Reading first file to collect info
        df_raw_1 = pd.read_excel(indiv_list[0], sheet_name=None)

        # Check if timepoints exist (would not allow combining tabs as different columns)
        contains_tps = False
        all_tabs = list(df_raw_1.keys())
        last_tab = all_tabs[-1]
        if df_raw_1[last_tab].shape[1] > 2:         # Checking no of columns in last sheet as 1st might be summary
            contains_tps = True

        # Checking if file is from a Cell Analysis recipe
        if any('Cell Membranes' in x for x in all_tabs[0:1]) is False:
            error_msg = 'The measurements table {} doesn\'t seem to be from a Cell Analysis recipe'.format(indiv_list[0])
            Mbox('Error', error_msg, 0)
            sys.exit(error_msg)

        # Check if summary tab is present or not
        if not 'Summary' in all_tabs:
            add_summary = True

        # Collect vesicle list and check "Cell ID" measurement exists for each vesicle set
        ves_list_tmp = [get_split_name(t)[1] for t in all_tabs if (str(t).startswith("Vesicles - ") and str(t).find("Cell ID") > -1)]
        ves_list = list(dict.fromkeys(ves_list_tmp))

        ves_list_msg = 'Vesicle sets:\n'
        for ves in ves_list:
            if '{}.Cell ID'.format(ves) in all_tabs:
                ves_list_msg += '{} >> Relation with cells is detected\n'.format(ves)
            else:
                ves_list_msg += '{} >> No relation with cells\n'.format(ves)
                ves_list.remove(ves)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.submit(Mbox, 'Information about vesicle sets', ves_list_msg, 0)
        print(ves_list_msg)     # for log

        df_grouped = {}     # init

        if len(indiv_list) == 1:    # D (see docstring)
            output_basename = '{}_combined-tab.xlsx'.format(os.path.basename(indiv_list[0]).split('.')[0])
            output_file = os.path.join(os.path.abspath(input_folder), output_basename)
            df_grouped = df_raw_1

        else:    # A-B-C (see docstring)
            # defining output name
            output_basename = '{}_grouped.xlsx'.format(os.path.basename(indiv_list[0]).split('.')[0])
            output_file = os.path.join(os.path.abspath(input_folder), output_basename)

            # Collect tab names from first file
            tab_names_ref = df_raw_1.keys()

            # Processing the first file
            df_grouped = df_raw_1

            if do_multiple_cols and not contains_tps:    # B
                do_combine_tabs = False     # not possible as columns = measurements

                # Renaming column headers for first table
                for t in tab_names_ref:
                    df_grouped[t].rename(columns={df_grouped[t].columns[-1]: os.path.basename(indiv_list[0])}, inplace=True)

                # Loop
                for f in indiv_list[1:]:
                    df_raw = pd.read_excel(f, sheet_name=None)
                    tab_names = df_raw.keys()

                    if tab_names == tab_names_ref:
                        # Start looping over the different sheets
                        for t in tab_names:
                            df_grouped[t] = pd.concat([df_grouped[t], df_raw[t].iloc[:, 1]], axis=1)
                            df_grouped[t].rename(columns={df_grouped[t].columns[-1]: os.path.basename(f)}, inplace=True)

            else:   # A-C
                # Adding prefix (file name) to first column
                for t in tab_names_ref:
                    df_grouped[t].iloc[:, 0] = [os.path.basename(indiv_list[0]) + "_" + r for r in df_grouped[t].iloc[:, 0]]

                # Loop
                for f in indiv_list[1:]:
                    if indiv_list != output_basename:       # avoids including an existing grouped table
                        df_raw = pd.read_excel(f, sheet_name=None)
                        tab_names = df_raw.keys()

                        if tab_names == tab_names_ref:
                            # Start looping over the different sheets
                            for t in tab_names:
                                # Adding prefix (file name) to first column in the raw table
                                df_raw[t].iloc[:, 0] = [os.path.basename(f) + "_" + r for r in df_raw[t].iloc[:, 0]]

                                # Merging to previous grouped data
                                df_grouped[t] = pd.concat([df_grouped[t], df_raw[t]], axis=0)

        # Combine tabs into one if no timepoints in data (scenario A or D)
        if not contains_tps and do_combine_tabs:
            df_grouped = combine_tabs(df_grouped)

            # Add the summary tab
            if add_summary:
                df_summary = pd.DataFrame({'Summary': [], 'Frame 0': []})
                df_grouped['Summary'] = df_summary

            # Add vesicles statistics if Cell ID exists for each set
            df_grouped['Cells'] = add_vesicles_statistics(df_grouped, ves_list)

            # Calculate cell count and average over cells
            cell_count = df_grouped['Cells'].shape[0]
            df_summary_to_add = pd.DataFrame({'Summary': ['Total number of cells'], 'Frame 0': [cell_count]})
            df_mean_values = df_grouped['Cells'].mean().to_frame().reset_index()
            df_mean_values.rename(columns={df_mean_values.columns[0]: 'Summary',
                                           df_mean_values.columns[1]: 'Frame 0'}, inplace=True)

            # Rename with "Average of "
            df_mean_values['Summary'] = 'Average of ' + df_mean_values['Summary']

            df_summary_to_add = pd.concat([df_summary_to_add, df_mean_values], axis=0, ignore_index=True)

            # Remove undesired results (e.g. centroid average)
            drop_list = ['Centroid']
            index_to_drop = [r for r in range(1, df_summary_to_add.shape[0])
                             if (any(x in df_summary_to_add.iloc[r, 0] for x in drop_list))]
            df_summary_to_add.drop(df_summary_to_add.index[index_to_drop], inplace=True)

            # Merge with potential existing summary tab
            df_grouped['Summary'] = pd.concat([df_grouped['Summary'], df_summary_to_add], axis=0, ignore_index=True)

        # Writing sheets to excel
        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            # Write Summary first
            df_grouped['Summary'].to_excel(writer, sheet_name='Summary', index=False)

            # Resizing columns
            for c in range(0, len(df_grouped['Summary'].columns)):
                col_letter = openpyxl.utils.cell.get_column_letter(c + 1)
                # Get longest text
                len_longest_text = df_grouped['Summary'].iloc[:, c].map(str).str.len().max()
                writer.sheets['Summary'].column_dimensions[col_letter].width = len_longest_text

            for sh in [d for d in df_grouped.keys() if d != 'Summary']:
                df_grouped[sh].to_excel(writer, sheet_name=sh, index=False)

                # Resizing columns
                for c in range(0, len(df_grouped[sh].columns)):
                    col_letter = openpyxl.utils.cell.get_column_letter(c+1)
                    writer.sheets[sh].column_dimensions[col_letter].width = len(str(df_grouped[sh].columns[c]))

        # Message box to confirm table processing
        print('Your new table was saved here:\n{}'.format(output_file))
        Mbox('Table processed', 'Your new table was saved here:\n{}'.format(output_file), 0)


def combine_tabs(df_raw):
    df_combined = {}
    df_temp = pd.DataFrame()
    object_name = ''
    main_object_set = ''        # Used for vesicle statistics addition

    for k in df_raw.keys():
        # Don't need the summary tab if included
        if k == 'Summary':
            df_combined = {k: df_raw[k]}

        # First iteration with detailed objects
        elif k != 'Summary' and df_temp.empty is True:
            # Determines what type of Aivia objects (i.e. Mesh, Slice of Cell, etc.) and measurement
            meas_name, object_name = get_split_name(k)
            if meas_name == '--incomplete--':
                meas_name = df_raw[k].columns[0]

            # Copying the sheet
            df_temp = df_raw[k]

            # Writing headers for the 1st and 2nd column
            df_temp.columns = ['Objects', df_raw[k].columns[0]]

            # Changing 'Cell Membrane' to 'Cell'
            df_temp['Objects'] = df_temp['Objects'].str.replace('Membrane ', '')

        # Fill the dataframe
        else:
            # Determines what type of Aivia objects (i.e. Mesh, Slice of Cell, etc.) and measurement
            meas_name, object_name_temp = get_split_name(k)
            if meas_name == '--incomplete--':
                meas_name = df_raw[k].columns[0]

            # Check if object name changed or not (only if it is 'Cell Membranes' or 'Vesicles - ...'
            # This allows to group 'Cells', 'Nuclear Membranes', 'Cytoplasm', etc.
            if object_name_temp != object_name and object_name_temp.split(' ')[0] in ['Cell', 'Vesicles']:

                # Adding prepared sheet to main series to create a new sheet
                main_object_set = object_name.replace(' Membranes', 's')
                df_combined[main_object_set] = df_temp

                # Now using new name as the new reference
                object_name = object_name_temp

                # Copying the current read sheet to be a new one
                df_temp = df_raw[k]

                # Writing headers for the 1st and 2nd column
                df_temp.columns = ['Objects', df_raw[k].columns[0]]

                # Changing 'Cell Membrane' to 'Cell'
                df_temp['Objects'] = df_temp['Objects'].str.replace('Membrane ', '')

            else:
                # Adding the new column to existing temp sheet
                df_temp = pd.concat([df_temp, df_raw[k].iloc[:, 1]], axis=1)

                # Adding the measurement name as a header
                df_temp.rename(columns={df_temp.columns[-1]: df_raw[k].columns[0]}, inplace=True)

    # Adding a generic name to objects if none
    if object_name == '':
        object_name = 'Object Set 1'

    # Adding last prepared sheet to main series to create a new sheet
    df_combined[object_name] = df_temp

    return df_combined


def add_vesicles_statistics(df, vesicle_list):
    # Warning: only working on the first cell set (in case there are multiple sets)

    df_main = df['Cells']                   # Where individual cell stats will be written
    start_col = len(df_main.columns)        # Column number where to start writing
    no_cells = df_main.shape[0]             # Number of cells
    i = 1                                   # Column index to put the vesicle count

    for ves_name in vesicle_list:
        df_ves = df[ves_name]
        # Rename columns with average
        df_ves = df_ves.rename(columns=lambda x: x.replace(x.split(".")[-1], 'Average ' + x.split(".")[-1]))

        df_main_to_add = pd.DataFrame(columns=df_ves.columns)
        # Rename first column to be total no of ves
        df_main_to_add.rename(columns={df_main_to_add.columns[0]: ves_name + '.Count'}, inplace=True)

        for cell_name in df_main.iloc[:, 0]:
            cell_no = int(cell_name.split(' ')[1])

            # Filter table for Cell ID matching cell no
            df_cell = df_ves[df_ves[ves_name + '.Average Cell ID'] == cell_no]

            # No of vesicles
            ves_count = pd.DataFrame({ves_name + '.Count': [df_cell.shape[0]]})

            # Calculate average values
            mean_vals = df_cell.mean().to_frame().transpose()

            # Concatenate with vesicle count
            df_cell_mean = pd.concat([ves_count, mean_vals], axis=1)

            # Write results in temp df
            df_main_to_add = pd.concat([df_main_to_add, df_cell_mean], axis=0, ignore_index=True)

        # Remove Cell ID column
        df_main_to_add = df_main_to_add.drop(ves_name + '.Average Cell ID', axis=1)

        # Concatenate with main df
        df_main = pd.concat([df_main, df_main_to_add], axis=1)

        # Move vesicle count column to the beginning
        count_column = df_main.pop(ves_name + '.Count')
        df_main.insert(i, ves_name + '.Count', count_column)
        i += 1

    return df_main      # To replace 'Cells' tab


def get_split_name(txt: str):
    # First check if text doesn't end with ...
    if txt.endswith('...'):
        txt = txt[:-3]
        meas_name = '--incomplete--'        # name can't be retrieved from here
    else:
        meas_name = txt.split('.')[-1]

    obj_name = '.'.join(txt.split('.')[:-1])
    if obj_name == 'Std. Dev':
        meas_name = txt
        obj_name = ''

    return meas_name, obj_name


def pick_files():
    print('Starting wxPython app')
    app = wx.App()

    # Create open file dialog
    openFileDialog = wx.FileDialog(None, "Select a Cell Analysis results table (xlsx) to process", ".\\", "",
                                   "Excel files (*.xlsx)|*.xlsx", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE)

    openFileDialog.ShowModal()
    filenames = openFileDialog.GetPaths()
    print("Selected table(s): ", filenames)
    openFileDialog.Destroy()
    return filenames


def Mbox(title, text, style):
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)


if __name__ == '__main__':
    params = {}
    run(params)

# Changelog:
# v1.00: - Checked for scenario D only. No time dimension expected.
