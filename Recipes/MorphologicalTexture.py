import os.path
import numpy as np
from skimage.io import imread, imsave
from skimage.morphology import closing, opening
from skimage.morphology import disk, ball
from skimage.exposure import rescale_intensity

np.seterr(divide='ignore', invalid='ignore')

"""
See: https://scikit-image.org/docs/dev/api/skimage.filters.html#skimage.filters.meijering

Estimates image texure using morphological transforms.

Closing and opening operations are performed in parallel. A disk kernel
is used for 2D images, and a ball kernel is used for 3D images. The user
defines the size of these kernels.

The closing returns the max value within that neighborhood for every
voxel, resulting in a brighter image.

The opening returns the min value within that neighborhood for every
voxel, resulting in a darker image.

The opening result is then subtracted from the closing result to create
the final output.
"""

# [INPUT Name:inputImagePath Type:string DisplayName:'Input Image']
# [INPUT Name:size Type:int DisplayName:'Size (px)' Default:3 Min:0 Max:100]
# [OUTPUT Name:resultPath Type:string DisplayName:'Texture']
def run(params):
    image_location = params['inputImagePath']
    result_location = params['resultPath']
    size = int(params['size'])
    if not os.path.exists(image_location):
        print(f'Error: {image_location} does not exist')
        return;
        
    image_data = imread(image_location)
    
    output_data = np.empty_like(image_data)
    
    if len(image_data.shape) == 2:
        structure = disk(size)
    else:
        structure = ball(size)

    output_data = closing(image_data, selem=structure) - opening(image_data, selem=structure)
        
    output_data = rescale_intensity(output_data, out_range='uint8').astype(image_data.dtype)
    
    imsave(result_location, output_data)


if __name__ == '__main__':
    params = {}
    params['inputImagePath'] = 'test.png'
    params['resultPath'] = 'testResult.png'
    params['size'] = 3
    
    run(params)


# CHANGELOG
# v1.00 TL - Original script by Trevor Lancon (trevorl@drvtechnologies.com)
#