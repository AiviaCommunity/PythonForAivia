import os
import pandas as pd
import json
import re
import shutil
import subprocess


INPUT_FOLD = r'D:\PythonCode\Python_scripts\Projects\PythonEnvForAivia_A16.0_Py3.12_SANDBOX'
TEST_FOLD = r'Tests'
TEST_IMAGE_FOLD = os.path.join(TEST_FOLD, '_InputImages')
RECIPE_FOLD = r'Recipes'

PREVIOUS_TEST_FOLDER = r'D:\PythonCode\Python_scripts\FromGitHub\Aivia GitHub recipes\Master Branch\PythonEnvForAivia\Tests'

EXCEL_TABLE_P = os.path.join(TEST_FOLD, 'Recipe database.xlsx')
TEST_SCRIPT_TEMPLATE = "test_RECIPE-NAME-PLACEHOLDER.py"

CREATE_IMAGE_LIST_FOR_GT_CREATION = True            # If GT does not exist yet. Will ease the manual load of all images in Aivia

'''
Reads an Excel table to create unit test scripts, config files and folder structure.
Association of test images and image types is available in the 2nd sheet of the Excel table.
'''
# TODO: set input number to be boolean, so that test can be defined both with 0 or 1

INDENT = "    "  # 4 spaces


# [INPUT Name:inputImagePath Type:string DisplayName:'Any channel']
# [OUTPUT Name:resultPath Type:string DisplayName:'Dummy to delete']
def run(params):

    # Setting the working directory, to reproduce the test conditions
    os.chdir(INPUT_FOLD)

    # Read the Excel table
    try:
        df_recipes = pd.read_excel(EXCEL_TABLE_P, sheet_name='Recipe database', na_filter=False)
        df_test_images = pd.read_excel(EXCEL_TABLE_P, sheet_name='Input Image match', na_filter=False)
    except FileNotFoundError:
        print(f'Excel table not found at: {EXCEL_TABLE_P}')

    # Hardcoded column groups
    groups = {
        "info": ["Folder", "Description", "AutoGenerateTest"],
        "dimensions": ["2D", "2D+T", "3D", "3D+T"],
        "input ch": ["Input Ch1 type", "Input Ch2 type", "Input Ch3 type", "Input Ch4 type", "Input Ch5 type", "Input Ch6 type"],
        "input no": ["Input number 1 type", "Input number 2 type", "Input number 3 type", "Input number 4 type"],
        "outputs": ["Output 1 type", "Output 2 type", "Output 3 type"]
    }

    # Collect info in variables
    scripts = {}
    for _, row in df_recipes.iterrows():
        script = row["File"]  # column A name

        scripts[script] = {
            group: {col: row.get(col) for col in cols if row.get(col)}
            for group, cols in groups.items()
        }

    # Read the template file for the test script
    with open(os.path.join(TEST_FOLD, TEST_SCRIPT_TEMPLATE)) as f:
        template = f.read()

    # Loop over expected subfolders from table (data = dict of dict)
    final_mess = '==================== SUMMARY ====================\n'
    for script, data in scripts.items():
        print(f">>> Processing script: {script} <<<")
        script_noext = script[:-3]

        if data['info']['AutoGenerateTest'] == 'no':
            mess = f"Script was skipped (auto test generation excluded in table)"
            print(mess)
            final_mess += f"[SCRIPT] {script}\n  [WARNING] * {mess}\n"
            continue

        # Check presence of script in the Recipes folder
        recipe_p = os.path.join(RECIPE_FOLD, data['info']['Folder'], script)
        if not os.path.exists(recipe_p):
            mess = f"Script was skipped because recipe file does not exist:\n'{recipe_p}'"
            print(mess)
            final_mess += f"[SCRIPT] {script}\n  [WARNING] * {mess}\n"
            continue

        # Sanity check with number of inputs and outputs
        recipe_input_chs, recipe_input_nos, recipe_outputs = collect_inputs_outputs_from_recipe(recipe_p)

        if len(recipe_input_chs) != len(data['input ch']):
            mess = (f"Script was skipped because recipe input channel list {recipe_input_chs} "
                    f"does not match with Excel table {data['input ch']}")
            print(mess)
            final_mess += f"[SCRIPT] {script}\n  [ERROR] *** {mess}\n"
            continue
        if len(recipe_input_nos) != len(data['input no']):
            mess = (f"Script was skipped because recipe input number list {recipe_input_nos} "
                   f"does not match with Excel table {data['input no']}")
            print(mess)
            final_mess += f"[SCRIPT] {script}\n  [ERROR] *** {mess}\n"
            continue

        channel_outputs = [o for _, o in data['outputs'].items() if o in ['channel', 'dummy channel']]

        if len(recipe_outputs) != len(channel_outputs):
            mess = (f"Script was skipped because recipe output list {recipe_outputs} "
                   f"does not match with Excel table {data['outputs']}")
            print(mess)
            final_mess += f"[SCRIPT] {script}\n  [ERROR] *** {mess}\n"
            continue

        # Script category subfolder
        subfold_p = os.path.join(TEST_FOLD, data['info']['Folder'])
        if not os.path.exists(subfold_p):
            os.mkdir(subfold_p)
            open("__init__.py", "a").close()

        # Script subfolder
        script_subfold_p = os.path.join(subfold_p, script_noext)
        if not os.path.exists(script_subfold_p):
            os.mkdir(script_subfold_p)

        #########  TEST SCRIPT BUILDING #################################
        # Init test script code
        test_script = template
        final_mess += f"[SCRIPT] {script}\n"

        # Replace script and subfolder names
        test_script = test_script.replace('RECIPE-FOLDER-PLACEHOLDER', data['info']['Folder'])
        test_script = test_script.replace('RECIPE-NAME-PLACEHOLDER', script_noext)

        # Prepare test guidance text if "NOTE:" is present in the description
        test_guidance_start = data['info']['Description'].find("NOTE:")
        test_guidance_text = data['info']['Description'][test_guidance_start:] if test_guidance_start != -1 else None

        # Prepare parameter handling (pop unnecessary parameters) and assertions to check outputs
        param_processing_list, assertion_list, import_needs = [f"{INDENT}config['unitTest'] = True\n"], [], []
        for ind in range(1, len(data['outputs']) + 1):
            output = data['outputs'].get(f"Output {ind} type")

            # Parameter handling -----------------------
            if output in ['channel', 'image file', 'txt file', 'json file', 'xml file', 'xlsx file', 'csv file']:
                param_processing_list.append(f"{INDENT}ground_truth_path_{ind} = config.pop('groundTruthPath_{ind}')\n")
            elif output in ['number']:
                param_processing_list.append(f"{INDENT}ground_truth_value_{ind} = config.pop('groundTruthValue_{ind}')\n")
            elif output in ['list of numbers']:
                param_processing_list.append(f"{INDENT}ground_truth_value_list_{ind} = config.pop('groundTruthValueList_{ind}')\n")

            # Specific to external output files
            if output in ['image file']:
                param_processing_list.append(f"{INDENT}file_output_value_{ind} = config.get('fileOutputPath_{ind}')\n")

            # Assertions -----------------------------
            if output in ['channel']:
                output_param_name = recipe_outputs[ind - 1]['Name']
                assertion_list.append(f"{INDENT}assert isIdentical(ground_truth_path_{ind}, config.get('{output_param_name}'))\n")
                if not 'isIdentical' in import_needs:
                    import_needs.append('isIdentical')

            elif output in ['image file']:
                assertion_list.append(f"{INDENT}assert isIdentical(ground_truth_path_{ind}, file_output_value_{ind})\n")
                if not 'isIdentical' in import_needs:
                    import_needs.append('isIdentical')

            elif output in ['json file']:
                # TODO: way to get the path of the output file needs to be implemented in the main recipe

                if output == 'json file':
                    if not 'isJsonIdentical' in import_needs:
                        import_needs.append('isJsonIdentical')

            elif output in ['number']:
                assertion_list.append(
                    f"{INDENT}assert (str(result_value) == str(ground_truth_value_{ind})), "
                    f"f'Expected {{ground_truth_value_{ind}}} but result was {{result_value}}'\n")

            elif output in ['list of numbers']:
                assertion_list.append(
                    f"{INDENT}n_values = len(result_value)   # Expected to contain multiple values\n"
                    f"{INDENT}gt_values = ground_truth_value_list_{ind}.split(', ')   # Expected to contain multiple values\n"                    
                    f"{INDENT}for val_ind in range(n_values):\n"
                    f"{INDENT}{INDENT}assert (str(result_value[val_ind]) == str(gt_values[val_ind])), "
                    f"f'Expected {{gt_values[val_ind]}} but result was {{result_value[val_ind]}}'\n")
            else:
                mess = f"Warning: no assertion could be set for this script with output = {output}"
                final_mess += f"  [WARNING] * {mess}\n"

        if test_guidance_text:
            param_processing_list.append(f"{INDENT}test_guidance = config.pop('testGuidance')\n"
                                         f"{INDENT}ctypes.windll.user32.MessageBoxW(0, test_guidance, 'Test guidance', 0)\n")

        # Write imports depending on needed comparisons (image file, value, json, etc.)
        import_list = [f"from Tests.utils.comparison import {fct}\n" for fct in import_needs]
        test_script = test_script.replace('IMPORT-PLACEHOLDER', ''.join(import_list))

        # Write parameter handling and assertions
        test_script = test_script.replace('PARAM-PLACEHOLDER', ''.join(param_processing_list))
        test_script = test_script.replace('ASSERTION-PLACEHOLDER', ''.join(assertion_list))

        # Put description
        test_script = test_script.replace('DESCRIPTION-PLACEHOLDER', "'''\n" + data['info']['Description'] + "'''\n")

        #########  /TEST SCRIPT BUILDING #################################

        # Saving script file
        script_p = os.path.join(subfold_p, f"test_{script}")
        with open(script_p, "w") as s_file:
            s_file.write(test_script)
        final_mess += f"  [INFO] Test script saved:\n    {script_p}\n"

        #########  CONFIG FILE BUILDING #################################
        json_config_data, image_list_dict = [], []

        # Loop over the different accepted image dimensions
        for dim in data['dimensions']:
            for bitdepth in ['8bit', '16bit']:
                dict_entry = {}
                skip_condition = False
                input_image_list_1_condition = []       # list to be used if all input images are available
                gt_image_list_1_condition = []

                # Add channel inputs
                for i, input in enumerate(recipe_input_chs):
                    # Find proper test images corresponding to dimensions, bitdepth and input type
                    input_var_name = input['Name']
                    input_type = data['input ch'][f'Input Ch{i + 1} type']
                    img_selection = df_test_images.query('Dimensions == @dim and Depth == @bitdepth and Type == @input_type')
                    img_selection = img_selection[img_selection["Filename match in _InputImages"] != ""]

                    # If no test image for this condition, skip
                    if img_selection.empty:
                        skip_condition = True
                    else:
                        test_image_name = img_selection['Filename match in _InputImages'].iloc[0]      # first of any list
                        dict_entry[input_var_name] = os.path.join(TEST_IMAGE_FOLD, test_image_name)
                        input_image_list_1_condition.append(test_image_name)

                if not skip_condition:
                    # Add default input parameter values if any
                    if recipe_input_nos:
                        for i, input_no in enumerate(recipe_input_nos):
                            if 'Default' in input_no.keys():
                                dict_entry[input_no['Name']] = input_no['Default']
                            else:
                                # GUI ---------------------------------------------------------------------
                                # Each entry is expected to have: label, widget_type, choices (if needed)
                                # A file browser is automatically bound to a "BrowseButton" in the same grid no. Same with "CallButton" and "Cancel"
                                # Slider choices = min, max, step, init-value (all should be integer) | &#10; for line break in labels
                                ui_width, ui_height = 540, 300
                                info_dict = {'val': {"widget_type": "RadioButtons",
                                                     "label": f'Default value for the script [{script_noext}] was not '
                                                              f'specified for the input [{input_no['Name']}]. Add it in the code.'
                                                              f'\nIn the meantime, it can be provided here: ',
                                                     "choices": "1.0"},
                                             'CallButton': {"widget_type": "OKButton", "label": "Proceed"}
                                             }

                                params_ui = ask_parameters_wpf(info_dict, ui_width, ui_height)

                                dict_entry[input_no['Name']] = params_ui['val']

                                final_mess += (f"  [WARNING] * Default value for ** {input_no['Name']} ** "
                                               f"was not specified in the recipe inputs.\n"
                                               f"    It was manually specified as ** {dict_entry[input_no['Name']]} **")

                    # Add output
                    for i in range(len(data['outputs'])):
                        output = data['outputs'][f'Output {i + 1} type']
                        if output in ['channel']:
                            ch_suffix = f"_{recipe_outputs[i]['DisplayName']}" # if len(channel_outputs) > 1 else ""
                            dict_entry[recipe_outputs[i]['Name']] = os.path.join(script_subfold_p,
                                                                                 f"OUT_{test_image_name[:-4]}{ch_suffix}.tif")

                            # Add GT path
                            dict_entry[f'groundTruthPath_{i + 1}'] = os.path.join(script_subfold_p,
                                                                                  f"GT_{test_image_name[:-4]}{ch_suffix}.tif")
                            gt_image_list_1_condition.append(f"GT_{test_image_name[:-4]}{ch_suffix}.tif")

                        elif output in ['dummy channel']:
                            dict_entry[recipe_outputs[i]['Name']] = ""      # to avoid error with the recipe

                        elif output in ['image file']:
                            ch_suffix = "_processed"
                            dict_entry[f"fileOutputPath_{i + 1}"] = os.path.join(script_subfold_p,
                                                                                 f"OUT_{test_image_name[:-4]}{ch_suffix}.tif")

                            # Add GT path
                            dict_entry[f'groundTruthPath_{i + 1}'] = os.path.join(script_subfold_p,
                                                                                  f"GT_{test_image_name[:-4]}{ch_suffix}.tif")
                            gt_image_list_1_condition.append(f"GT_{test_image_name[:-4]}{ch_suffix}.tif")

                            # Add extra entry relative to reopening image files in Aivia
                            dict_entry['CallingExecutable'] = 'None'

                        # Add output not in the Aivia UI
                        elif output in ['number']:
                            # Trying to find a GT value in the Excel table
                            if not img_selection.empty:
                                val_candidate = str(img_selection.iloc[0].get(script_noext))

                                if val_candidate:
                                    dict_entry[f'groundTruthValue_{i + 1}'] = val_candidate
                                else:
                                    skip_condition = True

                        # Add output not in the Aivia UI
                        elif output in ['list of numbers']:
                            # Trying to find GT values in the Excel table (should be COMMA separated!)
                            if not img_selection.empty:
                                val_candidate = str(img_selection.iloc[0].get(script_noext))

                                if val_candidate:
                                    dict_entry[f'groundTruthValueList_{i + 1}'] = val_candidate
                                else:
                                    skip_condition = True

                if not skip_condition:
                    # Add guidance test if any
                    if test_guidance_text:
                        dict_entry['testGuidance'] = test_guidance_text

                    # Add Z and T dimensions
                    dict_entry['ZCount'] = img_selection['ZCount'].iloc[0]
                    dict_entry['TCount'] = img_selection['TCount'].iloc[0]

                    # Add 'Calibration' value
                    # calibration_str = "XYZT: XY-VAL XYZ-UNIT, XY-VAL XYZ-UNIT, Z-VAL XYZ-UNIT, T-VAL T-UNIT"
                    pxsize_xy = img_selection['PxSize XY'].iloc[0]
                    pxsize_xy = str(pxsize_xy) if pxsize_xy else "1"
                    pxsize_z = img_selection['PxSize Z'].iloc[0]
                    pxsize_z = str(pxsize_z) if pxsize_z else "1"
                    xyzunit = img_selection['XYZ unit'].iloc[0]
                    xyzunit = str(xyzunit) if xyzunit else "Default"
                    tstep = img_selection['TimeStep'].iloc[0]
                    tstep = str(tstep) if tstep else "1"
                    tunit = img_selection['Time unit'].iloc[0]
                    tunit = str(tunit) if tunit else "Default"
                    dict_entry['Calibration'] = f"XYZT: {pxsize_xy} {xyzunit}, {pxsize_xy} {xyzunit}, {pxsize_z} {xyzunit}, {tstep} {tunit}"

                    # Add dict to list
                    json_config_data.append(dict_entry)

                    # Pair input and gt output image names
                    image_list_dict.append({"in": input_image_list_1_condition, "gt": gt_image_list_1_condition})

        # Write JSON Config file
        json_file_p = os.path.join(script_subfold_p, f"Config_{script_noext}.json")
        with open(json_file_p, "w") as json_file:
            json.dump(json_config_data, json_file, indent=4)
        final_mess += f"  [INFO] Json config saved:\n    {json_file_p}\n"

        #########  /CONFIG FILE BUILDING #################################
        skip_gt_preparation = False

        # Check GT files are not already in the destination folder
        gt_image_list = [i for il in image_list_dict for i in il["gt"]]
        if all([os.path.exists(os.path.join(script_subfold_p, im)) for im in gt_image_list]):
            skip_gt_preparation = True
            mess = f"    [INFO] GT files already exists in destination test folder.\n"
            final_mess += mess

        # Create folder to put input images to create GT (ease the manual load of all images in Aivia)
        if CREATE_IMAGE_LIST_FOR_GT_CREATION and not skip_gt_preparation:
            image_for_gt_fold_p = os.path.join(script_subfold_p, f"ImagesForGTcreation_ToDelete")

            # Copy input files
            # Search if GT image already exists in a previous test folder
            previous_script_subfold_p = os.path.join(PREVIOUS_TEST_FOLDER, data['info']['Folder'], script_noext)
            final_mess += "  [FILE] Copied GT files:\n"
            for img_1cond in image_list_dict:
                mess = ''

                # If gt images exists, copy them
                if all([os.path.exists(os.path.join(previous_script_subfold_p, i)) for i in img_1cond["gt"]]):
                    for gt in img_1cond["gt"]:
                        shutil.copy(os.path.join(previous_script_subfold_p, gt),
                                    os.path.join(script_subfold_p, gt))
                        mess += f"    - {gt} was copied from previous test folder.\n"

                else:   # copy the input images instead
                    if not os.path.exists(image_for_gt_fold_p):
                        os.mkdir(image_for_gt_fold_p)
                    for in_img in img_1cond["in"]:
                        shutil.copy(os.path.join(TEST_IMAGE_FOLD, in_img),
                                    os.path.join(image_for_gt_fold_p, in_img))
                        mess += f"    - {in_img} was copied to the GT creation preparation folder.\n"
                final_mess += mess

        final_mess += "==\n"

    # Write log in a text file in the test folder
    with open(os.path.join(TEST_FOLD, 'Log_automatic-test-script-creation.log'), "w") as log_file:
        log_file.write(final_mess)
    print(final_mess)


