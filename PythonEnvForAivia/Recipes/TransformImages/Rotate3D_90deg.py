import os
import sys
import shlex, subprocess, json
import imagecodecs
import numpy as np
from skimage import transform
from skimage.util import img_as_uint, img_as_ubyte
from tifffile import imread, imwrite
import re

DEFAULT_OUTPUT_FOLDER = r''

"""
Scales the input channel up or down (isotropic factor) and rotates the volume 90 degrees around one axis (not centered).
Works only for 3D (not timelapses) and for single channels.

Requirements
------------
numpy
scikit-image
imagecodecs
tifffile

Parameters
----------
Input channel:
    Input channel to be scaled.

Returns
-------
New channel in original image:
    Returns an empty channel.

New image:
    Opens Aivia to display the new scaled image.

"""

DEBUG_MODE = False

axis_rot_options = {'ClockWise': {'X': (1, 0), 'Y': (0, 2), 'Z': (2, 1)},
                    'CounterClockWise': {'X': (0, 1), 'Y': (2, 0), 'Z': (1, 2)}}
interpolation_mode = 1  # 0: Nearest-neighbor, 1: Bi-linear , 2: Bi-quadratic, 3: Bi-cubic, 4: Bi-quartic, 5: Bi-quintic

# [INPUT Name:inputImagePath Type:string DisplayName:'Input Channel']
# [OUTPUT Name:resultPath Type:string DisplayName:'Duplicate of input']
def run(params):
    global axis_rot_options, interpolation_mode
    image_location = params['inputImagePath']
    result_location = params['resultPath']
    zCount = int(params['ZCount'])
    tCount = int(params['TCount'])
    pixel_cal_tmp = params['Calibration']
    pixel_cal = pixel_cal_tmp[6:].split(', ')           # Expects calibration with 'XYZT: ' in front
    aivia_path = params['CallingExecutable'].replace('.dll', '.exe')

    # Getting XY and Z calibration values                # Expecting only 'Micrometers' in this code
    XY_cal = float(pixel_cal[0].split(' ')[0])
    Z_cal = float(pixel_cal[2].split(' ')[0])
    Z_ratio = float(Z_cal) / float(XY_cal)
    
    if not os.path.exists(image_location):
        print(f"Error: {image_location} does not exist")
        return

    if not 'fileOutputPath_2' in params.keys() and not os.path.exists(aivia_path):
        print(f"Error: {aivia_path} does not exist")
        return

    raw_data = imread(image_location)
    dims = raw_data.shape
    print('-- Input dimensions (expected (Z), Y, X): ', np.asarray(dims), ' --')

    # Checking image is not 2D+t or 3D+t
    if len(dims) != 3 or (len(dims) == 3 and tCount > 1):
        print('Error: Image should be XYZ only.')
        return

    # Scale image to be isotropic
    final_cal = XY_cal
    scale_factor_xy = 1
    scale_factor_z = 1
    if Z_ratio > 1:
        scale_factor_z = Z_ratio
    elif Z_ratio < 1:
        scale_factor_xy = 1 / Z_ratio
        final_cal = Z_cal

    if abs(Z_ratio - 1) > 0.001:
        print('-- Rescaling image as XY and Z calibration are different')
        final_scale = (scale_factor_z, scale_factor_xy, scale_factor_xy)
        iso_data = transform.rescale(raw_data, final_scale, interpolation_mode)
    else:
        iso_data = raw_data

    # GUI to choose rotation axis
    swap_axes_options = axis_rot_options['ClockWise']

    json_ui_values = wpf_xaml_UI({'Axis': {"label": "Select the rotation axis:",
                                           "widget_type": "RadioButtons",
                                           'choices': list(swap_axes_options.keys())},
                                  'Direction': {"label": "Select the rotation direction:",
                                                "widget_type": "RadioButtons",
                                                'choices': list(axis_rot_options.keys())},
                                  'OKButton': {"label": "Run", "widget_type": "OKButton"},
                                  'CancelButton': {"label": "Cancel", "widget_type": "CancelButton"}
                                  })

    if not json_ui_values:
        sys.exit("UI cancelled by user")

    rot_axis = json_ui_values['Axis']
    rot_dir = json_ui_values['Direction']

    # Rotation
    rot_axes = axis_rot_options[rot_dir][rot_axis]
    processed_data = np.rot90(iso_data, axes=rot_axes)

    # Formatting result array
    if raw_data.dtype is np.dtype('u2'):
        out_data = img_as_uint(processed_data)
    else:
        out_data = img_as_ubyte(processed_data)

    # Defining axes for output metadata and scale factor variable
    axes = 'ZYX'
    meta_info = {'axes': axes, 'spacing': str(final_cal), 'unit': 'um'}   # TODO: change to TZCYX for ImageJ style???

    # Formatting voxel calibration values
    inverted_XY_cal = 1 / final_cal

    # Output path depending on test mode or not
    if 'fileOutputPath_2' in params.keys():
        out_path = params['fileOutputPath_2']
    else:
        # Evaluate possible output in a user-defined folder
        if DEFAULT_OUTPUT_FOLDER:
            output_folder = DEFAULT_OUTPUT_FOLDER
        else:
            output_folder = os.path.dirname(result_location)

        # Attempt to collect name of current image (+bitdepth)
        out_path = ''
        if params.get("RawImageMetadata"):
            match = re.search(r'^(.*?)\s\(Dims\s.*?\|\sCalibration', params['RawImageMetadata'])
            if match is not None:
                img_name = match.groups()[0]
                output_name = f"{img_name}_Rot{rot_axis}-{rot_dir}.tif"

                out_path = os.path.join(output_folder, output_name)

        if not out_path:
            out_path = result_location.replace('.tif', 'tmp.tif')

    print('Saving image in temp location:\n', out_path)
    imwrite(out_path, out_data, imagej=True, photometric='minisblack', metadata=meta_info,
            resolution=(inverted_XY_cal, inverted_XY_cal))

    # Added for handling testing without opening aivia
    if aivia_path == "None":
        return

    # Dummy save
    dummy_data = np.zeros(raw_data.shape, dtype=raw_data.dtype)
    imwrite(result_location, dummy_data)

    # Write UI parameters to file if needed
    mess = write_ui_param_in_file(json.dumps(json_ui_values))
    print(mess)

    # Run external program
    cmdLine = 'start \"\" \"' + aivia_path + '\" \"' + out_path + '\"'

    args = shlex.split(cmdLine)
    subprocess.run(args, shell=True)


