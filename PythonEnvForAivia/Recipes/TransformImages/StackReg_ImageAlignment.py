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

from skimage.io import imread, imsave
import numpy as np
from pystackreg import StackReg
from pystackreg.util import to_uint16
import imagecodecs
import subprocess, json

# Manual input parameters (only used if 'use' is True below)
noGUI_params = {'use': False,
                'reg_type': 'Translation only',
                'reg_method': 'Previous image is the reference (original StackReg ImageJ plugin)'
                }

"""
Performs a 2D registration for timelapses, using PyStackReg. No parameters available (default ones only).
Methods:
- Previous = Use previous image to calculate registration
- First = First timepoint is used as the fixed reference.

Documentation: https://pypi.org/project/pystackreg/
Paper for citation available at the bottom of page above.

Requirements
------------
scikit-image
numpy
imagecodecs
pystackreg

Parameters
----------
Input:
    Channel/image in Aivia to be aligned
  
Output
------
New channel with registered images
"""

reg_methods = {
    'Previous image is the reference (original StackReg ImageJ plugin)': 'previous',
    'First image is the reference': 'first',
    'Mean of all images is the reference': 'mean'
    }
reg_types = {
    'Translation only': StackReg.TRANSLATION,
    'Rigid Body (translation + rotation)': StackReg.RIGID_BODY,
    'Affine (translation + rotation + scaling + shearing)': StackReg.AFFINE,
    'Bilinear (non-linear transformation; does not preserve straight lines)': StackReg.BILINEAR
}

