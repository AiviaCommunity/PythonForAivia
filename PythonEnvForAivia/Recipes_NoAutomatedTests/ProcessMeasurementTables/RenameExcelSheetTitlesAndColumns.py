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
from skimage.io import imread, imsave
import subprocess, json

"""
Rename sheet titles and column headers in Excel tables from Aivia.
Renaming is done thanks to a reference table (csv or excel based) where first column is the source name, 
and second column is the new name. Each sheet is separated with an empty row. 
First row of the reference table should be as the example below.
Column names are searched all along the first row of the table, as measurement name can either be in:
- column A on raw sheets out of Aivia,
- column B or more if sheets were processed to combine all measurements as columns.

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
    image_location = params['inputPath']
    result_location = params['resultPath']

    # First UI to help creating the reference table or not
    # Each entry is expected to have: label, widget_type, choices (if needed)
    # A file browser is automatically bound to a "BrowseButton" in the same grid no. Same with "CallButton" and "Cancel"
    # Slider choices = min, max, step, init-value (all should be integer) | &#10; for line break in labels
    ui_width, ui_height = 540, 380
    info_dict = {'g_table_to_process': {"widget_type": "FileDialog", "label": "Choose one Excel table to process "
                                                                              "&#10;(all other Excel tables in the same "
                                                                              "folder will be processed too):",
                                        "choices": "Excel files (*.csv;*.xlsx)|*.csv;*.xlsx"},
                 'g_file_extension': {"widget_type": "RadioButtons", "label": "Select the file type to be detected",
                                      'choices': ["xlsx", "csv"]},
                 'lbl1': {"widget_type": "Label",
                          "label": 'Note: If you want to create a reference table draft from the selected Excel file above,'
                                   '&#10;leave the field empty below and a file will be created automatically...'},
                 'g_ref_names_path': {"widget_type": "FileDialog", "label": "Choose the reference table providing "
                                                                            "the new sheet and column names:",
                                      "choices": "Excel files (*.csv;*.xlsx)|*.csv;*.xlsx"},
                 'g_remove_not_specified': {"widget_type": "CheckBox",
                                            "label": "Remove elements which do not have any replacement in the reference table?"
                                                     "&#10; (leave unticked if you want to keep all)",
                                            "choices": "True"},
                 'CallButton': {"widget_type": "OKButton", "label": "Process"}
                 }

    params_ui = ask_parameters_wpf(info_dict, ui_width, ui_height)

    table_to_process = params_ui['g_table_to_process']
    ref_names_path = params_ui['g_ref_names_path']
    remove_not_specified = params_ui['g_remove_not_specified']
    file_extension = params_ui['g_file_extension']

    # Create ref table draft if not specified
    if not os.path.exists(ref_names_path):
        ref_names_path = trigger_ref_table_creation(table_to_process)

    # List all Excel tables to process
    input_folder = os.path.dirname(table_to_process)
    all_files = os.listdir(input_folder)
    indiv_plist = [os.path.join(os.path.abspath(input_folder), f) for f in all_files
                   if (f.endswith(f'.{file_extension}') and not f.startswith('~'))]

    # Discard ref table if in the same folder
    if os.path.dirname(ref_names_path) == input_folder and ref_names_path in indiv_plist:
        indiv_plist.remove(ref_names_path)

    # Check if user wants to continue with all Excel tables
    mess = '{} Excel files were detected.\nPress OK to continue or CANCEL to stop.'.format(len(indiv_plist)) + \
           '\nA confirmation popup message will inform you when the process is complete.'
    ans = Mbox('Detected tables', mess, 1)

    if ans == "Cancel":
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
            # Trying to find the same name with potential regex tag

            for ref in ref_table_info.keys():
                t_template = ""
                if "REGEX" in ref:
                    constant_parts = ref.split("REGEX")
                    # print(f"'{t}' // '{constant_parts[0]}': {t.startswith(constant_parts[0])}")
                    if t.startswith(constant_parts[0]) and t.endswith(constant_parts[1]):
                        t_template = ref
                else:
                    if t == ref:
                        t_template = t

                if t_template != "":
                    colB_name = cur_table[t].columns[1]
                    new_tab_name = ref_table_info[t_template]['New sheet name']

                    if str(colB_name) == 'Frame 0':  # Raw table format, fresh from Aivia, where 1 tab sheet = 1 measurement
                        # We copy the whole tab, but modify the name in A1 cell
                        new_table[new_tab_name] = cur_table[t].copy()

                        # A1 cell modification
                        if len(list(ref_table_info[t_template].keys())) > 2:
                            print(f"!!! Warning: unexpected number of measurement names to replace for tab: {ref}."
                                  f"\nCheck the name reference table.")

                        c = list(ref_table_info[t_template].keys())[1]
                        if "REGEX" in c:
                            constant_parts_2 = c.split("REGEX")
                            # print(f"'{c}' // '{constant_parts_2[0]}': {c.startswith(constant_parts_2[0])}")
                            if not (c.startswith(constant_parts_2[0]) and c.endswith(constant_parts_2[1])):
                                print(f"!!! Warning: measurement replacement does not match: {c} // {cur_table[t].columns[0]}")
                            else:
                                c_orig = cur_table[t].columns[0]
                        else:
                            c_orig = cur_table[t].columns[0]

                        new_table[new_tab_name].rename(columns={c_orig: ref_table_info[t_template][c]},
                                                       inplace=True)
                        t_count += 1
                        c_count += 1

                    else:           # Table was processed and may contain multiple columns for multiple measurements
                        # Prepare new tab, as only columns which were specified in the ref table will be copied to the new
                        new_table[new_tab_name] = pd.DataFrame(cur_table[t].iloc[:, 0].values,
                                                               index=cur_table[t].index, columns=[new_tab_name])
                        t_count += 1

                        # Add column with new headers, if in the list
                        col_names = cur_table[t].columns.tolist()
                        for c in col_names:
                            if c in ref_table_info[t].keys():
                                to_append = cur_table[t].loc[:, c]
                                new_c_name = ref_table_info[t_template][c]
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
                        col_letter = get_column_letter(c + 1)
                        len_header = len(str(new_table[sh].columns[c]))
                        len_values = len(str(new_table[sh].iat[0, c]))
                        len_longest_text = int(max(len_header, len_values, 5) * 1.2)
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
    if not params.get('debugMode', False):
        Mbox('Process completed', final_mess, 0)
    subprocess.run(["explorer.exe", output_folder])


def trigger_ref_table_creation(excel_file_ex_path, ):
    # Define paths
    cur_ref_names_path = os.path.join(os.path.dirname(excel_file_ex_path), '_Name reference table.xlsx')

    # Create ref table from the selected example Excel file, so that completion is easier
    first_table = pd.read_excel(excel_file_ex_path, sheet_name=None)
    ref_table_draft = create_ref_table_from_file(first_table)
    with pd.ExcelWriter(cur_ref_names_path, engine="openpyxl") as writer:
        ref_table_draft['Ref table'].to_excel(writer, sheet_name='Ref table', index=False)

        # Resizing columns
        for c in range(0, len(ref_table_draft['Ref table'].columns)):
            col_letter = get_column_letter(c + 1)
            len_header = len(str(ref_table_draft['Ref table'].columns[c]))
            r_max = min(20, ref_table_draft['Ref table'].iloc[:, c].size)
            len_values = max([len(str(ref_table_draft['Ref table'].iat[r_tmp, c])) for r_tmp in range(r_max)])
            len_longest_text = int(max(len_header, len_values, 8) * 1.2)
            writer.sheets['Ref table'].column_dimensions[col_letter].width = len_longest_text

    # Prompt to edit the reference table
    Mbox('Edit reference table', 'The draft of the reference table will open shortly.\n'
                                      '\n1. Complete the new names to replace the old ones'
                                      '\n2. Save the file and close it.'
                                      '\n\nYou can then come back to the script...', 0)

    # Opening the excel table
    os.startfile(cur_ref_names_path)

    # Prompt to edit the reference table
    ans = Mbox('Reference table ready?', 'Press "Ok" to continue with the edited reference table...', 1)

    if ans == "Cancel":
        sys.exit("Process aborted by user")

    return cur_ref_names_path


def scan_ref_table(df_from_excel):
    """
    :param df_from_excel: from the reading of the excel file. Keeps only the first two columns

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
    df_from_excel_2cols = df_from_excel.iloc[:, 0:2]

    for i, ro in df_from_excel_2cols.iterrows():
        if not ro.isna().values.all():
            # All subsequent info should be associated to the same sheet
            if not pd.isna(ro.iat[1]):
                if start_new_sheet:
                    tmp_sheet_name = ro.iat[0]
                    tmp_dict['New sheet name'] = ro.iat[1]
                    start_new_sheet = False

                else:
                    tmp_dict[ro.iat[0]] = ro.iat[1]       # expected to be column names

        else:
            if tmp_sheet_name:
                out_dict[tmp_sheet_name] = tmp_dict
            tmp_dict, tmp_sheet_name = {}, ""
            start_new_sheet = True

    if tmp_sheet_name:
        out_dict[tmp_sheet_name] = tmp_dict

    return out_dict


