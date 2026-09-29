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


import pandas as pd
import re
import numpy as np
import subprocess, json
import wx
import math

def init_ui():
    app = wx.App()
    dlg = wx.Dialog(None)
    wx.CallLater(1, dlg.EndModal, wx.ID_OK)
    dlg.ShowModal()
    dlg.Destroy()

init_ui()
import matplotlib
matplotlib.use("WXAgg")

import matplotlib.pyplot as plt
import seaborn as sns

# File to quickly run the script on all Excel files in same folder
DEFAULT_FILE = ''

"""
Extracts values from result tables from Aivia and displays heatmaps or array of plots.
Will try to reconstruct the structure of a multiwell plate of well names are detected.

TODO: v1.20: - Ability to select any table having well names as header

WARNING: This currently works only under the following conditions:
    - no timepoints

Requirements
------------
pandas
openpyxl
xlrd
wxPython

Parameters
----------
aivia_excel_file : string
    Path to the Excel file exported from Aivia.

Returns
-------
DataFrame  
    Data from the spreadsheet converted to a Pandas DataFrame and then plot.

"""

color_palettes = [
    'Blues', 'Blues_r', 'BrBG', 'BrBG_r', 'BuGn', 'BuGn_r', 'BuPu', 'BuPu_r',
    'CMRmap', 'CMRmap_r', 'GnBu', 'GnBu_r', 'Greens', 'Greens_r', 'Greys',
    'Greys_r', 'OrRd', 'OrRd_r', 'Oranges', 'Oranges_r', 'PRGn', 'PRGn_r',
    'PiYG', 'PiYG_r', 'PuBu', 'PuBuGn', 'PuBuGn_r', 'PuBu_r', 'PuOr', 'PuOr_r',
    'PuRd', 'PuRd_r', 'Purples', 'Purples_r', 'RdBu', 'RdBu_r', 'RdGy',
    'RdGy_r', 'RdPu', 'RdPu_r', 'RdYlBu', 'RdYlBu_r', 'RdYlGn', 'RdYlGn_r',
    'Reds', 'Reds_r', 'Spectral', 'Spectral_r', 'Wistia', 'Wistia_r',
    'YlGn', 'YlGnBu', 'YlGnBu_r', 'YlGn_r', 'YlOrBr', 'YlOrBr_r', 'YlOrRd',
    'YlOrRd_r', 'afmhot', 'afmhot_r', 'autumn', 'autumn_r', 'binary',
    'binary_r', 'bone', 'bone_r', 'brg', 'brg_r', 'bwr', 'bwr_r',
    'cividis', 'cividis_r', 'cool', 'cool_r', 'coolwarm', 'coolwarm_r',
    'copper', 'copper_r', 'crest', 'crest_r', 'cubehelix', 'cubehelix_r',
    'flare', 'flare_r', 'gist_earth', 'gist_earth_r',
    'gist_gray', 'gist_gray_r', 'gist_heat', 'gist_heat_r', 'gist_ncar',
    'gist_ncar_r', 'gist_rainbow', 'gist_rainbow_r', 'gist_stern',
    'gist_stern_r', 'gist_yarg', 'gist_yarg_r', 'gnuplot', 'gnuplot2',
    'gnuplot2_r', 'gnuplot_r', 'gray', 'gray_r', 'hot', 'hot_r',
    'hsv', 'hsv_r', 'icefire', 'icefire_r', 'inferno', 'inferno_r',
    'jet', 'jet_r', 'magma', 'magma_r', 'mako', 'mako_r',
    'nipy_spectral', 'nipy_spectral_r', 'ocean', 'ocean_r', 'pink',
    'pink_r', 'plasma', 'plasma_r', 'rainbow',
    'rainbow_r', 'rocket', 'rocket_r', 'seismic', 'seismic_r',
    'spring', 'spring_r', 'summer', 'summer_r', 'terrain', 'terrain_r',
    'turbo', 'turbo_r', 'twilight', 'twilight_r', 'twilight_shifted',
    'twilight_shifted_r', 'viridis', 'viridis_r', 'vlag', 'vlag_r',
    'winter', 'winter_r'
]
COLOR_MAP_DEFAULT = sns.diverging_palette(150, 275, s=80, l=55, n=9)        # Max = 359
COLOR_MAPS = ['default'] + color_palettes
debug_mode = False

