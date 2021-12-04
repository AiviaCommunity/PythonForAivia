import os.path
import numpy as np
from skimage.io import imread, imsave
import shlex, subprocess
import sys
from os.path import dirname as up

"""
Performs a maximum intensity projection through Z for a single channel. 
Repeats the operation for the two other channels of the RGB image.

Works only in 3D (not 3D+t yet).

Requirements
------------
numpy (comes with Aivia installer)
scikit-image (comes with Aivia installer)

Parameters
----------
Input channels:
    3 input channels to use for the projection.

Returns
-------
New channels in original 3D image:
    Returns a binary map of the location of max values detected in volume.

New 3-channel 2D image:
    Opens Aivia (again) to display the 2D projection as a new image.

"""

#Get path to the Aivia executable
def getParentDir(currDir, level=1):

    for i in range(level):
        parentDir = up(currDir)
        currDir=parentDir

    return currDir

exeDir=sys.executable
parentDir=getParentDir(exeDir, level=2)
aivia_path = parentDir +'\\Aivia.exe'


# [INPUT Name:inputRedPath Type:string DisplayName:'Red channel']
# [INPUT Name:inputGreenPath Type:string DisplayName:'Green channel']
# [INPUT Name:inputBluePath Type:string DisplayName:'Blue channel']
# [OUTPUT Name:resultPath Type:string DisplayName:'Empty channel']
def run(params):
    image_location = []
    image_location.append(params['inputRedPath'])
    image_location.append(params['inputGreenPath'])
    image_location.append(params['inputBluePath'])
    result_location = params['resultPath']
    tCount = int(params['TCount'])
    
    for c in range(0, 3):
        if not os.path.exists(image_location[c]):
            print(f"Error: {image_location[c]} does not exist")
            return;
    
    if not os.path.exists(aivia_path):
        print(f"Error: {aivia_path} does not exist")
        return;
    
    first_ch = imread(image_location[0])
    input_dims = np.asarray(first_ch.shape)
    print('-- Input dimensions (expected Z, Y, X): ', input_dims, ' --')
    
    new_input_dims = np.insert(input_dims, 0, 3)
    image_data = np.zeros(new_input_dims).astype(first_ch.dtype)
    
    for c in range(0, 3):
        image_data[c] = imread(image_location[c])
    
    # Checking image is not 2D or 2D+t
    if input_dims.size == 2 or (input_dims.size == 3 and tCount > 1):
        print('Error: Maximum intensity projection cannot be applied to 2D images.')
        return;
    
    output_data = np.empty_like(first_ch)
    proj_output = np.zeros([input_dims[1], input_dims[2], 3])       # TO CHECK
    
    for c in range(0, 3):
        if tCount == 1:     # (image is not 3D+t)
            # Generate 2D max projection for each channel
            proj_output[:, :, 2-c] = np.amax(image_data[c], axis = 0)
    
    # Saving 3 channel image as single tif
    temp_location = result_location.replace('.tif', 'tmp.tif')
    imsave(temp_location, proj_output.astype(np.uint8))
    
    imsave(result_location, output_data)
    
    # Run external program
    cmdLine = 'start \"\" \"'+ aivia_path +'\" \"'+ temp_location +'\"'
    
    args = shlex.split(cmdLine)
    subprocess.run(args, shell=True)


if __name__ == '__main__':
    params = {}
    params['inputRedPath'] = 'D:\\python-tests\\3Dimage.aivia.tif'
    params['inputGreenPath'] = 'D:\\python-tests\\3Dimage.aivia.tif'
    params['inputBluePath'] = 'D:\\python-tests\\3Dimage.aivia.tif'
    params['resultPath'] = 'D:\\python-tests\\3DMaxMap.tif'
    params['TCount'] = 1
    
    run(params)
