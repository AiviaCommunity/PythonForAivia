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

from magicgui import magicgui
from skimage.io import imread, imsave
import numpy as np
from pystackreg import StackReg
from pystackreg.util import to_uint16
import imagecodecs

# Manual input parameters (only used if 'use' is True below)
noGUI_params = {'use': False,
                'reg_type': 'Rigid Body',
                'reg_method': 'previous'
                }

"""
Performs a 2D registration for timelapses, using PyStackReg, on one channel but transform the two specified channels. 
No parameters available (default ones only).
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
PySide2
magicgui

Parameters
----------
Input:
    Channel/image in Aivia to be aligned
  
Output
------
New channel with registered images
"""

n_channels = 2      # To adjust for more channels

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

# [INPUT Name:inputRawImagePath1 Type:string DisplayName:'Unregistered Ch 2']
# [INPUT Name:inputRawImagePath2 Type:string DisplayName:'Unregistered Ch 1 (aligned)']
# [OUTPUT Name:resultPath1 Type:string DisplayName:'Registered Ch 2']
# [OUTPUT Name:resultPath2 Type:string DisplayName:'Registered Ch 1']
def run(params):
    global reg_methods, reg_types, n_channels

    rawImageLocation = [params['inputRawImagePath' + str(val)] for val in range(1, n_channels + 1)]
    resultLocation = [params['resultPath' + str(val)] for val in range(1, n_channels + 1)]
    calibration = params['Calibration']
    tCount = int(params['TCount'])
    zCount = int(params['ZCount'])

    if tCount < 2:
        show_error(f'Error: detected dimensions do not contain time. (t={tCount})')
    if zCount > 1 and tCount > 1:
        show_error(f'Error: detected dimensions contain time and depth. This script is for 2D only. (t={tCount}, z={zCount})')

    # Checking existence of temporary files (individual channels)
    if not os.path.exists(rawImageLocation[0]):
        show_error(f'Error: {rawImageLocation[0]} does not exist')

    # Load input channels
    raw_npimgs = [imread(rawImageLocation[j]) for j in range(0, n_channels)]
    raw_dims = np.asarray(raw_npimgs[0].shape)
    print('-- Input dimensions (expected T, Z, Y, X): ', raw_dims, ' --')

    # Checking Time axis
    if raw_npimgs[0].shape[0] != tCount:
        show_error(f'Error: time dimension was not found on axis 1 (TYX).'
                   f'\nContact support team, mentioning if image was cropped or not.')

    # Check manual inputs
    if noGUI_params['use']:
        reg_type = noGUI_params['reg_type']
        reg_method = noGUI_params['reg_method']

    else:  # Choose csv/xlsx table (Aivia format) with GUI
        gui.called.connect(lambda x: gui.close())
        gui.show(run=True)

        # Parameters collected from the GUI
        reg_type = reg_types[gui.reg_typ.value]
        reg_method = reg_methods[gui.reg_meth.value]

    # Prepare parameters for registration
    sr = StackReg(reg_type)

    # Compute registration of 2D timelapse
    sr.register_stack(raw_npimgs[0], reference=reg_method)

    # Transform all channels
    out_npimgs, final_imgs = [], []
    for ch in range(0, n_channels):
        out_npimgs.append(sr.transform_stack(raw_npimgs[ch]))

        print(f'Raw image: Min = {np.min(raw_npimgs[0])}, Max = {np.max(raw_npimgs[0])}')
        print(f'Processed image: Min = {np.min(out_npimgs[0])}, Max = {np.max(out_npimgs[0])}')

        # Formatting result array
        if raw_npimgs[0].dtype is np.dtype('uint8'):
            final_imgs.append(out_npimgs[ch].clip(min=0, max=255).astype(raw_npimgs[0].dtype))
        else:
            final_imgs.append(to_uint16(out_npimgs[ch]).astype(raw_npimgs[0].dtype))

        # Save result
        imsave(resultLocation[ch], final_imgs[ch])


@magicgui(layout='vertical',
          reg_typ={'label': 'Registration type: ', 'choices': reg_types.keys()},
          reg_meth={'label': 'Registration reference: ', 'choices': reg_methods.keys()},
          call_button="Continue")
def gui(reg_typ=[*reg_types][0], reg_meth=[*reg_methods][0]):
    pass


def show_error(message):
    ctypes.windll.user32.MessageBoxW(0, message, 'Error', 0)
    sys.exit(message)


if __name__ == '__main__':
    params = {}
    # params['inputRawImagePath1'] = r'D:\PythonCode\Python_scripts\Projects\PythonEnvForAivia_A15.0_Py3.12\Tests' \
    #                                r'\InputTestImages\Test_8bit_TYX_Particles.aivia.tif'               # T=20
    params['inputRawImagePath1'] = r'D:\PythonCode\Python_scripts\Projects\PythonEnvForAivia_A15.0_Py3.12\Tests' \
                                   r'\InputTestImages\Test_16bit_TYX_2DandT_Nuclei_Crop.aivia.tif'       # T=3
    params['inputRawImagePath2'] = params['inputRawImagePath1']
    params['resultPath1'] = r'D:\PythonCode\_tests\2D-TL-aligned.tif'
    params['resultPath2'] = params['resultPath1']
    params['Calibration'] = '  : 0.4 microns, 0.4 microns, 1.2 microns, 2 seconds'
    params['TCount'] = 3
    params['ZCount'] = 1

    run(params)

# CHANGELOG
# v1_00 PM: - From StackReg_ImageAlignment_v1_11.py