def create_ref_table_from_file(df_from_excel_file):
    """
    Expects a multi tab or sheets Excel input which results in a dictionary,
    where keys are tab names, and value is the pd.DataFrame
    :param df_from_excel_file: dictionary
    :return: dictionary with only one key (= one tab)
    """
    out_dict, ro_ind = {}, 0

    # Init output dict
    out_dict['Ref table'] = pd.DataFrame(columns=['Old name', 'New name', '', 'Type of entry'])

    for k in df_from_excel_file.keys():
        cur_tab = df_from_excel_file[k]

        # Name of tab
        out_dict['Ref table'].at[ro_ind, 'Old name'] = k
        out_dict['Ref table'].at[ro_ind, 'Type of entry'] = 'Sheet name'
        ro_ind += 1

        # Name of measurements
        if str(cur_tab.columns[1]) == 'Frame 0':
            out_dict['Ref table'].at[ro_ind, 'Old name'] = str(cur_tab.columns[0])
            out_dict['Ref table'].at[ro_ind, 'Type of entry'] = 'Measurement name'
            ro_ind += 1

        else:       # expectation: measurement names are in column B and more
            list_of_meas = cur_tab.columns[1:]
            for meas in list_of_meas:
                out_dict['Ref table'].at[ro_ind, 'Old name'] = meas
                out_dict['Ref table'].at[ro_ind, 'Type of entry'] = 'Measurement name'
                ro_ind += 1

        # Creating an empty row to separate tabs
        out_dict['Ref table'].at[ro_ind, 'Old name'] = ''
        out_dict['Ref table'].at[ro_ind, 'Type of entry'] = '---'
        ro_ind += 1

    return out_dict