def wpf_xaml_UI(info_dict) -> dict:
    params_ui = ask_parameters_wpf(info_dict)

    if params_ui is None:
        return {}

    return params_ui


def ask_parameters_wpf(info_dict):
    # Functions to create XAML code
    def create_radiobutton_xaml(dict_key, full_dict):
        code = ''
        value_list = full_dict[dict_key]['choices']
        name_list = [f"{dict_key}RB{n}" for n in range(1, len(value_list) + 1)]

        if len(name_list) != len(value_list):
            sys.exit("Error creating radiobutton code")

        is_checked = 'IsChecked="True" '
        for i in range(len(name_list)):
            code += f'<RadioButton Name="{name_list[i]}" {is_checked}Content="{value_list[i]}"/>'
            is_checked = ''  # reset

        return code

    xaml_code = rf'''
        <Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
                xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
                Title="Aivia Parameters" Width="500" Height="260"
                WindowStartupLocation="CenterScreen">

            <Grid Margin="10">
                <Grid.RowDefinitions>
                    <RowDefinition Height="Auto"/>
                    <RowDefinition Height="Auto"/>
                    <RowDefinition Height="Auto"/>
                </Grid.RowDefinitions>

                <GroupBox Grid.Row="0" Header="{info_dict["Axis"]["label"]}" Margin="0,0,0,10">
                    <StackPanel>{create_radiobutton_xaml("Axis", info_dict)}</StackPanel>
                </GroupBox>

                <GroupBox Grid.Row="1" Header="{info_dict["Direction"]["label"]}" Margin="0,0,0,10">
                    <StackPanel>{create_radiobutton_xaml("Direction", info_dict)}</StackPanel>
                </GroupBox>

                <StackPanel Grid.Row="2" Orientation="Horizontal" HorizontalAlignment="Right">
                    <Button Name="OKButton" Width="70" Margin="5" Content="{info_dict["OKButton"]["label"]}"/>
                    <Button Name="CancelButton" Width="70" Margin="5" Content="Cancel"/>
                </StackPanel>
            </Grid>
        </Window>
    '''

    # Functions to create PowerShell code
    def ps_find(full_dict):
        names = []
        for k in full_dict.keys():
            if full_dict[k]['widget_type'] == "RadioButtons":
                names += [f"{k}RB{n}" for n in range(1, len(full_dict[k]['choices']) + 1)]
            else:
                names.append(k)

        return "\n".join(
            f'${name} = W "{name}"'
            for name in names
        )

    def ps_radio_choice(var_name, in_dict):
        blocks = []
        value_list = in_dict[var_name]['choices']
        name_list = [f"{var_name}RB{n}" for n in range(1, len(value_list) + 1)]

        for i in range(len(name_list)):
            if i == 0:
                prefix = f"if(${name_list[i]}.IsChecked)"
            elif i < len(name_list) - 1:
                prefix = f"elseif(${name_list[i]}.IsChecked)"
            else:
                prefix = "else"

            blocks.append(f'''
            {prefix}
            {{${var_name} = "{value_list[i]}"}}''')

        return "\n".join(blocks)

    # Expect dict in the form of keys = variable names, values = dict{"label", "widget_type", "choices"...}
    def ps_json_return(fields):
        # Specific function to return multiple choices for a MultiSelection element
        def ps_selected_items(list_name):
            return f'''
            @(
                ${list_name}.SelectedItems |
                ForEach-Object {{ $_.Content }}
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
            elif var_type == "CheckBox":
                content += f"    {k} = ${k}.IsChecked\n"
            elif var_type == "RadioButtons":
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

    ps_script = f'''
