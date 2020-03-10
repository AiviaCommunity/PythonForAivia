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
"""

# [INPUT Name:inputImagePath Type:string DisplayName:'Input Image']
# [INPUT Name:width Type:int DisplayName:'Width' Default:3 Min:2 Max:1000]
# [OUTPUT Name:resultPath Type:string DisplayName:'MaximumZ']
def run(params):
    image_location = params['inputImagePath']
    result_location = params['resultPath']
    width = int(params['width'])
    if not os.path.exists(image_location):
        print(f'Error: {image_location} does not exist')
        return;
        
    image_data = imread(image_location)
    print(f'Input data shape : {image_data.shape}')
    
    if len(image_data.shape) == 2:
        print(f'Error: Maximum intensity projection cannot be applied to 2D images.')
        return;
    
    output_data = np.empty_like(image_data)
    
    width_eff = int(width/2)
    max_slice = int(image_data.shape[0])
    for i in np.arange(0,max_slice):
        output_data[i,:,:] = np.amax(image_data[i-min(width_eff,i):i+min(width_eff,max_slice-i),:,:], axis=0)

    imsave(result_location, output_data)


if __name__ == '__main__':
    params = {}
    params['inputImagePath'] = 'test.png'
    params['resultPath'] = 'testResult.png'
    params['width'] = 2;
    
    run(params)


# CHANGELOG
# v1.00 TL - Original script by Trevor Lancon (trevorl@drvtechnologies.com)
#