def get_column_letter(col_num):
    result = ""
    while col_num > 0:
        col_num, remainder = divmod(col_num - 1, 26)
        result = chr(65 + remainder) + result
    return result


def ask_parameters_wpf(input_dict, ui_wi, ui_he, margin_v: int = 10):

    # Functions to create XAML code
    def create_radiobutton_xaml(dict_key, value_list):
        code = ''
        name_list = [f"{dict_key}RB{n}" for n in range(1, len(value_list) + 1)]

        is_checked = 'IsChecked="True" '
        for i in range(len(name_list)):
            code += f'<RadioButton Name="{name_list[i]}" {is_checked}Content="{value_list[i]}"/>'
            is_checked = ''  # reset

        return code

    def create_combobox_xaml(value_list):
        code = ''
        for i in range(len(value_list)):
            code += f'<ComboBoxItem Content="{value_list[i]}"/>'

        return code

    def create_listbox_xaml(list_name, value_list):
        code = f'<ListBox Name="{list_name}" SelectionMode="Extended">'

        for i in range(len(value_list)):
            code += f'<ListBoxItem>{value_list[i]}</ListBoxItem>'

        return code + '</ListBox>'

    def add_xaml_block_from_dict(input_key, input_value: dict, grid_number, margin_value):
        xaml_block = ''
        add_extra_grid_number = False
        if input_value["widget_type"] == "FileDialog":
            xaml_block = rf'''
                <TextBlock Grid.Row="{grid_number}" Margin="0,0,0,5" Text="{input_value['label']}"/>
                <DockPanel Grid.Row="{grid_number + 1}" Margin="0,0,0,{margin_value}">
                    <TextBox Name="{input_key}" Width="350" Margin="0,0,5,0"/>
                    <Button Name="{input_key}Browse" Width="80" Content="Browse"/>
                </DockPanel>
                '''
            add_extra_grid_number = True
        elif input_value["widget_type"] == "Label":
            xaml_block = rf'''
                <StackPanel Grid.Row="{grid_number}" Margin="{margin_value}">
                    <TextBlock Name="{input_key}" Text="{input_value['label']}" TextWrapping="Wrap"/>
                </StackPanel>
                '''
        elif input_value["widget_type"] in ["Int", "Double", "TextBox"]:
            default_v = input_value.get('choices', '')
            xaml_block = rf'''
                <StackPanel Grid.Row="{grid_number}" Margin="{margin_value}">
                    <TextBlock Text="{input_value['label']}"/>
                    <TextBox Name="{input_key}" Text="{default_v}"/>
                </StackPanel>
                '''
        elif input_value["widget_type"] == "Slider":
            minv, maxv, stepv, initv = input_value["choices"]
            xaml_block = rf'''
                <StackPanel Grid.Row="{grid_number}" Margin="{margin_value}">
                    <TextBlock Text="{input_value['label']}"/>
                    <Slider Name="{input_key}" Minimum="{minv}" Maximum="{maxv}" TickFrequency="{stepv}" IsSnapToTickEnabled="True" Value="{initv}"/>
                    <TextBlock Name="SLIDER_{input_key}" Text="{input_value['choices'][3]}" HorizontalAlignment="Center"/>
                </StackPanel>
                '''
        elif input_value["widget_type"] == "CheckBox":
            is_checked = input_value.get('choices', 'False')
            xaml_block = rf'''
                <CheckBox Grid.Row="{grid_number}" Name="{input_key}" Margin="0,0,0,{margin_value}" Content="{input_value['label']}" IsChecked="{is_checked}"/>
                '''
        elif input_value["widget_type"] == "RadioButtons":
            xaml_block = rf'''
                <GroupBox Grid.Row="{grid_number}" Header="{input_value['label']}" Margin="0,0,0,{margin_value}">
                    <StackPanel>{create_radiobutton_xaml(input_key, input_value['choices'])}</StackPanel>
                </GroupBox>
                '''
        elif input_value["widget_type"] == "ComboBox":
            xaml_block = rf'''
                <GroupBox Grid.Row="{grid_number}" Header="{input_value['label']}" Margin="0,0,0,{margin_value}">
                    <ComboBox Name="{input_key}" SelectedIndex="0">{create_combobox_xaml(input_value['choices'])}</ComboBox>
                </GroupBox>
                '''
        elif input_value["widget_type"] == "ListBox":
            xaml_block = rf'''
                <GroupBox Grid.Row="{grid_number}" Header="{input_value['label']}" Margin="0,0,0,{margin_value}">
                    {create_listbox_xaml(input_key, input_value['choices'])}
                </GroupBox>
                '''
        elif input_value["widget_type"] == "PushButton":
            button_width = input_value.get('choices', 0)
            xaml_block = rf'''
                <StackPanel Grid.Row="{grid_number}" Orientation="Horizontal" HorizontalAlignment="Right">
                    <Button Name="{input_key}" Width="{button_width}" Margin="{int(margin_value / 2)}" Content="{input_value['label']}"/>
                </StackPanel>
                '''
        elif input_value["widget_type"] == "OKButton":
            xaml_block = rf'''
                <StackPanel Grid.Row="{grid_number}" Orientation="Horizontal" HorizontalAlignment="Right">
                    <Button Name="{input_key}" Width="70" Margin="{int(margin_value / 2)}" Content="{input_value['label']}"/>
                    <Button Name="CancelButton" Width="70" Margin="{int(margin_value / 2)}" Content="Cancel"/>
                </StackPanel>
                '''
        return xaml_block, add_extra_grid_number

    def create_xaml_code(input_dict, width, height):
        all_widget_types = [v['widget_type'] for k, v in input_dict.items()]
        n_double_rows = 0
        for wt in all_widget_types:
            if wt == "FileDialog":
                n_double_rows = n_double_rows + 1

        n_def = len(input_dict) + n_double_rows

        # Code for row definitions
        row_def_code = ''.join([f'<RowDefinition Height="Auto"/>' for _ in range(n_def)])

        # Code for all items
        all_block_code = ''
        grid_no = 0
        for k, v in input_dict.items():
            code, do_increment_grid_no = add_xaml_block_from_dict(k, v, grid_no, margin_v)
            all_block_code += code
            grid_no = grid_no + 2 if do_increment_grid_no else grid_no + 1

        xaml_code = rf'''
            <Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
                    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
                    Title="Aivia Parameters" Width="{width}" Height="{height}"
                    WindowStartupLocation="CenterScreen">

                <Grid Margin="10">
                    <Grid.RowDefinitions>{row_def_code}</Grid.RowDefinitions>
                    {all_block_code}
                </Grid>
            </Window>
        '''
        return xaml_code

    # Functions to create PowerShell code
    def ps_find(full_dict):
        names = []
        for k in full_dict.keys():
            if full_dict[k]['widget_type'] == "RadioButtons":
                names += [f"{k}RB{n}" for n in range(1, len(full_dict[k]['choices']) + 1)]
            elif full_dict[k]['widget_type'] == "FileDialog":
                names += [k, f'{k}Browse']
            elif full_dict[k]['widget_type'] == "OKButton":
                names += [k, "CancelButton"]
            elif full_dict[k]['widget_type'] == "Slider":
                names += [k, f"SLIDER_{k}"]
            else:
                names.append(k)

        return "\n".join(
            f'${name} = W "{name}"'
            for name in names
        )

    def create_slider_update_code(full_dict):
        entries = []
        for k in full_dict.keys():
            if full_dict[k]['widget_type'] == "Slider":
                entries.append(k)

        return "\n".join(
            f'${entry}.Add_ValueChanged({{$SLIDER_{entry}.Text = [int]${entry}.Value}})'
            for entry in entries
        )

    def ps_click(control, code):
        return f'''
${control}.Add_Click({{
{code}
}})
'''

    def ps_file_dialog(target, file_filter):
        return f'''
$dlg = New-Object System.Windows.Forms.OpenFileDialog
$dlg.Filter = "{file_filter}"

if($dlg.ShowDialog() -eq 'OK')
{{
    ${target}.Text = $dlg.FileName
}}
'''

    def ps_radio_choice(var_name, value_list):
        blocks = []
        name_list = [f"{var_name}RB{n}" for n in range(1, len(value_list) + 1)]

        for i in range(len(name_list)):
            if i == 0:
                prefix = f"if(${name_list[i]}.IsChecked)"
            elif i < len(name_list) - 1:
                prefix = f"elseif(${name_list[i]}.IsChecked)"
            else:
                prefix = "else"

            blocks.append(f'''
{prefix} {{${var_name} = "{value_list[i]}"}}
''')

        return "\n".join(blocks)

    def ps_combobox_choice(var_name, value_list):
        blocks = [f'switch (${var_name}.SelectedIndex) {{']

        for i in range(len(value_list)):
            blocks.append(f'''
{i} {{${var_name} = "{value_list[i]}"}}
''')
        blocks.append('}')
        return "\n".join(blocks)

    def ps_action(var_name, option_list):
        # Powershell action, example below
        code = rf'''
            [System.Windows.MessageBox]::Show("Hello", "Extra popup")
            '''
        return code

    # Expect dict in the form of keys = variable names, values = dict{"label", "widget_type", "choices"...}
    def ps_json_return(fields):
        # Specific function to return multiple choices for a MultiSelection element
        def ps_selected_items(list_name):
            return f'''
            @(
                ${list_name}.SelectedItems | ForEach-Object {{ $_.Content }}
            )
            '''

        content = ""
        for k in fields.keys():
            var_type = fields[k].get("widget_type")
            if var_type == "TextBox":
                content += f"    {k} = ${k}.Text\n"
            elif var_type == "Int":
                content += f"    {k} = [int]${k}.Text\n"
            elif var_type == "Double":
                content += f"    {k} = [double]${k}.Text\n"
            elif var_type == "Slider":
                content += f"    {k} = [int]${k}.Value\n"
            elif var_type == "CheckBox":
                content += f"    {k} = ${k}.IsChecked\n"
            elif var_type == "RadioButtons":
                content += f"    {k} = ${k}\n"
            elif var_type == "ComboBox":
                content += f"    {k} = ${k}\n"
            elif var_type == "ListBox":
                content += f"    {k} = {ps_selected_items(k)}\n"
            elif var_type == "FileDialog":
                content += f"    {k} = ${k}.Text\n"

        return f'''
        $result = @{{
        {content}
        }}

        $window.Tag = $result | ConvertTo-Json -Compress
        $window.Close()
        '''

    def create_fdialog_button_call_code(input_dict):
        button_call_code = ''
        all_widget_types = [v['widget_type'] for k, v in input_dict.items()]
        if "FileDialog" in all_widget_types:
            all_filedialogs = [(k, v) for k, v in input_dict.items() if v['widget_type'] == "FileDialog"]

            if all_filedialogs:
                for k, v in all_filedialogs:
                    k_browse = f'{k}Browse'
                    button_call_code += f'{ps_click(k_browse, ps_file_dialog(k, v["choices"]))}'

        return button_call_code

    def create_push_button_call_code(input_dict):
        button_call_code = ''
        all_widget_types = [v['widget_type'] for k, v in input_dict.items()]
        if "PushButton" in all_widget_types:
            all_filedialogs = [(k, v) for k, v in input_dict.items() if v['widget_type'] == "PushButton"]

            if all_filedialogs:
                for k, v in all_filedialogs:
                    button_call_code += f'{ps_click(k, ps_action(k, v["choices"]))}'

        return button_call_code

    def create_radiobuttons_code(input_dict):
        radiobuttons_code = ''
        all_widget_types = [v['widget_type'] for k, v in input_dict.items()]
        if "RadioButtons" in all_widget_types:
            all_rb = [(k, v) for k, v in input_dict.items() if v['widget_type'] == "RadioButtons"]

            if all_rb:
                for k, v in all_rb:
                    radiobuttons_code += f'{ps_radio_choice(k, v['choices'])}'

        return radiobuttons_code

    def create_combobox_code(input_dict):
        combobox_code = ''
        all_widget_types = [v['widget_type'] for k, v in input_dict.items()]
        if "RadioButtons" in all_widget_types:
            all_cb = [(k, v) for k, v in input_dict.items() if v['widget_type'] == "ComboBox"]

            if all_cb:
                for k, v in all_cb:
                    combobox_code += f'{ps_combobox_choice(k, v['choices'])}'

        return combobox_code

    # Now preparing the final Powershell Script
    ps_script = f'''
Add-Type -AssemblyName PresentationFramework
Add-Type -AssemblyName System.Windows.Forms

[xml]$xaml = @"
{create_xaml_code(input_dict, ui_wi, ui_he)}
"@

$reader = New-Object System.Xml.XmlNodeReader $xaml
try {{
    $window = [Windows.Markup.XamlReader]::Load($reader)
}}
catch {{
    $_.Exception
    $_.Exception.InnerException
    $_.Exception.InnerException.InnerException
}}

function W($name) {{ $window.FindName($name) }}

{ps_find(input_dict)}
{create_slider_update_code(input_dict)}

{create_fdialog_button_call_code(input_dict)}
{create_push_button_call_code(input_dict)}

$CallButton.Add_Click({{
    {create_radiobuttons_code(input_dict)}
    {create_combobox_code(input_dict)}
    {ps_json_return(input_dict)}
}})

$CancelButton.Add_Click({{
    $window.Tag = ""
    $window.Close()
}})

[void]$window.ShowDialog()

$window.Tag
'''
    # print(ps_script)

    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_script],
        capture_output=True,
        text=True
    )

    # print("RC=", result.returncode)
    # print("STDOUT=", repr(result.stdout))
    # print("STDERR=", repr(result.stderr))

    txt = result.stdout.strip()
    print("UI Output: ", txt)

    if not txt:
        print("No output detected")
        return None

    return json.loads(txt)