Add-Type -AssemblyName PresentationFramework
Add-Type -AssemblyName System.Windows.Forms

[xml]$xaml = @"
{xaml_code}
"@

$reader = New-Object System.Xml.XmlNodeReader $xaml
$window = [Windows.Markup.XamlReader]::Load($reader)
function W($name) {{ $window.FindName($name) }}

{ps_find(info_dict)}

$OKButton.Add_Click({{
    {ps_radio_choice("Axis", info_dict)}
    {ps_radio_choice("Direction", info_dict)}

    {ps_json_return(info_dict)}
}})

$CancelButton.Add_Click({{
    $window.Tag = ""
    $window.Close()
}})

[void]$window.ShowDialog()

$window.Tag
    '''

    # DEBUG
    if DEBUG_MODE:
        detect_leading_whitespace(ps_script)
        detect_non_breaking_spaces(ps_script)

    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_script],
        capture_output=True,
        text=True
    )
    if DEBUG_MODE:
        print("RC=", result.returncode)
        print("STDOUT=", repr(result.stdout))
        print("STDERR=", repr(result.stderr))

    txt = result.stdout.strip()
    print("UI Output: ", txt)

    if not txt:
        print("No output detected")
        return None

    return json.loads(txt)


def write_ui_param_in_file(params_ui):
    message = ''

    # Check existence of the RecipeParameters subfolder
    def getEnvRootDir(curr_dir, level=1):
        for i in range(level):
            parent_dir = os.path.dirname(curr_dir)
            if os.path.exists(os.path.join(parent_dir, r"_RecipeParameters")):
                return parent_dir
            curr_dir = parent_dir
        return ''

    env_root_dir = getEnvRootDir(os.path.abspath(__file__), level=3)
    if env_root_dir:
        print('Env Root Dir detected: ', env_root_dir)
        ui_param_dir = os.path.join(env_root_dir, "_RecipeParameters")
        
        # Looking for an existing parameters file
        ui_param_file = os.path.basename(__file__).replace('.py', '_ui-param.json')
        ui_param_fp = os.path.join(ui_param_dir, ui_param_file)

        if os.path.exists(ui_param_fp):
            # Read the last line and compare to existing values
            with open(ui_param_fp, "r") as f:
                try:
                    last_line = next(reversed(list(f))).rstrip("\n")
                except BaseException as e:
                    last_line = ""
                    print(f"Error: could not read last line of parameter file: {ui_param_fp}\n{e}")

            if last_line:
                if params_ui == last_line:
                    message = f"New parameters equal previous parameters in: {ui_param_fp}.\nNothing changed!"
                else:
                    with open(ui_param_fp, "a") as f:
                        f.write("\n" + params_ui)
                    message = f"New parameters differ from previous parameters and were added to: {ui_param_fp}"
        else:
            with open(ui_param_fp, 'w') as f:
                f.write(params_ui)
                message = f"New parameters written to: {ui_param_fp}"
    else:
        message = (f"Env directory was not detected from the current script location ({os.path.abspath(__file__)})"
                   f"\n so assumption is that the recipe was not run from PythonEnvForAivia folder."
                   f"\nHence, parameters are not saved in the expected '_RecipeParameters' directory.")
    return message


def detect_leading_whitespace(ps_str):
    for i, line in enumerate(ps_str.splitlines(), 1):
        if line.lstrip() in ('"@', "'@") and line != line.lstrip():
            print(f"Line {i}: here-string terminator preceded by whitespace")
        # print(repr(line))


def detect_non_breaking_spaces(ps_str):
    for i, line in enumerate(ps_str.splitlines(), 1):
        if '\u00A0' in line:
            print(f"Line {i}: contains NBSP")
        # print(repr(line))


if __name__ == '__main__':
    params = {'inputImagePath': r'D:\PythonCode\_tests\XYZ_50x50x51_1ch_8bit_binarymask_synthetic_A9.0.aivia.tif',
              'resultPath': r'D:\PythonCode\_tests\dummy-output.tif',
              'fileOutputPath_2': r'D:\PythonCode\_tests\output.tif',
              'TCount': 1,
              'ZCount': 192,
              'Calibration': 'XYZT: 0.46 micrometers, 0.46 micrometers, 0.46 micrometers, 1 Default',
              'CallingExecutable': r"C:\Program Files\Leica Microsystems\Aivia 16.0.0\Aivia.dll"}
    run(params)

# CHANGELOG
# v1_00: - Including isotropic scaling and proper export to Aivia
# v1_10: - Adding a GUI to choose rotation axis + virtual environment activation
# v1_11: - New virtual env code for auto-activation
# v1.12: - Added an extra key in params for Unit test output and changed the way to catch Aivia.exe path
# v1.13: - CallingExecutable key now provides the path of a dll file. Adjusting to exe path
# v1.20: - Adding default folder for potential batch functionality (input still can't be put in a workflow)
# v2.00: - New UI to work with Aivia 16, Env removed