# outputs tuple of list of dicts
def collect_inputs_outputs_from_recipe(file_path: str) -> tuple:
    with open(file_path, "r") as f:
        lines = f.readlines()

    # Definitions
    input_pattern = re.compile(r"^#\s*\[INPUT\s+(.*?)\]$")
    output_pattern = re.compile(r"^#\s*\[OUTPUT\s+(.*?)\]$")

    def parse_block(block):
        fields = {}
        parts = re.findall(r"(\w+):('[^']*'|[^ ]+)", block)
        for k, v in parts:
            fields[k] = v.strip("'")
        return fields

    inputs, outputs = [], []

    # Find def run()
    for i, line in enumerate(lines):
        if line.strip().startswith("def run"):
            idx = i
            break
    else:
        return [], []  # no run found

    # Walk backwards
    i = idx - 1
    while i >= 0:
        line = lines[i].strip()

        # Stop if blank line → breaks attachment rule
        if line == "":
            break

        # Parse INPUT / OUTPUT
        m_in = input_pattern.search(line)
        m_out = output_pattern.search(line)

        if m_in:
            inputs.append(parse_block(m_in.group(1)))
        elif m_out:
            outputs.append(parse_block(m_out.group(1)))
        else:
            # Non-matching line breaks the block (strict)
            break

        i -= 1

    # reverse order (as requested)
    # inputs.reverse()
    # outputs.reverse()

    # Split input channels and numbers
    input_chs, input_nos = [], []
    for inp in inputs:
        if inp.get("Type") == "string":
            input_chs.append(inp)
        else:
            input_nos.append(inp)

    return input_chs, input_nos, outputs


