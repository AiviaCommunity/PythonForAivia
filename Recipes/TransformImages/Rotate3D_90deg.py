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

import shlex
import subprocess
import imagecodecs
import numpy as np
from skimage import transform, img_as_uint, img_as_ubyte
from tifffile import imread, imwrite
from os.path import dirname as up
from magicgui import magicgui


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

axis_rot_options = {'ClockWise': {'X': (1, 0), 'Y': (0, 2), 'Z': (2, 1)},
                    'CounterClockWise': {'X': (0, 1), 'Y': (2, 0), 'Z': (1, 2)}}
interpolation_mode = 1  # 0: Nearest-neighbor, 1: Bi-linear , 2: Bi-quadratic, 3: Bi-cubic, 4: Bi-quartic, 5: Bi-quintic


# Get path to the Aivia executable
def getParentDir(curr_dir, level=1):
    for i in range(level):
        parent_dir = up(curr_dir)
        curr_dir = parent_dir
    return curr_dir


exeDir = sys.executable
parentDir = getParentDir(exeDir, level=2)
aivia_path = parentDir + '\\Aivia.exe'


# [INPUT Name:inputImagePath Type:string DisplayName:'Input Channel']
# [OUTPUT Name:resultPath Type:string DisplayName:'Duplicate of input']
def run(params):
    global axis_rot_options, interpolation_mode
    # image_org = params['EntryPoint']
    image_location = params['inputImagePath']
    result_location = params['resultPath']
    zCount = int(params['ZCount'])
    tCount = int(params['TCount'])
    pixel_cal_tmp = params['Calibration']
    pixel_cal = pixel_cal_tmp[6:].split(', ')           # Expects calibration with 'XYZT: ' in front

    # Getting XY and Z calibration values                # Expecting only 'Micrometers' in this code
    XY_cal = float(pixel_cal[0].split(' ')[0])
    Z_cal = float(pixel_cal[2].split(' ')[0])
    Z_ratio = float(Z_cal) / float(XY_cal)
    
    if not os.path.exists(image_location):
        print(f"Error: {image_location} does not exist")
        return

    if not os.path.exists(aivia_path):
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
    @magicgui(axis={"label": "Select the rotation axis:", "widget_type": "RadioButtons",
                    'choices': swap_axes_options.keys()},
              direction={"label": "Select the rotation direction:", "widget_type": "RadioButtons",
                         'choices': axis_rot_options.keys()},
              call_button="Run")
    def get_rot_param(axis=list(swap_axes_options.keys())[0], direction=list(axis_rot_options.keys())[0]):
        pass

    @get_rot_param.called.connect
    def close_GUI_callback():
        get_rot_param.close()

    get_rot_param.show(run=True)
    rot_axis = get_rot_param.axis.value
    rot_dir = get_rot_param.direction.value

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
    meta_info = {'axes': axes, 'spacing': str(final_cal), 'unit': 'um'}

    # Formatting voxel calibration values
    inverted_XY_cal = 1 / final_cal

    tmp_path = result_location.replace('.tif', '-rotated.tif')
    print('Saving image in temp location:\n', tmp_path)
    imwrite(tmp_path, out_data, imagej=True, photometric='minisblack', metadata=meta_info,
            resolution=(inverted_XY_cal, inverted_XY_cal))

    # Dummy save
    # dummy_data = np.zeros(image_data.shape, dtype=image_data.dtype)
    # imwrite(result_location, dummy_data)

    # Run external program
    cmdLine = 'start \"\" \"' + aivia_path + '\" \"' + tmp_path + '\"'

    args = shlex.split(cmdLine)
    subprocess.run(args, shell=True)


if __name__ == '__main__':
    params = {'inputImagePath': r'D:\PythonCode\_tests\3D_Embryo_Fluo-IsotropicCube-8b.aivia.tif',
              'resultPath': r'D:\PythonCode\_tests\output.tif',
              'TCount': 1,
              'ZCount': 192,
              'Calibration': 'XYZT: 0.46 micrometers, 0.46 micrometers, 0.46 micrometers, 1 Default'}
    run(params)

# CHANGELOG
# v1_00: - Including isotropic scaling and proper export to Aivia
# v1_10: - Adding a GUI to choose rotation axis + virtual environment activation
# v1_11: - New virtual env code for auto-activation