# [INPUT Name:inputRawImagePath Type:string DisplayName:'Unregistered stack']
# [OUTPUT Name:resultPath Type:string DisplayName:'Registered stack']
def run(params):
    global reg_methods, reg_types

    rawImageLocation = params['inputRawImagePath']
    resultLocation = params['resultPath']
    calibration = params['Calibration']
    tCount = int(params['TCount'])
    zCount = int(params['ZCount'])

    if tCount < 2:
        show_error(f'Error: detected dimensions do not contain time. (t={tCount})')
    if zCount > 1 and tCount > 1:
        show_error(f'Error: detected dimensions contain time and depth. This script is for 2D only. (t={tCount}, z={zCount})')

    # Checking existence of temporary files (individual channels)
    if not os.path.exists(rawImageLocation):
        show_error(f'Error: {rawImageLocation} does not exist')

    # Loading input image
    raw_npimg = imread(rawImageLocation)
    raw_dims = np.asarray(raw_npimg.shape)
    print('-- Input dimensions (expected T, Z, Y, X): ', raw_dims, ' --')

    # Checking Time axis
    if raw_npimg.shape[0] != tCount:
        show_error(f'Error: time dimension was not found on axis 1 (TYX).'
                   f'\nContact support team, mentioning if image was cropped or not.')

    # Preparing output
    final_img = np.zeros(raw_npimg.shape).astype(raw_npimg.dtype)

    # Check manual inputs
    if noGUI_params['use'] or params.get('unitTest', False):
        reg_type = reg_types[noGUI_params['reg_type']]
        reg_method = reg_methods[noGUI_params['reg_method']]

    else:  # Choose with GUI
        # GUI: Each entry is expected to have: label, widget_type, choices (if needed)
        # A file browser is automatically bound to a "BrowseButton" in the same grid no. Same with "CallButton" and "Cancel"
        # Slider choices = min, max, step, init-value (all should be integer)
        ui_width, ui_height = 540, 280
        info_dict = {
            'reg_typ': {'label': 'Registration type: ', "widget_type": "RadioButtons", 'choices': list(reg_types.keys())},
            'reg_meth': {'label': 'Registration reference: ', "widget_type": "RadioButtons", 'choices': list(reg_methods.keys())},
            'CallButton': {"label": "Process", "widget_type": "OKButton"}
        }

        params_ui = ask_parameters_wpf(info_dict, ui_width, ui_height, 5)

        # Parameters collected from the GUI
        reg_type = reg_types[params_ui['reg_typ']]
        reg_method = reg_methods[params_ui['reg_meth']]

    # Prepare parameters for registration
    sr = StackReg(reg_type)

    # Register 2D timelapse
    out_npimg = sr.register_transform_stack(raw_npimg, reference=reg_method)

    print(f'Raw image: Min = {np.min(raw_npimg)}, Max = {np.max(raw_npimg)}')
    print(f'Processed image: Min = {np.min(out_npimg)}, Max = {np.max(out_npimg)}')

    test = np.histogram(raw_npimg[0])
    test2 = np.histogram(out_npimg[0])

    # Formatting result array
    # print(raw_npimg.dtype)
    if raw_npimg.dtype is np.dtype('uint8'):
        final_img = out_npimg.clip(min=0, max=255).astype(raw_npimg.dtype)
    else:
        final_img = to_uint16(out_npimg).astype(raw_npimg.dtype)

    print(f'Final image: Min = {np.min(final_img)}, Max = {np.max(final_img)}')

    # Save result
    imsave(resultLocation, final_img)


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
                    <Button Name="BrowseButton" Width="80" Content="Browse"/>
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
            xaml_block = rf'''
                <CheckBox Grid.Row="{grid_number}" Name="{input_key}" Margin="0,0,0,{margin_value}" Content="{input_value['label']}"/>
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
        elif input_value["widget_type"] == "OKButton":
            xaml_block = rf'''
                <StackPanel Grid.Row="{grid_number}" Orientation="Horizontal" HorizontalAlignment="Right">
                    <Button Name="{input_key}" Width="70" Margin="{int(margin_value / 2)}" Content="{input_value['label']}"/>
                    <Button Name="CancelButton" Width="70" Margin="{int(margin_value / 2)}" Content="Cancel"/>
                </StackPanel>
                '''
        return xaml_block, add_extra_grid_number

    def create_xaml_code(input_dict, width, height):
        n_def = len(input_dict)
        if "FilePath" in input_dict:
            n_def += 1  # For Browse button

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
                names += [k, "BrowseButton"]
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
                    button_call_code += f'{ps_click("BrowseButton", ps_file_dialog(k, v["choices"]))}'

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
    # print("Leading spaces: ", detect_leading_whitespace(ps_script))
    # print("Non-Breaking spaces: ", detect_non_breaking_spaces(ps_script))

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


def show_error(message):
    cmd = [
        "powershell",
        "-Command",
        "Add-Type -AssemblyName Microsoft.VisualBasic; "
        f"$x=[Microsoft.VisualBasic.Interaction]::MsgBox('{message}', "
        f"[Microsoft.VisualBasic.MsgBoxStyle]::OkOnly, 'Error');"
        "Write-Output $x"
    ]
    subprocess.run(cmd, capture_output=True, text=True)
    sys.exit(message)


if __name__ == '__main__':
    params = {}
    params['inputRawImagePath'] = r'D:\PythonCode\Python_scripts\Projects\PythonEnvForAivia_A16.0_Py3.12\Tests' \
                                  r'\_InputImages\Test_16bit_TYX_Particles.tif'               # T=20
    params['resultPath'] = r'D:\PythonCode\_tests\2D-TL-aligned.tif'
    params['Calibration'] = '  : 0.4 microns, 0.4 microns, 1.2 microns, 2 seconds'
    params['TCount'] = 20
    params['ZCount'] = 1

    run(params)

# CHANGELOG
# v1_00 PM: - Registration with default parameters of PyStackReg
# v1_01 PM: - New virtual env code for auto-activation
# v1_10 PM: - Works in 15.0 but black pixels instead of white saturated ones are present in resulting image.
# v1_11 PM: - Fixed black and white pixels in registered images for 8 bit images
# v1_20 PM: - Changed show_error to VB and magicgui to VB too
