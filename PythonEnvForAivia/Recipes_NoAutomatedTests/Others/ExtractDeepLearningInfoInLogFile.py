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

import wx
import matplotlib.pyplot as plt
from matplotlib.widgets import RadioButtons
import re
import concurrent.futures

"""
Extracts Deep Learning training info (epochs with their relative loss and validation loss values)
Some regex modifications are required if other values are needed, specific to a certain model. 

Requirements
------------
numpy
scikit-image
matplotlib
re
wxpython

Parameters
----------
Input:
Log file from local computer in:
C:\ Users\ {username}\ AppData\ Local\ Leica Microsystems\ Aivia {version}\ 
or from GCP storage

Returns
-------
A chart with two axes, that can be saved with the matplotlib buttons.

"""


# [INPUT Name:inputPath Type:string DisplayName:'Any channel']
# [OUTPUT Name:resultPath Type:string DisplayName:'Dummy to delete']
def run(params):
    print("Running")
    # Setting colors for chart
    col1 = 'royalblue'
    col2 = 'r'          # red

    # GUI to select a log file
    print('Starting wxPython app')
    app = wx.App()
    logfile = pick_file()
    print('-- Selected file: {}--'.format(logfile))

    # Check if log file is from local Aivia or Google Cloud Platform
    is_local = True
    if logfile.endswith('Worklog.log'):
        is_local = False

    file = open(logfile, "r")
    all_lines = file.read()
    list_n_epoch, list_i_epoch = [], []
    if is_local:
        print('-- Extracting local DL data --')
        indiv_data_blocks = extract_DL_runs(all_lines)

        for data in indiv_data_blocks:
            list_n_epoch_tmp, list_i_epoch_tmp = extract_data(data)
            list_n_epoch.append(list_n_epoch_tmp)
            list_i_epoch.append(list_i_epoch_tmp)

    else:
        print('-- Extracting Google Cloud DL data --')
        # (n_epoch, i_epoch) = extract_data_GCP(all_lines)    # TODO: now n_epoch is a list of lists

    # If nothing found, exit
    if list_n_epoch is None:
        concurrent.futures.ThreadPoolExecutor().submit(Mbox, 'No info found',
                                                       'No Deep Learning training info found in this log.', 0)
        sys.exit("No Deep Learning training info found in this log.")

    print('-- Found {} DL training blocks --'.format(len(list_n_epoch)))

    # Init chart
    # fig = plt.figure(figsize=plt.figaspect(0.4))
    # ax1 = fig.add_subplot(111)
    fig, ax1 = plt.subplots(figsize=plt.figaspect(0.4))

    # Create second axis
    ax2 = ax1.twinx()       # instantiate a second axes that shares the same x-axis

    # Create buttons to switch to another DL run
    # sub-plot for radio button with
    # left, bottom, width, height values
    plt.subplots_adjust(right=0.7)
    rax = plt.axes([0.8, 0.1, 0.16, 0.8])
    radio_button = RadioButtons(rax, tuple(['DL training [{}]'.format(x) for x in range(1, len(list_n_epoch) + 1)]),
                                active=len(list_n_epoch) - 1)

    def get_values(run_index):
        run_index -= 1
        n_epoch = list(map(int, list_n_epoch[run_index]))
        i_epoch = list_i_epoch[run_index]

        # extracting values from individual info
        if is_local:
            (all_v1, all_v2) = extract_epoch_val('\n'.join(i_epoch) + '\n')
        else:
            (all_v1, all_v2) = extract_epoch_val_GCP('\n'.join(i_epoch) + '\n')
        all_v1 = list(map(float, all_v1))
        all_v2 = list(map(float, all_v2))

        all_v1_nonsci = [float('{:.4f}'.format(v)) for v in all_v1]  # Remove scientific notation for loss value

        ymax1 = max(all_v1) * 1.1
        ymax2 = max(all_v2) * 1.1

        return n_epoch, all_v1_nonsci, all_v2, ymax1, ymax2

    # Define function for the radio buttons
    def change_DL_run(label):
        run_no = int(str(label).split('no ')[-1])
        n_epoch, all_v1_nonsci, all_v2, ymax1, ymax2 = get_values(run_no)
        print('Selected DL run: {}'.format(run_no))

        # Clear values
        ax1.clear()
        ax2.clear()

        # Create the axes titles
        ax1.set_xlabel('epochs')
        ax1.set_ylabel('loss', color=col1)
        ax1.tick_params(axis='y', labelcolor=col1)

        ax2.set_ylabel('validation_loss', color=col2)
        ax2.tick_params(axis='y', labelcolor=col2)

        # Plot values
        ax1.plot(n_epoch, all_v1_nonsci, color=col1, linewidth=1)
        ax2.plot(n_epoch, all_v2, color=col2, linewidth=1)

        ax1.set_ylim(0, ymax1)
        ax2.set_ylim(0, ymax2)

        plt.draw()      # Update plot

    radio_button.on_clicked(change_DL_run)

    # Process the last DL run
    run_index = len(list_n_epoch)
    change_DL_run(run_index)

    plt.show()


