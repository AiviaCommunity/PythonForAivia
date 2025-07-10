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


test_file = ''
sep = ' | '     # separator for recipe parameters
max_char_len = 150


# Table with WxPython
class WxTable:
    def __init__(self, t_title, t_width, t_height):
        self.app = wx.App()
        self.frame = wx.Frame(parent=None, title=t_title, size=(t_width, t_height))

        self.table = wx.ListCtrl(self.frame, size=(-1, 100), style=wx.LC_REPORT)
        self.table.InsertColumn(0, 'Info', width=200)
        self.table.InsertColumn(1, 'Value', width=1600)

        self.row = 0        # Table row number

    def add_line(self, title, text):
        self.table.InsertItem(self.row, str(title))
        self.table.SetItem(self.row, 1, str(text))
        self.row += 1

    def add_line_with_sep(self, title):
        self.table.InsertItem(self.row, '----- ' + str(title) + ' -----')
        self.table.SetItem(self.row, 1, '---------------------------------')
        self.row += 1

    def add_block_with_header(self, action_name, block_dict, block_tags):
        self.add_line('Action', action_name)
        for t in block_tags:
            self.add_line(t, block_dict[t])


# [INPUT Name:inputImagePath Type:string DisplayName:'Any channel']
# [OUTPUT Name:resultPath Type:string DisplayName:'Dummy to delete']
def run(params):
    # Choose file
    file_path = test_file if test_file else pick_file('')

    # Read the file
    raw_text = open(file_path, 'r+').read()
    cleaned_text = replace_all(raw_text, {'null': '""', 'true': 'True', 'false': 'False'})

    # Attempt to create dict from file string
    try:
        wkfl_dict = eval(cleaned_text)

    except BaseException as e:
        sys.exit(f'Error trying to convert workflow file as dict:\n{e}')

    # Init wx table
    wx_table = WxTable('Aivia workflow file reader', 1000, 1000)

    # Write first part
    main_tags = ['Name', 'Description', 'CreationUser', 'CreationDateUTC']
    for t in main_tags:
        wx_table.add_line(t, wkfl_dict[t])

    # Process sub-parts in 'Entities' = workflow steps
    steps_dicts = wkfl_dict['Entities']

    # Define tags to retrieve
    calib_tags = ['XYCalibration', 'ZCalibration', 'TCalibration']
    pxclass_tags = ['PixelClassifierName', 'InputChannels', 'BackupPath']   # InputChannels needs to be created
    recipe_tags = ['RecipeName', 'InputChannels', 'RecipeSettings', 'BackupPath']
    #               RecipeName, InputChannels, RecipeSettings need to be created

    for i in range(len(steps_dicts)):
        # Writing a line to separate blocks
        wx_table.add_line_with_sep('Step ' + str(i))

        step_dict = steps_dicts[i]

        # Specific processing if first step is calibration of the image
        if 'DoCalibration' in step_dict.keys():
            wx_table.add_block_with_header('Image calibration', step_dict, calib_tags)

        else:
            # Pixel Classifier step
            if 'PixelClassifierID' in step_dict.keys():
                # Creating / Processing some tags
                step_dict['InputChannels'] = ', '.join([f'Channel {ind}' for ind in step_dict['InputIndices']])

                wx_table.add_block_with_header('Pixel Classifier', step_dict, pxclass_tags)

            elif 'RecipeApplyState' in step_dict.keys():
                # Creating / Processing some tags
                recipe_settings = step_dict['RecipeApplyState']['RecipeSettings']
                step_dict['RecipeName'] = recipe_settings['RecipeName']
                step_dict['InputChannels'] = ', '.join([f'Channel {ind}' for ind in step_dict['InputIndices']])

                # Gathering recipe parameters (ParameterSetStates = parameters group, Parameters = actual parameters)
                step_dict['RecipeSettings'] = ''
                for p_group in recipe_settings['ParameterSetStates']:
                    recipe_params = p_group['Parameters']
                    step_dict['RecipeSettings'] += p_group['ParameterSetName'] + sep
                    step_dict['RecipeSettings'] += sep.join([f"{str(p['Name'])} = {str(p['Value'])}" for p in recipe_params])
                    step_dict['RecipeSettings'] += sep

                wx_table.add_block_with_header('Recipe', step_dict, recipe_tags)

    wx_table.frame.Show()
    wx_table.app.MainLoop()


def replace_all(text, dic):
    for i, j in dic.items():
        text = text.replace(i, j)
    return text


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
# v1.02: - Now using conversion of workflow to a dictionary. Tested on one workflow only. Text replacements are needed.
