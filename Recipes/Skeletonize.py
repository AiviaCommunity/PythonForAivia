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
    if not os.path.exists(image_location):
        print(f'Error: {image_location} does not exist')
        return;
        
    image_data = imread(image_location)
    
    temp_array = np.empty_like(image_data)
    output_data = np.empty_like(image_data)
    
    # 1. Apply a mask given the input threshold
    temp_array = np.where(image_data>threshold, 1, 0)
    
    # 2. Skeletonize using default methods
    if len(image_data.shape) == 2:
        temp_array = skeletonize(temp_array)
    else:
        temp_array = skeletonize_3d(temp_array)
    
    # 3. Apply a closing if user inputs radius > 0
    if radius != 0:
        if len(image_data.shape) == 2:
            structure = disk(radius)
        else:
            structure = ball(radius)
        temp_array = closing(temp_array, selem=structure)
        
    # 4. Put back into appropriate range for the bit depth
    temp_array = np.where(temp_array.astype(image_data.dtype)>0, image_data.max(), 0)
    
    # 5. Finally assign the output
    output_data = temp_array.astype(image_data.dtype)
    imsave(result_location, output_data)


if __name__ == '__main__':
    params = {}
    params['inputImagePath'] = 'test.png'
    params['resultPath'] = 'testResult.png'
    params['threshold'] = 128
    params['radius'] = 0
    
    run(params)

# TODO: test skimage.morphology.medial_axis instead of skeletonize

# CHANGELOG
# v1.00 TL - Original script by Trevor Lancon (trevorl@drvtechnologies.com)
# v1.01 TL - Removed unused skimage.exposure.rescale_intensity import