import os.path
import shlex
import subprocess
import imagecodecs
import numpy as np
from tifffile import imread, imwrite
from skimage import transform, img_as_uint, img_as_ubyte
import sys
from os.path import dirname as up


"""
Scales the input channel up or down (isotropic factor). Option for interpolation is in the code.
Works only for 2D/3D (not timelapses) and for single channels.

Documentation
-------------
https://scikit-image.org/docs/stable/api/skimage.transform.html#skimage.transform.rescale

Requirements
------------
numpy (comes with Aivia installer)
scikit-image (comes with Aivia installer)
imagecodecs (comes with Aivia installer)
tifffile (comes with Aivia installer)

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
def getParentDir(currDir, level=1):

    for i in range(level):
        parentDir = up(currDir)
        currDir=parentDir

    return currDir

exeDir = sys.executable
parentDir = getParentDir(exeDir, level=2)
aivia_path = parentDir + '\\Aivia.exe'


# automatic parameters


# [INPUT Name:inputImagePath Type:string DisplayName:'Input Channel']
# [INPUT Name:scaleDirection Type:int DisplayName:'Down or Upscale (0 or 1)' Default:0 Min:0 Max:1]
# [INPUT Name:scaleFactorZ Type:double DisplayName:'Z scale factor' Default:1.0 Min:0.01 Max:20.0]
# [INPUT Name:scaleFactorXY Type:double DisplayName:'XY scale factor' Default:1.0 Min:0.01 Max:20.0]
# [OUTPUT Name:resultPath Type:string DisplayName:'Duplicate of input']
def run(params):
    image_org=params['EntryPoint']
    image_location = params['inputImagePath']
    result_location = params['resultPath']
    scale_factor_xy = float(params['scaleFactorXY'])
    scale_factor_z = float(params['scaleFactorZ'])
    scale_direction = int(params['scaleDirection'])
    zCount = int(params['ZCount'])
    tCount = int(params['TCount'])
    pixel_cal_tmp = params['Calibration']
    pixel_cal = pixel_cal_tmp[6:].split(', ')           # Expects calibration with 'XYZT: ' in front

    # Getting XY and Z values                # Expecting only 'Micrometers' in this code
    XY_cal = float(pixel_cal[0].split(' ')[0])
    Z_cal = float(pixel_cal[2].split(' ')[0])
    
    if not os.path.exists(image_location):
        print(f"Error: {image_location} does not exist")
        return

    if not os.path.exists(aivia_path):
        print(f"Error: {aivia_path} does not exist")
        return

    image_data = imread(image_location)
    dims = image_data.shape
    print('-- Input dimensions (expected (Z), Y, X): ', np.asarray(dims), ' --')

    # Checking image is not 2D+t or 3D+t
    if len(dims) > 3 or (len(dims) == 3 and tCount > 1):
        print('Error: Cannot handle timelapses yet.')
        return

    if scale_factor_xy == 0.0:
        scale_factor_xy = 1.0                 #TODO: manual input for batch
    if scale_factor_z == 0.0:
        scale_factor_z = 1.0                  #TODO
        
    if scale_direction == 0:        
        scale_factor_xy = 1/scale_factor_xy
        scale_factor_z = 1/scale_factor_z
    else:
        scale_factor_xy = scale_factor_xy
        scale_factor_z = scale_factor_z    
        
    # Calculating final pixel calibration
    final_XY_cal = XY_cal / scale_factor_xy
    final_Z_cal = Z_cal / scale_factor_z
       
    # Defining axes for output metadata and scale factor variable
    final_scale = None
    if tCount == 1 and zCount > 1:         # 3D
        axes = 'ZYX'       # Data is 'YXZ'
        final_scale = (scale_factor_z, scale_factor_xy, scale_factor_xy)

    elif tCount == 1 and zCount == 1:      # 2D
        axes = 'YX'
        final_scale = scale_factor_xy

    scaled_img = transform.rescale(image_data, final_scale, interpolation_mode)

    # Formatting result array
    
    if image_data.dtype is np.dtype('u2'):
        out_data = img_as_uint(scaled_img)
        print('img_as_uint')
    else:
        out_data = img_as_ubyte(scaled_img)
        print('img_as_ubyte')
    
    # Formatting voxel calibration values
    formatted_XY_cal = '{0:.4g}'.format(final_XY_cal)

    tmp_path = result_location.replace('.tif', '-scaled.tif')
    meta_info = {'axes': axes,
                'PhysicalSizeX': formatted_XY_cal,
                'PhysicalSizeY': formatted_XY_cal,
                'PhysicalSizeZ': str(final_Z_cal),
                'PhysicalSizeXUnit': '\xb5m',
                'PhysicalSizeYUnit': '\xb5m',
                'PhysicalSizeZUnit': '\xb5m'}       # '\xb5m' for microns?

    print('Saving image in temp location:\n', tmp_path)
    imwrite(tmp_path, out_data, ome=True, photometric='minisblack', metadata=meta_info)

    # Dummy save
    imwrite(result_location, image_data)

    # Run external program
    cmdLine = 'start \"\" \"' + aivia_path + '\" \"' + tmp_path + '\"'
    # cmdLine = 'start \"\" \"' + IJ_path + '\" \"' + tmp_path + '\"'

    args = shlex.split(cmdLine)
    subprocess.run(args, shell=True)


if __name__ == '__main__':
    params = {'inputImagePath': 'D:\\python-tests\\3D-image.aivia.tif',
              'resultPath': 'D:\\python-tests\\scaled.tif',
              'TCount': 1,
              'ZCount': 51}
    run(params)

# CHANGELOG
# v1_00: - scaling in XYZ with same factor
# v1_10: - scaling in XY and Z are now independent
# v1_11: - tkinter not installed by default so removing all code and adding parameters in Aivia UI
# v1_13: - Fallback values if factors equal 0 / automated detection of latest Aivia version on PC
# v1_14: - Adding pixel/voxel calibration
