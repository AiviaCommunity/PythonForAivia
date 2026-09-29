import os
import sys
import shlex
import subprocess
import imagecodecs
import numpy as np
from skimage import transform
from skimage.util import img_as_uint, img_as_ubyte
from tifffile import imread, imwrite
from os.path import dirname as up
import re

DEFAULT_OUTPUT_FOLDER = r''

"""
Rotates a 2D image given the user-defined angle.
Works only for single channels.

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
# [INPUT Name:resize Type:int DisplayName:'Resize image (0 = No, 1 = Yes)' Default:0 Min:0 Max:1]
# [INPUT Name:rotAngle Type:int DisplayName:'Rotation Angle (-180 to 180)' Default:90 Min:0 Max:180]
# [OUTPUT Name:resultPath Type:string DisplayName:'Rotated channel']
def run(params):
    global interpolation_mode
    # image_org = params['EntryPoint']
    image_location = params['inputImagePath']
    result_location = params['resultPath']
    zCount = int(params['ZCount'])
    tCount = int(params['TCount'])
    pixel_cal_tmp = params['Calibration']
    pixel_cal = pixel_cal_tmp[6:].split(', ')           # Expects calibration with 'XYZT: ' in front
    rot_angle = int(params['rotAngle']) * (-1)          # 1 axis is inverted from Aivia to python
    do_resize = True if params['resize'] == '1' else False

    if abs(rot_angle) > 360:
        error_mess = f"Error: {rot_angle} value is not appropriate as a rotating angle"
        Mbox('Error', error_mess, 0)
        sys.exit(error_mess)

    # Getting XY and Z calibration values                # Expecting only 'Micrometers' in this code
    XY_cal = float(pixel_cal[0].split(' ')[0])
    Z_cal = float(pixel_cal[2].split(' ')[0])
    
    if not os.path.exists(image_location):
        print(f"Error: {image_location} does not exist")
        return

    raw_data = imread(image_location)
    dims = raw_data.shape
    print('-- Input dimensions (expected (Z), Y, X): ', np.asarray(dims), ' --')

    # Checking image is not 2D+t or 3D+t
    if len(dims) > 2 or tCount > 1:
        error_mess = 'Error: Image should be 2D only.'
        Mbox('Error', error_mess, 0)
        sys.exit(error_mess)

    # Rotation
    processed_data = transform.rotate(raw_data, rot_angle, resize=do_resize, order=interpolation_mode)

    # Formatting result array
    if raw_data.dtype is np.dtype('u2'):
        out_data = img_as_uint(processed_data)
    else:
        out_data = img_as_ubyte(processed_data)

    if do_resize:
        # Defining axes for output metadata and scale factor variable
        axes = 'YX'
        meta_info = {'axes': axes, 'spacing': str(Z_cal), 'unit': 'um'}  # TODO: change to TZCYX for ImageJ style???

        # Formatting voxel calibration values
        inverted_XY_cal = 1 / XY_cal

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
                output_name = f"{img_name}_Rot{rot_angle * -1}deg.tif"

                out_path = os.path.join(output_folder, output_name)

        if not out_path:
            out_path = result_location.replace('.tif', 'tmp.tif')

        print('Saving image in location:\n', out_path)
        imwrite(out_path, out_data, imagej=True, photometric='minisblack', metadata=meta_info,
                resolution=(inverted_XY_cal, inverted_XY_cal))

        # Added for handling testing without opening aivia
        if aivia_path == "None":
            return
        if not os.path.exists(aivia_path):
            print(f"Error: {aivia_path} does not exist")
            return
        # Run external program
        cmdLine = 'start \"\" \"' + aivia_path + '\" \"' + out_path + '\"'

        args = shlex.split(cmdLine)
        subprocess.run(args, shell=True)

        mess = 'Rotated image with new dimensions is available in the Image Explorer'
        Mbox('Process complete', mess, 0)
        imwrite(result_location, np.zeros_like(raw_data))

    else:
        imwrite(result_location, out_data)


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
        return result.stdout.strip()  # return = "Ok" or "Cancel"
    except:
        return None


if __name__ == '__main__':
    params = {'inputImagePath': r'D:\PythonCode\_tests\2D-image.tif',
              'resultPath': r'D:\PythonCode\_tests\output.tif',
              'TCount': 1,
              'ZCount': 1,
              'Calibration': 'XYZT: 0.46 micrometers, 0.46 micrometers, 0.46 micrometers, 1 Default',
              'rotAngle': 15,
              'resize': 0}
    run(params)

# CHANGELOG
# v1_00: - Including isotropic scaling and proper export to Aivia
# v1.10: - Adding default folder for potential batch functionality (input still can't be put in a workflow)
# v1.11: - Changed ctypes Mbox to VB
