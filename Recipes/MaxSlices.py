import os.path
import numpy as np
from skimage.io import imread, imsave

"""
Performs a slicewise maximum intensity projection through Z with a given
width about a slice.

For example, using a width value of 2 means that for every slice, every
voxel in XY will be replaced with the maximum value found within the 2
slices before and after that slice.

Works only in 3D.

Requirements
------------
numpy
scikit-image

Parameters
----------
Input Image : Aivia channel
    Input channel to use for the transform.

Width : int
    Number of slices around the current slice to consider for the MIP.

Returns
-------
Aivia channel
    Result of the transform

"""

# [INPUT Name:inputImagePath Type:string DisplayName:'Input Image']
# [INPUT Name:width Type:int DisplayName:'Width' Default:3 Min:2 Max:1000]
# [OUTPUT Name:resultPath Type:string DisplayName:'MaximumZ']
def run(params):
    image_location = params['inputImagePath']
    result_location = params['resultPath']
    width = int(params['width'])
    tCount = int(params['TCount'])
    if not os.path.exists(image_location):
        print(f"Error: {image_location} does not exist")
        return;
        
    image_data = imread(image_location)
    dims = image_data.shape
    output_data = np.empty_like(image_data)
    
    if len(dims) == 2 or (len(dims) == 3 and tCount > 1):
        print('Error: Maximum intensity projection cannot be applied to 2D images.')
        return;
    
    if tCount == 1:
        max_slice = int(dims[0])
        width_eff = min(int(width/2), max_slice)
        for i in np.arange(0, max_slice):
            output_data[i, :, :] = np.amax(
                image_data[i-min(width_eff,i):i+min(width_eff,max_slice-i), :, :], axis=0
            )
    else:
        max_slice = int(dims[1])
        width_eff = min(int(width/2), max_slice)
        for i in np.arange(0, max_slice):
            output_data[:, i, :, :] = np.amax(
                image_data[:, i-min(width_eff,i):i+min(width_eff,max_slice-i), :, :], axis=1
            )
            
    imsave(result_location, output_data)


if __name__ == '__main__':
    params = {}
    params['inputImagePath'] = 'test.png'
    params['resultPath'] = 'testResult.png'
    params['width'] = 2;
    
    run(params)
