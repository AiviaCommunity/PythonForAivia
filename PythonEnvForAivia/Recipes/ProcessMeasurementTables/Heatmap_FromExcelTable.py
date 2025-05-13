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
import wx
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from magicgui import magicgui
import concurrent.futures

# Folder to quickly run the script on all Excel files in it
DEFAULT_FILE = ''

"""
Extracts value from the 'Analysis Summary.xlsx' file created by 'ProcessMultipleExcelTables_FromAivia_v1_40.py'.

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
    Data from the spreadsheet converted to a Pandas DataFrame.

"""

default_color_maps = ['Accent', 'Accent_r', 'Blues', 'Blues_r', 'BrBG', 'BrBG_r', 'BuGn', 'BuGn_r', 'BuPu', 'BuPu_r',
                      'CMRmap', 'CMRmap_r', 'Dark2', 'Dark2_r', 'GnBu', 'GnBu_r', 'Greens', 'Greens_r', 'Greys',
                      'Greys_r', 'OrRd', 'OrRd_r', 'Oranges', 'Oranges_r', 'PRGn', 'PRGn_r', 'Paired', 'Paired_r',
                      'Pastel1', 'Pastel1_r', 'Pastel2', 'Pastel2_r', 'PiYG', 'PiYG_r', 'PuBu', 'PuBuGn', 'PuBuGn_r',
                      'PuBu_r', 'PuOr', 'PuOr_r', 'PuRd', 'PuRd_r', 'Purples', 'Purples_r', 'RdBu', 'RdBu_r', 'RdGy',
                      'RdGy_r', 'RdPu', 'RdPu_r', 'RdYlBu', 'RdYlBu_r', 'RdYlGn', 'RdYlGn_r', 'Reds', 'Reds_r', 'Set1',
                      'Set1_r', 'Set2', 'Set2_r', 'Set3', 'Set3_r', 'Spectral', 'Spectral_r', 'Wistia', 'Wistia_r',
                      'YlGn', 'YlGnBu', 'YlGnBu_r', 'YlGn_r', 'YlOrBr', 'YlOrBr_r', 'YlOrRd', 'YlOrRd_r', 'afmhot',
                      'afmhot_r', 'autumn', 'autumn_r', 'binary', 'binary_r', 'bone', 'bone_r', 'brg', 'brg_r', 'bwr',
                      'bwr_r', 'cividis', 'cividis_r', 'cool', 'cool_r', 'coolwarm', 'coolwarm_r', 'copper', 'copper_r',
                      'crest', 'crest_r', 'cubehelix', 'cubehelix_r', 'flag', 'flag_r', 'flare', 'flare_r',
                      'gist_earth', 'gist_earth_r', 'gist_gray', 'gist_gray_r', 'gist_heat', 'gist_heat_r', 'gist_ncar',
                      'gist_ncar_r', 'gist_rainbow', 'gist_rainbow_r', 'gist_stern', 'gist_stern_r', 'gist_yarg',
                      'gist_yarg_r', 'gnuplot', 'gnuplot2', 'gnuplot2_r', 'gnuplot_r', 'gray', 'gray_r', 'hot', 'hot_r',
                      'hsv', 'hsv_r', 'icefire', 'icefire_r', 'inferno', 'inferno_r', 'jet', 'jet_r', 'magma',
                      'magma_r', 'mako', 'mako_r', 'nipy_spectral', 'nipy_spectral_r', 'ocean', 'ocean_r', 'pink',
                      'pink_r', 'plasma', 'plasma_r', 'prism', 'prism_r', 'rainbow', 'rainbow_r', 'rocket', 'rocket_r',
                      'seismic', 'seismic_r', 'spring', 'spring_r', 'summer', 'summer_r', 'tab10', 'tab10_r', 'tab20',
                      'tab20_r', 'tab20b', 'tab20b_r', 'tab20c', 'tab20c_r', 'terrain', 'terrain_r', 'turbo', 'turbo_r',
                      'twilight', 'twilight_r', 'twilight_shifted', 'twilight_shifted_r', 'viridis', 'viridis_r',
                      'vlag', 'vlag_r', 'winter', 'winter_r']