def Mbox(title, text, style):
    style_tags = ["OkOnly", "OkCancel", "YesNo", "YesNoCancel"]
    cmd = [
        "powershell",
        "-Command",
        "Add-Type -AssemblyName Microsoft.VisualBasic; "
        f"$x=[Microsoft.VisualBasic.Interaction]::MsgBox('{text}', "
        f"[Microsoft.VisualBasic.MsgBoxStyle]::{style_tags[style]}, '{title}');"
        "Write-Output $x"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return result.stdout.strip()        # return = "Ok" or "Cancel"
    except:
        return None


if __name__ == '__main__':
    di = r'D:\PythonCode\Python_scripts\Projects\ExcelFileHandling\tests'
    params = {'inputPath': di + r'\_Wiki_3D Obj Tracking-Demo_10.5_R_2 track sets for distance-angle.aivia.tif',
              'resultPath': di + r'\_Wiki_3D Obj Tracking-Demo_10.5_R_angle_map.tif',
              'debugMode': True}
    run(params)

# Changelog:
# v1.00: - First version only keeping columns which are listed in the ref table. Others are not kept.
# v1.10: - Adding the ability to prefill an excel table with the existing tabs and column names
# v1.20: - Adding the possibility to provide old names with "REGEX" in the name meaning this would be a variable part
#        - Mbox and MagicGui to VB for Aivia 16
