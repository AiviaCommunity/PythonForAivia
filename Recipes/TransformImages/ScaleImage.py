import os.path
import shlex
import subprocess
import imagecodecs
import numpy as np
from tifffile import imread, imwrite
from skimage import transform, img_as_uint, img_as_ubyte
import sys


"""
Scales the input channel up or down (isotropic factor). Option for interpolation is in the code.
Works only for 2D/3D rescaling (not timelapses) but can be applied on a per timepoint basis.
Works for single channels.

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

IJTimeUnit = {'Minutes': 'min', 'Seconds': 's', 'Milliseconds': 'ms', 'Microseconds': 'us'}


# [INPUT Name:inputImagePath Type:string DisplayName:'Input Channel']
# [INPUT Name:scaleDirection Type:int DisplayName:'Down or Upscale (0 or 1)' Default:0 Min:0 Max:1]
# [INPUT Name:scaleFactorZ Type:double DisplayName:'Z scale factor' Default:1.0 Min:0.01 Max:20.0]
# [INPUT Name:scaleFactorXY Type:double DisplayName:'XY scale factor' Default:1.0 Min:0.01 Max:20.0]
# [OUTPUT Name:resultPath Type:string DisplayName:'Duplicate of input']
def run(params):
    image_org = params['EntryPoint']
    image_location = params['inputImagePath']
    result_location = params['resultPath']
    scale_factor_xy = float(params['scaleFactorXY'])
    scale_factor_z = float(params['scaleFactorZ'])
    scale_direction = int(params['scaleDirection'])
    zCount = int(params['ZCount'])
    tCount = int(params['TCount'])
    pixel_cal_tmp = params['Calibration']
    pixel_cal = pixel_cal_tmp[6:].split(', ')           # Expects calibration with 'XYZT: ' in front
    aivia_path = params['CallingExecutable']

    # Getting XY and Z values                # Expecting only 'Micrometers' in this code
    XY_cal = float(pixel_cal[0].split(' ')[0])
    Z_cal = float(pixel_cal[2].split(' ')[0])
    T_cal = float(pixel_cal[3].split(' ')[0])
    
    # Check real calibration
    real_XYZ_calibration, real_T_calibration = False, False
    if not 'efault' in pixel_cal[0].split(' ')[1]:      # calibration ok
        real_XYZ_calibration = True
    if not 'efault' in pixel_cal[3].split(' ')[1]:      # calibration ok
        real_T_calibration = True
    
    if not os.path.exists(image_location):
        print(f"Error: {image_location} does not exist")
        return

    if not os.path.exists(aivia_path):
        print(f"Error: {aivia_path} does not exist")
        return

    image_data = imread(image_location)
    dims = image_data.shape
    print('-- Input dimensions (expected (T) (Z), Y, X): ', np.asarray(dims), ' --')

    if scale_factor_xy == 0.0:
        scale_factor_xy = 1.0
    if scale_factor_z == 0.0:
        scale_factor_z = 1.0
        
    if scale_direction == 0:        
        scale_factor_xy = 1/scale_factor_xy
        scale_factor_z = 1/scale_factor_z
    else:
        scale_factor_xy = scale_factor_xy
        scale_factor_z = scale_factor_z    
        
    # Calculating final pixel calibration
    final_XY_cal = XY_cal / scale_factor_xy if real_XYZ_calibration else 1
    final_Z_cal = Z_cal / scale_factor_z if real_XYZ_calibration else 1
       
    # Defining axes for output metadata and scale factor variable
    final_scale = None
    axes = ''
    if tCount > 1 and zCount > 1:  # 3D + T
        axes = 'TZYX'
        final_scale = (1, scale_factor_z, scale_factor_xy, scale_factor_xy)

    elif tCount > 1 and zCount == 1:  # 2D + T
        axes = 'TYX'
        final_scale = (1, scale_factor_xy, scale_factor_xy)

    elif tCount == 1 and zCount > 1:         # 3D
        axes = 'ZYX'        # should be 'YXZ'
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

    tmp_path = result_location.replace('.tif', '-scaled.tif')
    meta_info = {'axes': axes}
    if real_XYZ_calibration and zCount > 1:
        meta_info.update({'spacing': str(final_Z_cal), 'unit': 'um'})
    if real_T_calibration:
        meta_info.update({'TimeIncrement': T_cal, 'TimeIncrementUnit': IJTimeUnit[pixel_cal[3].split(' ')[1]]})

    # Formatting voxel calibration values
    inverted_XY_cal = 1 / final_XY_cal
    print(final_XY_cal)

    print('Saving image in temp location:\n', tmp_path)
    if real_XYZ_calibration:
        imwrite(tmp_path, out_data, imagej=True, photometric='minisblack', metadata=meta_info,
                resolution=(inverted_XY_cal, inverted_XY_cal))
    else:
        # To avoid calibration in XYZ
        imwrite(tmp_path, out_data, imagej=True, photometric='minisblack', metadata=meta_info) 
    
    # Dummy save
    dummy_data = np.zeros(image_data.shape, dtype=image_data.dtype)
    imwrite(result_location, dummy_data)

    # Run external program
    cmdLine = 'start \"\" \"' + aivia_path + '\" \"' + tmp_path + '\"'

    args = shlex.split(cmdLine)
    subprocess.run(args, shell=True)


if __name__ == '__main__':
    params = {'inputImagePath': 'D:\\PythonCode\\_tests\\3D-TL-toalign.aivia.tif',
              'resultPath': 'D:\\PythonCode\\_tests\\Output.tif',
              'TCount': 16,
              'ZCount': 41,
              'Calibration': 'XYZT: 0.4 Micrometers, 0.4 Micrometers, 1.2 Micrometers, 599.9996 Seconds',
              'scaleFactorXY': 2,
              'scaleFactorZ': 1,
              'scaleDirection': 0,
              'EntryPoint': '',
              'CallingExecutable': ''}
    run(params)

# CHANGELOG
# v1_00: - scaling in XYZ with same factor
# v1_10: - scaling in XY and Z are now independent
# v1_11: - tkinter not installed by default so removing all code and adding parameters in Aivia UI
# v1_13: - Fallback values if factors equal 0 / automated detection of latest Aivia version on PC
# v1_14: - Adding pixel/voxel calibration
# v1_20: - Adding time handling (but not rescale with time dimension)
# v1_30: - Fusing with parallel version updating aivia_path using new API params value
#        - Time increment is not recognized in Aivia at the moment