def ask_parameters_wpf(input_dict, ui_wi, ui_he, margin_v: int = 10):

    # Functions to create XAML code
    def create_radiobutton_xaml(dict_key, value_list, margin_val):
        code = ''
        name_list = [f"{dict_key}RB{n}" for n in range(1, len(value_list) + 1)]

        is_checked = 'IsChecked="True" '
        for i in range(len(name_list)):
            code += f'<RadioButton Name="{name_list[i]}" {is_checked}Content="{value_list[i]}" Margin="0,0,10,{margin_val}"/>'
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
                    <StackPanel Margin="0,5,0,0">{create_radiobutton_xaml(input_key, input_value['choices'], margin_value)}</StackPanel>
                </GroupBox>
                '''
        elif input_value["widget_type"] == "RadioButtonsH":
            xaml_block = rf'''
                <GroupBox Grid.Row="{grid_number}" Header="{input_value['label']}" Margin="0,0,0,{margin_value}">
                    <StackPanel Margin="0,5,0,0" Orientation="Horizontal">{create_radiobutton_xaml(input_key, input_value['choices'], margin_value)}</StackPanel>
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
                content += f"    {k} = ${k}.Items[${k}.SelectedIndex].Content\n"
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
        if "RadioButtons" in all_widget_types or "RadioButtonsH" in all_widget_types:
            all_rb = [(k, v) for k, v in input_dict.items() if v['widget_type'] in ["RadioButtons", "RadioButtonsH"]]

            if all_rb:
                for k, v in all_rb:
                    radiobuttons_code += f'{ps_radio_choice(k, v['choices'])}'

        return radiobuttons_code

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
    {ps_json_return(input_dict)}
}})

$CancelButton.Add_Click({{
    $window.Tag = ""
    $window.Close()
}})

[void]$window.ShowDialog()

$window.Tag
'''
    print(ps_script)
    # print("Leading spaces: ", detect_leading_whitespace(ps_script))
    # print("Non-Breaking spaces: ", detect_non_breaking_spaces(ps_script))

    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_script],
        capture_output=True
    )

    # print("RC=", result.returncode)
    # print("STDOUT=", repr(result.stdout))
    # print("STDERR=", repr(result.stderr))

    txt = result.stdout.decode("cp850").strip()             # To make sure utf-8 characters are correctly output (µ² etc)
    print("UI Output: ", txt)

    if not txt:
        print("No output detected")
        return None

    return json.loads(txt)


if __name__ == '__main__':
    params = {}
    run(params)

# CHANGELOG
#   v1_00: - First version
#   v1_10: - Magicgui replaced by VB for Aivia 16 env
#          - Bug corrected with check of GT images in the Master Branch
