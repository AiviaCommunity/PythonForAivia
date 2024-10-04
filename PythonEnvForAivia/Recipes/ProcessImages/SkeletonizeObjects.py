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
 5. The skeleton is passed to Aivia's mesh creation engine to output the result as a mesh.
 
Requirements
------------
numpy (comes with Aivia installer)
scikit-image (comes with Aivia installer)

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
Aivia objects
    Result of the transform
"""

# [INPUT Name:inputImagePath Type:string DisplayName:'Input Image']
# [INPUT Name:threshold Type:int DisplayName:'Threshold' Default:128 Min:0 Max:65535]
# [INPUT Name:radius Type:int DisplayName:'Closing Radius' Default:0 Min:0 Max:100]
# [OUTPUT Name:resultImagePath Type:string DisplayName:'Skeleton Image']
# [OUTPUT Name:resultObjectPath Type:string DisplayName:'Skeleton Objects' Objects:3D MinSize:0.0 MaxSize:1000000000.0]
def run(params):
    image_location = params['inputImagePath']
    result_image_location = params['resultImagePath']
    result_object_location = params['resultObjectPath']
    threshold = int(params['threshold'])
    radius = int(params['radius'])
    tCount = int(params['TCount'])
    zCount = int(params['ZCount'])
    if not os.path.exists(image_location):
        print(f'Error: {image_location} does not exist')
        return;
        
    if zCount == 1:
        print('Mesh creation for skeletons is currently only supported in 3D.')
        print('Try using Skeletonize.py instead.')
        return
    
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
                temp_array[t, :, :, :] = closing(temp_array[t, :, :, :], footprint=structure)
    # 2D+T
    elif tCount > 1 and zCount == 1:
        for t in range(0, dims[0]):
            temp_array[t, :, :] = skeletonize(temp_array[t, :, :])
            if radius != 0:
                temp_array[t, :, :] = closing(temp_array[t, :, :], footprint=structure)
    # 3D
    elif tCount ==1 and zCount > 1:
        temp_array = skeletonize_3d(temp_array)
        if radius != 0:
            temp_array = closing(temp_array, footprint=structure)
    # 2D
    else:
        temp_array = skeletonize(temp_array)
        if radius != 0:
            temp_array = closing(temp_array, footprint=structure)


    temp_array = np.where(temp_array.astype(image_data.dtype)>0, image_data.max(), 0)
    
    output_data = temp_array.astype(image_data.dtype)
    imsave(result_image_location, output_data)
    imsave(result_object_location, output_data)


if __name__ == '__main__':
    params = {}
    params['inputImagePath'] = 'test.png'
    params['resultImagePath'] = 'testResult.png'
    params['resultObjectPath'] = 'testResult.png'
    params['threshold'] = 128
    params['radius'] = 0
    
    run(params)
