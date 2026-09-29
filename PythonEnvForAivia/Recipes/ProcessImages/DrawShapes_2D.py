import os
import sys
import numpy as np
from skimage.io import imread, imsave
from skimage import draw
import subprocess
import json

"""
Create shapes in 2D or 2D+t images.

Documentation
------------
https://scikit-image.org/docs/stable/api/skimage.draw.html
https://scikit-image.org/docs/stable/auto_examples/edges/plot_shapes.html#sphx-glr-auto-examples-edges-plot-shapes-py

Requirements
------------
numpy
scikit-image
magicgui

Parameters
----------
Input channel:
    Any channel, just passing dimensions and pixel resolution used for shape size definition.

Returns
-------
Channel in Aivia
"""


# [INPUT Name:inputImagePath Type:string DisplayName:'Any channel']
# [OUTPUT Name:resultPath Type:string DisplayName:'Shape mask']
def run(params):
    image_location = params['inputImagePath']
    result_location = params['resultPath']
    zCount = int(params['ZCount'])
    tCount = int(params['TCount'])
    unit_test = True if 'unitTest' in params.keys() else False
    external_output = True if 'externalOutput' in params.keys() else False

    if not os.path.exists(image_location):
        print(f"Error: {image_location} does not exist")
        return
    if zCount > 1:
        error_mess = 'Error: script is not compatible with 3D images'
        Mbox('Error', error_mess, 0)
        sys.exit(error_mess)

    pixel_cal_tmp = params['Calibration']
    pixel_cal = pixel_cal_tmp[6:].split(', ')           # Expects calibration with 'XYZT: ' in front
    XY_cal = float(pixel_cal[0].split(' ')[0])

    image_data = imread(image_location)
    dims = image_data.shape
    bitdepth = image_data.dtype
    bitdepth_max = np.iinfo(bitdepth).max
    print('-- Input dimensions (expected (T,) (Z,) Y, X): ', np.asarray(dims), ' --')

    # Define shape
    dim_shift = 1 if tCount > 1 else 0
    max_x = dims[1 + dim_shift]
    max_y = dims[dim_shift]
    image_center = get_image_center(max_y, max_x)       # WARNING: Y, X due to shape constraint

    # SHAPE DEFINITIONS ------------------------
    def draw_disk(shape_YX_pos, shape_width, image_XYshape):
        return draw.disk(shape_YX_pos, shape_width / 2, shape=image_XYshape)

    def draw_circle(shape_YX_pos, shape_width, image_XYshape):
        return draw.circle_perimeter(int(shape_YX_pos[0]), int(shape_YX_pos[1]), int(shape_width / 2), shape=image_XYshape)

    def draw_circle_aa(shape_YX_pos, shape_width, image_XYshape):
        return draw.circle_perimeter_aa(int(shape_YX_pos[0]), int(shape_YX_pos[1]), int(shape_width / 2), shape=image_XYshape)

    def draw_ellipse(shape_YX_pos, shape_width, shape_height, image_XYshape):       # X/Y are inverted!!
        return draw.ellipse(int(shape_YX_pos[0]), int(shape_YX_pos[1]), int(shape_height / 2), int(shape_width / 2),
                            shape=image_XYshape)

    def draw_ellipse_perimeter(shape_YX_pos, shape_width, shape_height, image_XYshape):
        return draw.ellipse_perimeter(int(shape_YX_pos[0]), int(shape_YX_pos[1]), int(shape_height / 2), int(shape_width / 2),
                                      shape=image_XYshape)

    def draw_rectangle(shape_YX_pos, rect_width, rect_height, image_XYshape):
        rect_center = int(shape_YX_pos[0]), int(shape_YX_pos[1])
        rect_start = int(rect_center[0] - (rect_height / 2)), int(rect_center[1] - (rect_width / 2))
        rect_end = int(rect_center[0] + (rect_height / 2)), int(rect_center[1] + (rect_width / 2))
        return draw.rectangle(start=rect_start, end=rect_end, shape=image_XYshape)

    def draw_rectangle_perimeter(shape_YX_pos, rect_width, rect_height, image_XYshape):
        rect_center = int(shape_YX_pos[0]), int(shape_YX_pos[1])
        rect_start = int(rect_center[0] - (rect_height / 2)), int(rect_center[1] - (rect_width / 2))
        rect_end = int(rect_center[0] + (rect_height / 2)), int(rect_center[1] + (rect_width / 2))
        return draw.rectangle_perimeter(start=rect_start, end=rect_end, shape=image_XYshape)

    def draw_line(shape_YX_pos, X_end, Y_end, image_XYshape):
        line_start_X = int(shape_YX_pos[1])
        line_start_Y = int(shape_YX_pos[0])
        line_end_X = int(X_end)
        line_end_Y = int(Y_end)
        return draw.line(line_start_Y, line_start_X, line_end_Y, line_end_X)

    shapes = {'Disk': draw_disk, 'Circle': draw_circle, 'Smoothed Circle': draw_circle_aa,
              'Ellipse (plain shape)': draw_ellipse, 'Ellipse contour': draw_ellipse_perimeter,
              'Rectangle (plain shape)': draw_rectangle, 'Rectangle contour': draw_rectangle_perimeter,
              'Line': draw_line}
    # /SHAPE DEFINITIONS -----------------------

    # GUI: Each entry is expected to have: label, widget_type, choices (if needed)
    # A file browser is automatically bound to a "BrowseButton" in the same grid no. Same with "CallButton" and "Cancel"
    # Slider choices = min, max, step, init-value (all should be integer)
    ui_width, ui_height = 540, 500
    info_dict = {
                'shape_c': {"label": "Shape:",
                            "widget_type": "RadioButtons",
                            'choices': list(shapes.keys())},
                'shape_center_X_c': {"label": "X coordinate of shape center (calibrated from original image): ",
                                     "widget_type": "Double", "choices": image_center[1] * XY_cal},
                'shape_center_Y_c': {"label": "Y coordinate of shape center (calibrated from original image): ",
                                     "widget_type": "Double", "choices": image_center[0] * XY_cal},
                'shape_width_c': {"label": "Width (calibrated from original image): ",
                                  "widget_type": "Double", "choices": image_center[1] * XY_cal},
                'shape_height_c': {"label": "[Optional for disk/circle] Height (calibrated from original image): ",
                                   "widget_type": "Double", "choices": image_center[0] * XY_cal},
                'CallButton': {"label": "Draw", "widget_type": "OKButton"}
                }

    if unit_test:     # UNIT TEST
        selected_shape = info_dict['shape_c']["choices"][0]
        selected_position = (float(info_dict['shape_center_Y_c']["choices"]) / XY_cal,
                             float(info_dict['shape_center_X_c']["choices"]) / XY_cal)    # Y, X
        selected_width = float(info_dict['shape_width_c']["choices"]) / XY_cal
        selected_height = float(info_dict['shape_height_c']["choices"]) / XY_cal

    else:
        params_ui = ask_parameters_wpf(info_dict, ui_width, ui_height, 5)

        selected_shape = params_ui['shape_c']
        selected_position = float(params_ui['shape_center_Y_c']) / XY_cal, float(params_ui['shape_center_X_c']) / XY_cal    # Y, X
        selected_width = float(params_ui['shape_width_c']) / XY_cal
        selected_height = float(params_ui['shape_height_c']) / XY_cal

    # Collect shape mask indexes
    image_XY_shape = (dims[dim_shift], dims[1 + dim_shift])
    if any([t in selected_shape for t in ['Ellipse', 'Rectangle', 'Line']]):
        draw_args = selected_position, selected_width, selected_height, image_XY_shape
    else:
        draw_args = selected_position, selected_width, image_XY_shape

    shape_np_indexes = shapes[selected_shape](*draw_args)
    if len(shape_np_indexes) == 3:
        rr, cc, val = shape_np_indexes
    else:
        rr, cc = shape_np_indexes
        val = 1

    # Draw shape in numpy array
    output_data = np.zeros_like(image_data)
    if tCount > 1:
        output_data[:, rr, cc] = val * bitdepth_max
    else:
        output_data[rr, cc] = val * bitdepth_max

    if external_output:
        # Defining axes for output metadata and scale factor variable
        axes = 'YX' if tCount == 1 else 'TYX'
        meta_info = {'axes': axes}

        imsave(result_location, output_data, imagej=True, photometric='minisblack', metadata=meta_info)
    else:
        imsave(result_location, output_data)


def get_image_center(height, width):
    return height / 2, width / 2


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
        return result.stdout.strip()  # return = "Ok" or "Cancel"
    except:
        return None


if __name__ == '__main__':
    params = {'inputImagePath': r'D:\PythonCode\_tests\XYT_160x160x16_1ch_8bit_nuclei-fluo_embryo_APP-2Dalign_IJ1.53t.tif',
              'resultPath': r'D:\PythonCode\_tests\output.tif',
              'ZCount': 1,
              'TCount': 16,
              'Calibration': 'XYZT: 1 micrometers, 1 micrometers, 1 micrometers, 1 Default',
              'externalOutput': 1}

    run(params)

# CHANGELOG
# v1.00: - using Skimage.draw shapes. Adding virtual env for GUI
# v1.01: - New virtual env code for auto-activation
# v1.10: - Changed ctypes Mbox and MagicGui to VB, and then removing Env need
# v1.11: - Removed UI for unit test and using default values