def extract_DL_runs(s):
    # To detect and extract all DL runs in the same log
    start_pattern = re.compile(r"(.+DeepLearning:Epoch\s+1/\d+.+\n)")
    str_split = start_pattern.split(s)
    blocks = [a + b for a, b in zip(str_split[1::2], str_split[2::2])]

    return blocks


def extract_data(s):  # TODO
    # The following regex is for the log from Aivia - from restoration model (see PSNR)
    pattern = re.compile(r""".+DeepLearning:Epoch\s?(?P<epoch>\d*)\/(?P<totalEpochs>\d+)    # First line
                             \n(.*\n){0,20}                                            # followed by several info lines
                             (.*DeepLearning:.*\n){2,258}                              # lines for iterations
                             .+DeepLearning:\s?\d+\/\d+\s\[={20,35}\]\s-\s(?P<status>.+)\n  # Last line with info
                             """, re.VERBOSE)
    match = pattern.findall(s)

    if len(match) < 1:
        return 0, 0

    n_epoc = [ite[0] for ite in match]
    i_epoc = [ite[4] for ite in match]

    return n_epoc, i_epoc


def extract_epoch_val(s):  # TODO
    # The following regex is for the Worklog from Aivia - from restoration model (see PSNR)
    in_pattern = re.compile(r""".*\sloss:\s(?P<vloss>\d+\.?\d*e?-?\d*)
                                \s.*-\sval_loss:\s(?P<vdloss>\d+\.?\d*e?-?\d*)
                                .*
                                \n""", re.VERBOSE)
    in_match = in_pattern.findall(s)

    v_loss = [ite[0] for ite in in_match]
    vd_loss = [ite[1] for ite in in_match]

    return v_loss, vd_loss


def extract_data_GCP(s):
    # The following regex is for the Worklog from the GCP - from restoration model (see PSNR)
    pattern = re.compile(r"""Epoch\s(?P<epoch>\d*)\/(?P<totalEpochs>\d+)     # First line giving epoch no
                            \n\n(.*\n){2,256}                               # All the iterations before the final one
                            \d+\/\d+\s\[={25,35}\]\s-\s                      # Beginning of the final iteration line
                            (?P<status>.+)\n                                # All info for epoch from time to val_psnr
                            """, re.VERBOSE)
    match = pattern.findall(s)

    if len(match) < 1:
        return 0, 0

    n_epoc = [ite[0] for ite in match]
    i_epoc = [ite[3] for ite in match]

    return n_epoc, i_epoc


def extract_epoch_val_GCP(s):
    # The following regex is for the Worklog from the GCP - from restoration model (see PSNR)
    in_pattern = re.compile(r""".*\sloss:\s(?P<vloss>\d+\.?\d*e?-?\d*)
                                \s.*-\sval_loss:\s(?P<vdloss>\d+\.?\d*e?-?\d*)
                                \n""", re.VERBOSE)
    in_match = in_pattern.findall(s)

    v_loss = [ite[0] for ite in in_match]
    vd_loss = [ite[1] for ite in in_match]

    return v_loss, vd_loss


def pick_file():
    # Create open file dialog
    openFileDialog = wx.FileDialog(None, "Select a log file to process", ".\\", "",
                                   "Log files (*.log)|*.log", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

    if openFileDialog.ShowModal() == wx.ID_CANCEL:
        sys.exit()
    fname = openFileDialog.GetPath()
    print("Selected file: ", fname)
    openFileDialog.Destroy()
    return fname


def Mbox(title, text, style):
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)

if __name__ == '__main__':
    params = {}
    run(params)
    # image_location = params['inputImagePath']
    # result_location = params['resultPath']
    # imsave(result_location, output_data)

# Changelog:
# v1.10: - Bug fixed with wxPython app not being run in v1.00
# v1.20: - New virtual env code for auto-activation
# v1.21: - Correcting the mistake of opening the log file as 'r+'. Also fixing some display missing (axis title)