# [INPUT Name:inputPath Type:string DisplayName:'Any channel']
# [OUTPUT Name:resultPath Type:string DisplayName:'Dummy to delete']
def run(params):
    color_map = sns.diverging_palette(150, 275, s=80, l=55, n=9)        # Max = 359
    # color_map = 'crest'

    # Choose files (or rely on an hard coded default folder)
    input_file = DEFAULT_FILE
    if input_file == "":
        input_file = pick_file()

    # Read file
    df_raw = pd.read_excel(input_file, sheet_name=None)
    all_sheets = list(df_raw.keys())

    # Select sheet tab GUI ---------------------------
    if len(all_sheets) > 1:
        @magicgui(sheet={"label": f"{len(all_sheets)} sheets were detected in your Excel table.\n\nSelect a sheet tab:",
                         "widget_type": "Select", 'choices': all_sheets},
                  call_button="Run")
        def get_tab(sheet=all_sheets[0]):
            pass

        @get_tab.called.connect
        def close_get_tab_callback():
            get_tab.close()

        get_tab.show(run=True)
        selected_tab = get_tab.sheet.value[0]
    else:
        selected_tab = all_sheets[0]
    # -------------------------------------------------

    # Collect data per column (well or image)
    df_data = df_raw[selected_tab]
    col_list = list(df_data.columns)

    # If only 1 column, check if want to proceed
    if len(col_list) < 2:         # TODO: CHANGE condition
        msg = 'The selected spreadsheet tab contains only 1 column of data:\n' \
                    'Do you want to proceed?'
        ans = concurrent.futures.ThreadPoolExecutor().submit(Mbox, 'Continue?', msg, 1)
        if ans == 2:
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

    @magicgui(measurement={"label": "Select a measurement:", "widget_type": "RadioButtons", 'choices': sub_param},
              stat={"label": "Calculated statistics:", "widget_type": "RadioButtons", "orientation": "horizontal",
                    'choices': stats},
              seeval={"label": "[Heatmap] Display values on heatmap"},
              sameyaxis={"label": "[Charts] Share the same Y axis?"},
              call_button="Run")
    def get_choices(measurement=sub_param[0], stat=stats[0], seeval=True, sameyaxis=True):
        pass

    @get_choices.called.connect
    def close_GUI_callback():
        get_choices.close()

    get_choices.show(run=True)
    sub_tab_index = sub_param.index(get_choices.measurement.value)
    stat_index = stats.index(get_choices.stat.value)
    see_values = get_choices.seeval.value
    same_y_axis = get_choices.sameyaxis.value

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
            concurrent.futures.ThreadPoolExecutor().submit(Mbox, 'Error', msg, 0)
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

    plt.show()


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


def pick_file():
    print('Starting wxPython app')
    app = wx.App()

    # Create open file dialog
    openFileDialog = wx.FileDialog(None, "Select a results table (xlsx) to process", ".\\", "",
                                   "Excel files (*.xlsx)|*.xlsx", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

    openFileDialog.ShowModal()
    file_path = openFileDialog.GetPath()
    print("Selected table: ", file_path)
    openFileDialog.Destroy()
    return file_path


def Mbox(title, text, style):
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)


if __name__ == '__main__':
    params = {}
    run(params)

# Changelog:
# v1.00: - Based on main summary output from 'ProcessMultipleExcelTables_FromAivia_v1_40.py'
#        - Started with Matplotlib
# v1.10: - Implementing Seaborn instead, to use the matrix functionalities
# v1.20: - Input table can be any (just need first row to be a header). Renaming script "FromExcelTable"
#          Script offers the ability to select the sheet tab and the measurement
# v1.21: - New virtual env code for auto-activation
