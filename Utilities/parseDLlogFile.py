import ctypes
import sys
from os import path, listdir, environ
import win32con
import win32gui
# from skimage.io import imread, imsave
# import numpy as np
import matplotlib.pyplot as plt
import re

"""
Extracts Deep Learning training info (epochs with their relative val_loss + val_acc)
Some regex modifications are required if other values are needed, specific to a certain model. 

Requirements
------------
numpy (comes with Aivia installer)
scikit-image (comes with Aivia installer)
win32con (comes with Aivia installer?)
win32gui (comes with Aivia installer?)
matplotlib (comes with Aivia installer)
re (comes with Aivia installer?)

Parameters
----------
Input:
Log file from local computer in:
C:\ Users\ {username}\ AppData\ Local\ DRVision Technologies LLC\ Aivia {version}\ 
or from GCP storage

Returns
-------
A chart with two axes, that can be saved with the matplotlib buttons.

"""


def run():
    print("Running")
    # Setting colors for chart
    col1 = 'royalblue'
    col2 = 'r'

    logfile = pick_file()

    # Check if log file is from local Aivia or Google Cloud Platform
    is_local = True
    if logfile.endswith('Worklog.log'):
        is_local = False

    file = open(logfile, "r+")
    all_lines = file.read()
    if is_local:
        (n_epoch, i_epoch) = extract_data(all_lines)
    else:
        (n_epoch, i_epoch) = extract_data_GCP(all_lines)

    # If nothing found, exit
    if n_epoch == 0:
        Mbox('No info found', 'No Deep Learning training info found in this log.', 0)
        sys.exit("No Deep Learning training info found in this log.")

    n_epoch = list(map(int, n_epoch))

    # extracting values from individual info
    if is_local:
        (all_v1, all_v2) = extract_epoch_val('\n'.join(i_epoch)+'\n')
    else:
        (all_v1, all_v2) = extract_epoch_val_GCP('\n'.join(i_epoch) + '\n')
    all_v1 = list(map(float, all_v1))
    all_v2 = list(map(float, all_v2))

    ymax1 = max(all_v1) * 1.1
    ymax2 = max(all_v2) * 1.1

    fig = plt.figure(figsize=plt.figaspect(0.5))
    ax1 = fig.add_subplot(111)
    ax1.set_xlabel('epochs')
    ax1.set_ylabel('val_loss', color=col1)
    ax1.tick_params(axis='y', labelcolor=col1)
    ax1.set_ylim(0, ymax1)
    # ax1.yaxis.set_major_locator(ticker.MultipleLocator(0.1))

    # Create second axis
    ax2 = ax1.twinx()
    ax2.set_ylabel('val_acc', color=col2)
    ax2.tick_params(axis='y', labelcolor=col2)
    ax2.set_ylim(0, ymax2)
    # ax2.yaxis.set_major_locator(ticker.MultipleLocator(1))

    # Plot values
    ax1.plot(n_epoch, all_v1, color=col1, linewidth=1)
    ax2.plot(n_epoch, all_v2, color=col2, linewidth=1)

    plt.show()


def extract_data(s):        # TODO
    # The following regex is for the Worklog from the GCP - from restoration model (see PSNR)
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


def extract_epoch_val(s):       # TODO
    # The following regex is for the Worklog from the GCP - from restoration model (see PSNR)
    in_pattern = re.compile(r""".*\sval_loss:\s(?P<vloss>\d+\.?\d*)
                                \s-\sval_acc:\s(?P<vacc>\d+\.?\d*)
                                \n""", re.VERBOSE)
    in_match = in_pattern.findall(s)

    v_loss = [ite[0] for ite in in_match]
    v_acc = [ite[1] for ite in in_match]

    return v_loss, v_acc


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
    in_pattern = re.compile(r""".*\sval_loss:\s(?P<vloss>\d+\.?\d*)
                                \s-\sval_acc:\s(?P<vpsnr>\d+\.?\d*)
                                \n""", re.VERBOSE)
    in_match = in_pattern.findall(s)

    v_loss = [ite[0] for ite in in_match]
    v_acc = [ite[1] for ite in in_match]

    return v_loss, v_acc


def pick_file():
    fname, filt, flags = win32gui.GetOpenFileNameW(
        InitialDir=environ['temp'],
        Flags=win32con.OFN_EXPLORER,
        File='somefilename', DefExt='log',
        Title='GetOpenFileNameW',
        Filter='Selected extensions\0*.*\0',
        FilterIndex=0)
    return fname


def Mbox(title, text, style):
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)


run()
    # image_location = params['inputImagePath']
    # result_location = params['resultPath']
    # imsave(result_location, output_data)