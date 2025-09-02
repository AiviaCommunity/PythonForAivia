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

    # Register 2D timelapse
    out_npimg = sr.register_transform_stack(raw_npimg, reference=reg_method)
    print(f'Raw image: Min = {np.min(raw_npimg)}, Max = {np.max(raw_npimg)}')
    print(f'Processed image: Min = {np.min(out_npimg)}, Max = {np.max(out_npimg)}')

    # Formatting result array
    # print(raw_npimg.dtype)
    if raw_npimg.dtype is np.dtype('uint8'):
        final_img = out_npimg.clip(min=0, max=255).astype(raw_npimg.dtype)
    else:
        final_img = to_uint16(out_npimg).astype(raw_npimg.dtype)

    # Save result
    imsave(resultLocation, final_img)


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
    # params['inputRawImagePath'] = r'D:\PythonCode\Python_scripts\Projects\PythonEnvForAivia_A15.0_Py3.12\Tests' \
    #                               r'\InputTestImages\Test_8bit_TYX_Particles.aivia.tif'
    params['inputRawImagePath'] = r'D:\PythonCode\Python_scripts\Projects\PythonEnvForAivia_A15.0_Py3.12\Tests' \
                                  r'\InputTestImages\Test_16bit_TYX_2DandT_Nuclei_Crop.aivia.tif'
    params['resultPath'] = r'D:\PythonCode\_tests\2D-TL-aligned.tif'
    params['Calibration'] = '  : 0.4 microns, 0.4 microns, 1.2 microns, 2 seconds'
    params['TCount'] = 3
    params['ZCount'] = 1

    run(params)

# CHANGELOG
# v1_00 PM: - Registration with default parameters of PyStackReg
# v1_01 PM: - New virtual env code for auto-activation
# v1_10 PM: - Works in 15.0 but black pixels instead of white saturated ones are present in resulting image.
# v1_11 PM: - Fixed black and white pixels in registered images for 8 bit images
