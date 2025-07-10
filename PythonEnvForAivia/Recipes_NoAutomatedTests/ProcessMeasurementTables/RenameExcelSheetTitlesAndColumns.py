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

import numpy as np
import pandas as pd
from magicgui import magicgui
from skimage.io import imread, imsave
import openpyxl.utils.cell
import concurrent.futures

"""
Rename sheet titles and column headers in Excel tables from Aivia.
Renaming is done thanks to a reference table (csv or excel based) where first column is the source name, 
and second column is the new name. Each sheet is separated with an empty row. 
First row of the reference table should be as the example below.
If column headers or sheet titles are not found in the reference table, they would be deleted in the output.
Below is an example:

..........................
Old name,New name                               (mandatory first row)
Sheet 1 old name,Sheet 1 new name
Column 1 old name,Column 1 new name
Column 2 old name,Column 2 new name
                                                (blank row)
Sheet 2 old name,Sheet 2 new name
Column 1 old name,Column 1 new name
Column 2 old name,Column 2 new name
..........................

Requirements
------------
pandas
openpyxl
xlrd
wxPython
magicgui

Parameters
----------
GUI asking for:
    - Input file, so that all excel tables in the same folder are also processed
    - Reference csv or xslx file providing new names

Returns
-------
- New folder with all new tables renamed

"""


# [INPUT Name:inputPath Type:string DisplayName:'Any channel']
# [OUTPUT Name:resultPath Type:string DisplayName:'Dummy to delete']
def run(params):
    # image_org = params['EntryPoint']
    image_location = params['inputPath']
    result_location = params['resultPath']

    @magicgui(g_table_to_process={'label': 'Choose one Excel table to process '
                                           '(all other Excel tables will be processed too):',
                                  'mode': 'r'},
              g_ref_names_path={'label': 'Choose the reference table providing the new sheet and column names:',
                                'mode': 'r'},
              g_remove_not_specified={"widget_type": "CheckBox", "visible": False,
                                      "label": "Remove any sheet or column if name is not mentioned in the reference table"},
              call_button="Run")
    def magic_gui(g_table_to_process=Path.home(), g_ref_names_path=Path.home(), g_remove_not_specified=True):
        pass

    @magic_gui.called.connect
    def close_GUI_callback():
        magic_gui.close()

    magic_gui.show(run=True)
    table_to_process = magic_gui.g_table_to_process.value
    ref_names_path = magic_gui.g_ref_names_path.value
    remove_not_specified = magic_gui.g_remove_not_specified.value

    # List all Excel tables to process
    input_folder = os.path.dirname(table_to_process)
    all_files = os.listdir(input_folder)
    indiv_plist = [os.path.join(os.path.abspath(input_folder), f) for f in all_files
                  if (f.endswith('.xlsx') and not f.startswith('~'))]

    # Discard ref table if in the same folder
    if ref_names_path in indiv_plist:
        indiv_plist.remove(ref_names_path)

    # Check if user wants to continue with all Excel tables
    with concurrent.futures.ThreadPoolExecutor() as executor:
        mess = '{} Excel files were detected.\nPress OK to continue or CANCEL to stop.'.format(len(indiv_plist)) + \
               '\nA confirmation popup message will inform you when the process is complete.'
        future = executor.submit(Mbox, 'Detected tables', mess, 1)
        ans = future.result()

    if ans == 2:
        sys.exit('>>> Process terminated by user <<<')

    # Define output folder
    output_folder = os.path.join(os.path.dirname(input_folder), os.path.basename(input_folder) + '_renamed')
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    # Scan ref table with old and new names
    ref_table = pd.read_excel(ref_names_path, sheet_name=0)
    ref_table_info = scan_ref_table(ref_table)

    # Execute changes on all tables
    f_count = 0
    for f in indiv_plist:
        t_count, c_count = 0, 0
        cur_table = pd.read_excel(f, sheet_name=None)
        tab_names = cur_table.keys()

        # Init new table
        new_table = {}

        for t in tab_names:
            if t in ref_table_info.keys():
                # Prepare new tab
                new_tab_name = ref_table_info[t]['New sheet name']
                new_table[new_tab_name] = pd.DataFrame(cur_table[t].iloc[:, 0].values,
                                                       index=cur_table[t].index, columns=[new_tab_name])
                t_count += 1

                # Add column with new headers, if in the list
                col_names = cur_table[t].columns.tolist()
                for c in col_names:
                    if c in ref_table_info[t].keys():
                        to_append = cur_table[t].loc[:, c]
                        new_c_name = ref_table_info[t][c]
                        new_table[new_tab_name][new_c_name] = to_append
                        c_count += 1

        # Save new Excel table
        try:
            assert bool(new_table)
            out_path = os.path.join(output_folder, os.path.basename(f))
            with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
                for sh in new_table.keys():
                    new_table[sh].to_excel(writer, sheet_name=sh, index=False)
    
                    # Resizing columns
                    for c in range(0, len(new_table[sh].columns)):
                        col_letter = openpyxl.utils.cell.get_column_letter(c + 1)
                        len_header = len(str(new_table[sh].columns[c]))
                        len_values = len(str(new_table[sh].iat[0, c]))
                        len_longest_text = max(len_header, len_values)
                        writer.sheets[sh].column_dimensions[col_letter].width = len_longest_text

            mess = f'{t_count} sheets and {c_count} columns were copied for the file:\n{os.path.basename(f)}'
            print(mess)
            f_count += 1
                        
        except BaseException as e:
            mess = f'Following file was skipped:\n{os.path.basename(f)}\nError message:\n{e}'
            print(mess)

    # Main LOOP END -------------------------------------------------------------------------------------------

    # Save the angle map
    input_image = imread(image_location)
    imsave(result_location, np.zeros_like(input_image))

    # Message box to confirm table processing
    final_mess = f'{f_count} Excel tables were processed. Output folder will open now...'
    print(final_mess)
    Mbox('Process completed', final_mess, 0)
    os.startfile(output_folder)


def scan_ref_table(df_from_excel):
    """
    :param df_from_excel: from the reading of the excel file

    return: a dictionary:
                {'Sheet 1 old name': {
                                'New sheet name': 'Sheet 1 new name',
                                'Column 1 old name': 'Column 1 new name',
                                'Column 2 old name': 'Column 2 new name'
                                }
                etc.
    """
    out_dict, tmp_dict, tmp_sheet_name = {}, {}, ""
    start_new_sheet = True

    for i, ro in df_from_excel.iterrows():
        if not ro.isna().values.all():
            # All subsequent info should be associated to the same sheet
            if start_new_sheet:
                tmp_sheet_name = ro.iat[0]
                tmp_dict['New sheet name'] = ro.iat[1]
                start_new_sheet = False

            else:
                tmp_dict[ro.iat[0]] = ro.iat[1]       # expected to be column names

        else:
            out_dict[tmp_sheet_name] = tmp_dict
            tmp_dict, tmp_sheet_name = {}, ""
            start_new_sheet = True

    out_dict[tmp_sheet_name] = tmp_dict

    return out_dict


def Mbox(title, text, style):
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)


if __name__ == '__main__':
    di = r'D:\PythonCode\Python_scripts\Projects\ExcelFileHandling\tests'
    params = {'inputPath': di + r'\_Wiki_3D Obj Tracking-Demo_10.5_R_2 track sets for distance-angle.aivia.tif',
              'resultPath': di + r'\_Wiki_3D Obj Tracking-Demo_10.5_R_angle_map.tif'
              }
    run(params)

# Changelog:
# v1.00: - First version only keeping columns which are listed in the ref table. Others are not kept.
