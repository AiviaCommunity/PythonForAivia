import os.path
import numpy as np
from skimage.io import imread, imsave
import shlex, subprocess
import sys
from os.path import dirname as up
from os.path import isfile

"""
Performs a maximum intensity projection through Z for a single channel.

Works only in 3D (not 3D+t yet).

Requirements
------------
numpy (comes with Aivia installer)
scikit-image (comes with Aivia installer)

Parameters
----------
Input channel:
    Input channel to use for the projection.

Returns
-------
New channel in original 3D image:
    Returns a binary map of the location of max values detected in volume.

New 2D image:
    Opens Aivia (again) to display the 2D projection as a new image.

"""


# [INPUT Name:inputImagePath Type:string DisplayName:'Input Image']
# [OUTPUT Name:resultPath Type:string DisplayName:'Max Intensity Location']
def run(params):
    image_location = params['inputImagePath']
    result_location = params['resultPath']
    tCount = int(params['TCount'])
    aivia_path = params['CallingExecutable']
    if not os.path.exists(image_location):
        print(f"Error: {image_location} does not exist")
        return
    
    if not os.path.exists(aivia_path):
        print(f"Error: {aivia_path} does not exist")
        return
        
    image_data = imread(image_location)
    dims = image_data.shape
    print('-- Input dimensions (expected Z, Y, X): ', np.asarray(dims), ' --')
    
    # Checking image is not 2D or 2D+t
    if len(dims) == 2 or (len(dims) == 3 and tCount > 1):
        print('Error: Maximum intensity projection cannot be applied to 2D images.')
        return
    
    output_data = np.empty_like(image_data)
    proj_output = output_data[0, :, :]
    
    # Value for binary map
    int_info = np.iinfo(image_data.dtype)
    vbin = int_info.max
    
    if tCount == 1:     # (image is not 3D+t)
        # Generate 2D max projection
        proj_output = np.amax(image_data, axis = 0)
        
        for z in np.arange(0, dims[0]):
            current_z = image_data[z, :, :]
            curr_z_nozeros = np.where(current_z > 0, current_z, -1)
            output_data[z, :, :] = np.where(curr_z_nozeros < proj_output, 0, vbin)
        
        temp_location = result_location.replace('.tif', 'tmp.tif')
        imsave(temp_location, proj_output)
    
    imsave(result_location, output_data)
    
    # Run external program
    cmdLine = 'start \"\" \"'+ aivia_path +'\" \"'+ temp_location +'\"'
    
    args = shlex.split(cmdLine)
    subprocess.run(args, shell=True)


if __name__ == '__main__':
    params = {}
    params['inputImagePath'] = 'D:\\python-tests\\3Dimage.aivia.tif'
    params['resultPath'] = 'D:\\python-tests\\3DMaxMap.tif'
    params['TCount'] = 1
    
    run(params)