# [INPUT Name:inputPath Type:string DisplayName:'Any channel']
# [OUTPUT Name:resultPath Type:string DisplayName:'Dummy to delete']
def run(params):
    if params.get('debugMode', False):
        debug_mode = True

    # Choose files (or rely on an hard coded default folder)
    input_file = DEFAULT_FILE
    if input_file == "":
        input_file = pick_file()

    # Read file
    df_raw = pd.read_excel(input_file, sheet_name=None)
    all_sheets = list(df_raw.keys())

    # Select sheet tab GUI ---------------------------
    if len(all_sheets) > 1:
        # Each entry is expected to have: label, widget_type, choices (if needed)
        # A file browser is automatically bound to a "BrowseButton" in the same grid no. Same with "CallButton" and "Cancel"
        # Slider choices = min, max, step, init-value (all should be integer) | &#10; for line break in labels
        ui_width, ui_height = 540, 280
        info_dict = {'selected_tab': {"widget_type": "ComboBox", "label": f"{len(all_sheets)} sheets were detected in your Excel table."
                                                                          f"&#10;&#10;Select a sheet tab:",
                                  'choices': all_sheets},
                     'CallButton': {"widget_type": "OKButton", "label": "Select"}
                     }

        params_ui = ask_parameters_wpf(info_dict, ui_width, ui_height)

        selected_tab = params_ui['selected_tab']
    else:
        selected_tab = all_sheets[0]
    # -------------------------------------------------

    # Collect data per column (well or image)
    df_data = df_raw[selected_tab]
    col_list = list(df_data.columns)

    # If only 1 column, check if want to proceed
    if len(col_list) < 2:         # TODO: CHANGE condition
        msg = 'The selected spreadsheet tab contains only 1 column of data:\nDo you want to proceed?'
        ans = Mbox('Continue?', msg, 1)
        if ans == "Cancel":
            sys.exit('Script aborted by user')

    # Check if first column contains values or is only text and should be discarded
    info_in_col1 = False
    first_col = df_data.iloc[:, 0]
    if all(is_text(value) for value in first_col.dropna()):
        info_in_col1 = True
        del col_list[0]

    # Check if first column contains only object names
    is_first_col_objects = False
    if all(is_object_name(value) for value in first_col.dropna()):
        is_first_col_objects = True

    # Check if third column exists (scenario 2) and is not a timepoint
    is_multi_meas_tab = False
    if is_first_col_objects and df_data.shape[1] > 2:
        if not is_object_name(df_data.columns[2]):      # i.e. not a timepoint
            is_multi_meas_tab = True

    sub_df = []         # to store sub tables as a list of df
    sub_param = []      # to store sub table parameter (area, intensity, etc.)
    temp_data = []      # to store sub table data as list before conversion as DataFrame
    r = 0

    # Scenario 1: standard measurement tab from Aivia = first column is object names
    #             OR standard summary tab from Aivia = first column is measurement names
    if info_in_col1 and not is_multi_meas_tab:
        # Check if all rows in column 1 are objects with numbers (i.e. ending with a number) or not
        # If so, then rows are individual objects, whereas opposite case means 1 row = 1 summary value
        if is_first_col_objects:
            # Rows are individual objects
            sub_df.append(df_data[col_list])
            sub_param.append(df_data.columns[0])        # Name of measurement expected in first cell of table

        else:   # Rows are individual summary values, such as in the summary tab
            for r, r_data in df_data.iterrows():
                if not pd.isna(first_col[r]):
                    test = r_data[1:]
                    df_to_transfer = pd.DataFrame([test], columns=col_list)
                    sub_df.append(df_to_transfer)
                    sub_param.append(first_col[r])

    # Scenario 2: object set tab from a combined sheet, with 1 column = 1 measurement, first column is object names
    if is_multi_meas_tab:
        sub_df.append(df_data[col_list])
        sub_param.append('All measurements')

    # Scenario 3: each column contains (without header) measurement name and subsequent measurements, a space and
    #             another set of measurements with the name at top of the block
    max_r = min(df_data.shape[0], 10)
    if any(is_text(value) for value in df_data.iloc[0:max_r, -1]):
        while r < df_data.shape[0]:
            row_data = df_data.iloc[r]
            is_empty = (row_data.eq('') | row_data.isna()).all()
            if not is_empty:
                # Search for text that doesn't correspond to a number or %
                has_text = any(is_text(value) for value in row_data)

                if has_text and r < df_data.shape[0] - 1:       # Header of sub table and init with next row
                    # Get measurement name
                    sub_param.append(row_data.iloc[0])

                    # Init/reset data list
                    temp_data = []

                    # Scan for all rows corresponding to the same header
                    add_next_row = True
                    while r < df_data.shape[0] - 1 and add_next_row:
                        r += 1
                        row_data = df_data.iloc[r]
                        is_empty = (row_data.eq('') | row_data.isna()).all()
                        has_text = any(is_text(value) for value in row_data)

                        if has_text or is_empty:
                            # Transfer collected sub table to main collection
                            sub_df.append(pd.DataFrame(temp_data, index=list(range(1, len(temp_data) + 1)),
                                                       columns=col_list))
                            add_next_row = False
                        else:
                            temp_data.append(row_data)

                else:
                    r += 1
            else:
                r += 1

    # GUI: User picks the measurement and the statistics type to use ----------------------------------------------
    # Collect describing values
    stats = list((pd.DataFrame([0, 1]).describe()).index)
    stats[0] = 'total'
    stats = [st.replace('%', '% quantile') for st in stats]
    describe_len = len(stats)

    # Adding some other chart types
    other_plots = ['Histogram', 'Box Plot', 'Violin Plot']      # 'Cumulative Histogram' (not working)
    stats = stats + other_plots

    # Each entry is expected to have: label, widget_type, choices (if needed)
    # A file browser is automatically bound to a "BrowseButton" in the same grid no. Same with "CallButton" and "Cancel"
    # Slider choices = min, max, step, init-value (all should be integer) | &#10; for line break in labels
    ui_width, ui_height = 600, 500
    info_dict = {'measurement': {"widget_type": "ComboBox", "label": "Select a measurement:",
                                 'choices': sub_param},
                 'stat': {"widget_type": "RadioButtons", "label": "Calculated statistics:",
                          'choices': stats},
                 'cmap': {"widget_type": "ComboBox", "label": "[Heatmap] Choose a color palette (default is green-white-purple)",
                          'choices': COLOR_MAPS},
                 'seeval': {"widget_type": "CheckBox", "label": "[Heatmap] Display values on heatmap",
                            'choices': "True"},
                 'sameyaxis': {"widget_type": "CheckBox", "label": "[Charts] Share the same Y axis?",
                               'choices': "True"},
                 'show_color_palettes': {"widget_type": "CheckBox", "label": "[Heatmap] On top of the heatmap, show all available colors?",
                                         'choices': "False"},
                 'CallButton': {"label": "Run", "widget_type": "OKButton"}
                 }
    params_ui = ask_parameters_wpf(info_dict, ui_width, ui_height, 10)

    sub_tab_index = sub_param.index(params_ui['measurement'])
    stat_index = stats.index(params_ui['stat'])
    color_map = params_ui['cmap']
    if color_map == "default":
        color_map = COLOR_MAP_DEFAULT
    see_values = params_ui['seeval']
    same_y_axis = params_ui['sameyaxis']
    show_color_palettes = params_ui['show_color_palettes']

    # Type of chart
    if stat_index < describe_len:
        plt_type = 'heatmap'
    else:
        plt_type = stats[stat_index]
    # --------------------------------------------------------------------------------------------------------

    # Calculate statistics to combine all fov to single values per well
    selected_sub_df = sub_df[sub_tab_index]
    min_n_rows = selected_sub_df.count().min()
    max_n_rows = selected_sub_df.count().max()

    # Check if n == 1 that std dev is not selected
    if max_n_rows == 1:
        if stats[stat_index] == 'std':
            msg = 'You selected Standard Deviation for a measurement which contains only 1 value per column.\n' \
                  'This cannot be calculated, please launch the script again.'
            Mbox('Error', msg, 0)
            sys.exit(msg)

    # Handle specific formats (%, etc.)
    is_percentage = False
    if '%' in str(selected_sub_df.iloc[0, 0]):
        is_percentage = True
        selected_sub_df.replace(to_replace='%', value='', inplace=True, regex=True)
        selected_sub_df = selected_sub_df.astype(float)
        selected_sub_df /= 100
    stats_df = selected_sub_df.describe()

    # Replace "count" by "total"
    stats_df.rename(index={stats_df.index[0]: 'total'}, inplace=True)
    stats_df.loc['total'] = stats_df.loc['total'] * stats_df.loc['mean']

    # Detect max layout (rows, columns) in a multiwell plate format
    if is_well_name(col_list[0]):
        rows = [ord(s[0]) - 64 for s in col_list]
        r_min = min(rows)
        r_max = max(rows)
        cols = [int(s[1:]) for s in col_list]
        c_min = min(cols)
        c_max = max(cols)
    else:       # if no multiwell header
        r_min = 1
        r_max = 1
        c_min = 1
        c_max = len(col_list[:])

    no_rows = r_max - r_min + 1
    no_cols = c_max - c_min + 1

    # HEATMAP **********************************************************************
    if plt_type == 'heatmap':
        # Init multiwell plate format (index = row letters)
        tilt_x_axis = False
        if is_well_name(col_list[0]):
            final_df_indexes = [chr(r + 64) for r in range(r_min, r_max + 1)]
            final_df_columns = [str(c) for c in range(c_min, c_max + 1)]
        else:
            final_df_indexes = range(r_min, r_max + 1)
            final_df_columns = col_list
            if max(list(map(len, col_list))) > 10:
                tilt_x_axis = True

        multiwell_df = pd.DataFrame(np.nan, index=final_df_indexes, columns=final_df_columns)

        # Transfer stats in multiwell df
        selected_stat = stats_df.iloc[stat_index]
        for index, s in selected_stat.items():
            if is_well_name(index):
                current_row = index[0]
                current_col = index[1:]
            else:
                current_row = 1
                current_col = index

            multiwell_df.loc[current_row, current_col] = s

        # Create main figure
        plate_size = (no_rows, no_cols)
        fig = plt.figure(1, figsize=(max(plate_size[1], 4), max(plate_size[0], 2)))

        # Number format for heatmap
        value_format = '.3g'
        if is_percentage:
            value_format = '.1%'

        # Create heatmap
        legend_settings = {'fraction': 0.02}
        if tilt_x_axis:    # put color legend at the bottom
            # legend_settings = {'location': 'bottom', 'orientation': 'horizontal'}
            legend_settings = {'fraction': 0.05}

        ax = sns.heatmap(
            multiwell_df,
            mask=multiwell_df.isnull(),
            square=True,                    # make cells square
            cbar_kws=legend_settings,      # 'fraction': 0.01 = shrink colour bar
            cmap=color_map,                    # use orange/red colour map e.g. 'OrRd'
            linewidth=1,                    # space between cells
            fmt=value_format,                         # value format
            annot=see_values               # to see values in cells
        )

        # Chart formatting
        range_n_rows = str(max_n_rows)
        if min_n_rows != max_n_rows:
            range_n_rows = '[{}-{}]'.format(min_n_rows, max_n_rows)

        prefix = '{} of '.format(stats_df.index[stat_index])
        if max_n_rows == 1:
            prefix = ''
        plt.title('{}{} (n={})'.format(prefix, sub_param[sub_tab_index], range_n_rows),
                  fontsize=14, pad=30)
        ax.xaxis.tick_top()  # x axis on top
        ax.xaxis.set_label_position('top')
        if tilt_x_axis:
            plt.setp(ax.get_xticklabels(), rotation=45, ha="left", rotation_mode="anchor")

        ax.tick_params(length=0)       # Removes ticks
        plt.yticks(rotation=0)
        plt.tight_layout()

    # **************************************************************************************

    if plt_type in other_plots:
        # Create a matrix figure
        if sub_param[0] == 'All measurements':
            fig, axs = plt.subplots(nrows=no_rows, ncols=no_cols, squeeze=False,
                                    figsize=(no_cols * 1.5, max(no_rows, 4)))
        elif not same_y_axis:
            fig, axs = plt.subplots(nrows=no_rows, ncols=no_cols, squeeze=False, sharex='all')
        else:
            fig, axs = plt.subplots(nrows=no_rows, ncols=no_cols, squeeze=False, sharex='all', sharey='all')

        data_index = 0          # Index to retrieve data, which is not matching plot index due to possible empty plots
        top_of_chart = 0.8
        title_rot_value = 0
        xlbl_rot_value = 0

        for ro in range(1, no_rows + 1):
            for co in range(1, no_cols + 1):
                create_plot = True
                ax = axs[ro - 1, co - 1]

                if is_well_name(col_list[0]):
                    # Retrieve well name
                    current_row = ro + r_min - 1
                    current_col = co + c_min - 1
                    current_well = chr(current_row + 64) + str(current_col)

                    if not current_well in col_list:
                        create_plot = False
                        fig.delaxes(ax)
                    else:
                        # Adding labels for row and columns
                        if ro == 1:
                            ax.set_title(current_col, pad=10, fontsize=12)
                        if co == 1:
                            ax.set_ylabel(chr(current_row + 64), rotation=0, labelpad=20, fontsize=12)

                if create_plot:
                    plt_data = selected_sub_df[col_list[data_index]].dropna()

                    if plt_type.startswith('Histogram'):
                        if max(plt_data) > 1000:
                            xlbl_rot_value = 45

                        if plt_type == 'Cumulative Histogram':
                            ax.hist(plt_data, density=True, histtype='step', cumulative=True)
                        else:
                            ax.hist(plt_data)

                    if plt_type == 'Box Plot':
                        ax.boxplot(plt_data)

                    if plt_type == 'Violin Plot':
                        ax.violinplot(plt_data, showmedians=True)

                    if sub_param[0] == 'All measurements':
                        if max(list(map(len, col_list))) > 15:
                            title_rot_value = 45
                            top_of_chart = 0.7

                        ax.set_title(col_list[data_index], fontsize=8, rotation=title_rot_value)
                        ax.tick_params(axis='x', labelsize=8)
                        ax.tick_params(axis='y', labelsize=8)
                        if xlbl_rot_value > 0:
                            plt.setp(ax.get_xticklabels(), rotation=xlbl_rot_value, ha="right", rotation_mode="anchor")

                    data_index += 1

        if sub_param[0] == 'All measurements':
            plt.subplots_adjust(top=top_of_chart, bottom=0.1, wspace=0.5)
        else:
            plt.subplots_adjust(top=top_of_chart, bottom=0.1, wspace=0.4)

        # Set main title
        fig.suptitle(sub_param[0], fontsize=14)

    # Display all color palettes
    if show_color_palettes:
        plt.show(block=False)
        plt.pause(0.5)

        # 1024x800 window
        dpi = 100
        fig = plt.figure(figsize=(1024 / dpi, 800 / dpi), dpi=dpi)

        cols = 4
        rows = math.ceil(len(color_palettes) / cols)

        gradient = np.linspace(0, 1, 256).reshape(1, -1)

        for i, cmap_name in enumerate(color_palettes):
            ax = plt.subplot(rows, cols, i + 1)

            try:
                ax.imshow(
                    gradient,
                    aspect='auto',
                    cmap=matplotlib.colormaps[cmap_name]
                )
            except Exception:
                continue

            ax.set_title(cmap_name, fontsize=6, pad=1)
            ax.set_xticks([])
            ax.set_yticks([])

        plt.subplots_adjust(
            left=0.01,
            right=0.99,
            top=0.99,
            bottom=0.01,
            hspace=0.8,
            wspace=0.2
        )

    plt.show()
    plt.pause(5)


