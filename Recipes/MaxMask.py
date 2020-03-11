import os.path
import numpy as np
from skimage.io import imread, imsave

"""
Given an input image (I) and a mask image (M), returns (O) the input image only where
the mask image is BELOW a specified threshold (t).

O(x,y) = I(X,Y) * [M(X,Y)<t]

Requirements
------------
numpy
scikit-image

Parameters
----------
Input Image : Aivia channel
    Input channel to be masked.

Input Mask : Aivia channel
    Input channel to use for the mask after thresholding.

Threshold : int
    Grayvalue in above which we would like to mask.

Returns
-------
Aivia channel
    Result of the transform
"""

# [INPUT Name:inputImagePath Type:string DisplayName:'Input Image']
# [INPUT Name:inputMaskImagePath Type:string DisplayName:'Input Mask']
# [INPUT Name:threshold Type:int DisplayName:'Masking Threshold' Default:128 Min:0 Max:65535]
# [OUTPUT Name:resultPath Type:string DisplayName:'Masked Image']
def run(params):
    image_location = params['inputImagePath']
    mask_location = params['inputMaskImagePath']
    result_location = params['resultPath']
    threshold = int(params['threshold'])
    if not os.path.exists(image_location):
        print(f'Error: {image_location} does not exist')
        return;
        
    image_data = imread(image_location)
    mask_data = imread(mask_location)
    output_data = np.empty_like(image_data)
    output_data = np.where(mask_data<threshold, image_data, 0)
    output_data = output_data.astype(image_data.dtype)
    imsave(result_location, output_data)


if __name__ == '__main__':
    params = {}
    params['inputImagePath'] = 'test.png'
    params['inputMaskImagePath'] = 'test.png'
    params['resultPath'] = 'testResult.png'
    params['threshold'] = 128
    
    run(params)

