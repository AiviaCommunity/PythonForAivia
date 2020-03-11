import os.path
import numpy as np
from skimage.io import imread, imsave
from skimage.morphology import skeletonize, skeletonize_3d
from skimage.morphology import closing, disk, ball

np.seterr(divide='ignore', invalid='ignore')

"""
See: https://scikit-image.org/docs/dev/api/skimage.morphology.html#skimage.morphology.skeletonize
and https://scikit-image.org/docs/dev/api/skimage.morphology.html#skimage.morphology.skeletonize_3d

Computes a skeleton of the input image based on the thinning of its binarization:

 1. The image is binarized (thresholded) based on the user's "Threshold" input
 2. The binarized image is thinned according to the methodology explained in
    the linked documentation
 3. (Optional) The skeleton image is closed based on the radius provided by the user.
    If the "Radius" is 0, no closing is performed.
 4. The skeleton is converted to the bit space from the original image.

Requirements
------------
numpy
scikit-image

Parameters
----------
Input Image : Aivia channel
    Input channel to use for the transform.

Threshold : int
    Grayvalue above which to mask.

Closing Radius : int
    Size of kernel used to "fill in" concavities or connect close ends of the skeleton.

Returns
-------
Aivia channel
    Result of the transform
"""

# [INPUT Name:inputImagePath Type:string DisplayName:'Input Image']
# [INPUT Name:threshold Type:int DisplayName:'Threshold' Default:128 Min:0 Max:65535]
# [INPUT Name:radius Type:int DisplayName:'Closing Radius' Default:0 Min:0 Max:100]
# [OUTPUT Name:resultPath Type:string DisplayName:'Skeleton']
def run(params):
    image_location = params['inputImagePath']
    result_location = params['resultPath']
    threshold = int(params['threshold'])
    radius = int(params['radius'])
    tCount = int(params['TCount'])
    zCount = int(params['ZCount'])
    if not os.path.exists(image_location):
        print(f'Error: {image_location} does not exist')
        return;
        
    image_data = imread(image_location)
    dims = image_data.shape
    temp_array = np.empty_like(image_data)
    output_data = np.empty_like(image_data)
    
    temp_array = np.where(image_data>threshold, 1, 0)

    if radius != 0:
        if zCount > 1:
            structure = ball(radius)
        else:
            structure = disk(radius)
    
    # 3D+T
    if tCount > 1 and zCount > 1:
        for t in range(0, dims[0]):
            temp_array[t, :, :, :] = skeletonize_3d(temp_array[t, :, :, :])
            if radius != 0:
                temp_array[t, :, :, :] = closing(temp_array[t, :, :, :], selem=structure)
    # 2D+T
    elif tCount > 1 and zCount == 1:
        for t in range(0, dims[0]):
            temp_array[t, :, :] = skeletonize(temp_array[t, :, :])
            if radius != 0:
                temp_array[t, :, :] = closing(temp_array[t, :, :], selem=structure)
    # 3D
    elif tCount ==1 and zCount > 1:
        temp_array = skeletonize_3d(temp_array)
        if radius != 0:
            temp_array = closing(temp_array, selem=structure)
    # 2D
    else:
        temp_array = skeletonize(temp_array)
        if radius != 0:
            temp_array = closing(temp_array, selem=structure)


    temp_array = np.where(temp_array.astype(image_data.dtype)>0, image_data.max(), 0)
    
    output_data = temp_array.astype(image_data.dtype)
    imsave(result_location, output_data)


if __name__ == '__main__':
    params = {}
    params['inputImagePath'] = 'test.png'
    params['resultPath'] = 'testResult.png'
    params['threshold'] = 128
    params['radius'] = 0
    
    run(params)