def is_text(val):
    is_it_text = False
    if isinstance(val, str):
        pattern = r'^\d+\.?\d*%?'
        if not re.search(pattern, val):
            is_it_text = True
    return is_it_text


def is_well_name(val):
    is_it_well = False
    if isinstance(val, str):
        pattern = r'^[a-zA-Z][_-]?\d{1,3}$'                 # Accepts '-' and '_' as separators for col and row
        if re.search(pattern, val):
            is_it_well = True
    return is_it_well


def is_object_name(val):
    is_it = False
    if isinstance(val, str):
        pattern = r'.*\d+$'
        if re.search(pattern, val):
            is_it = True
    return is_it


def ask_parameters_wpf(input_dict, ui_wi, ui_he, margin_v: int = 10):
    global debug_mode

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
        if "RadioButtons" in all_widget_types:
            all_rb = [(k, v) for k, v in input_dict.items() if v['widget_type'] == "RadioButtons"]

            if all_rb:
                for k, v in all_rb:
                    radiobuttons_code += f'{ps_radio_choice(k, v['choices'])}'

        return radiobuttons_code

    def create_combobox_code(input_dict):
        combobox_code = ''
        all_widget_types = [v['widget_type'] for k, v in input_dict.items()]
        if "ComboBox" in all_widget_types:
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
    
    {ps_json_return(input_dict)}
}})

$CancelButton.Add_Click({{
    $window.Tag = ""
    $window.Close()
}})

[void]$window.ShowDialog()

$window.Tag
'''
    if debug_mode:
        print(ps_script)

    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_script],
        capture_output=True
    )

    if debug_mode:
        print("RC=", result.returncode)
        print("STDOUT=", repr(result.stdout))
        print("STDERR=", repr(result.stderr))

    txt = result.stdout.decode("cp850").strip()             # To make sure utf-8 characters are correctly output (µ² etc)
    print("UI Output: ", txt)

    if not txt:
        print("No output detected")
        return None

    return json.loads(txt)


def pick_file(default_dir = None):
    cmd = [
        "powershell",
        "-Command",
        "Add-Type -AssemblyName System.Windows.Forms; "
        "$dlg=New-Object System.Windows.Forms.OpenFileDialog; "
        "$dlg.Title='Select a result table (xlsx) to process'; "
        f"$dlg.InitialDirectory='{default_dir}'; "
        "$dlg.Filter='Excel files (*.xlsx)|*.xlsx'; "
        "if($dlg.ShowDialog() -eq 'OK'){Write-Output $dlg.FileName}"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    filepath = result.stdout.strip()
    return filepath


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
    params = {'debugMode': True}
    run(params)

# Changelog:
# v1.00: - Based on main summary output from 'ProcessMultipleExcelTables_FromAivia_v1_40.py'
#        - Started with Matplotlib
# v1.10: - Implementing Seaborn instead, to use the matrix functionalities
# v1.20: - Input table can be any (just need first row to be a header). Renaming script "FromExcelTable"
#          Script offers the ability to select the sheet tab and the measurement
# v1.21: - New virtual env code for auto-activation
# v1.30: - Changed Mbox ctypes, wx and MagicGui to VB for Aivia 16.
#        - Adding the option to display color palettes to choose in the GUI
