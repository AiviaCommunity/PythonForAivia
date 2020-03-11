import os.path
import numpy as np
from skimage.io import imread, imsave
from skimage.morphology import closing, opening
from skimage.morphology import disk, ball
from skimage.util import img_as_uint, img_as_ubyte

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

Requirements
------------
numpy
scikit-image

Parameters
----------
Input Image : Aivia channel
    Input channel to use for the transform.

Size : double
    Size of the disk or ball morphological kernel in pixels.

Returns
-------
Aivia channel
    Result of the transform
"""

# [INPUT Name:inputImagePath Type:string DisplayName:'Input Image']
# [INPUT Name:size Type:int DisplayName:'Size (px)' Default:3 Min:0 Max:100]
# [OUTPUT Name:resultPath Type:string DisplayName:'Texture']
def run(params):
    image_location = params['inputImagePath']
    result_location = params['resultPath']
    size = int(params['size'])
    tCount = int(params['TCount'])
    zCount = int(params['ZCount'])
    if not os.path.exists(image_location):
        print(f'Error: {image_location} does not exist')
        return;
        
    image_data = imread(image_location)
    texture_image = np.empty_like(image_data)
    output_data = np.empty_like(image_data)
    
    print(f"z {zCount} t {tCount} shape {image_data.shape}")
    
    if zCount == 1:
        structure = disk(size)
    else:
        structure = ball(size)

    if tCount > 1 and zCount > 1:
        for t in range(0, image_data.shape[0]):
            texture_image[t,:,:,:] = closing(
                image_data[t,:,:,:], selem=structure) - opening(image_data[t,:,:,:], selem=structure
            )
    elif tCount > 1 and zCount == 1:
        for t in range(0, image_data.shape[0]):
            texture_image[t,:,:] = closing(
                image_data[t,:,:], selem=structure) - opening(image_data[t,:,:], selem=structure
            )
    else:
        texture_image = closing(image_data, selem=structure) - opening(image_data, selem=structure)
    
    if image_data.dtype == np.uint16:
        output_data = img_as_uint(texture_image)
    else:
        output_data = img_as_ubyte(texture_image)
    
    imsave(result_location, output_data)


if __name__ == '__main__':
    params = {}
    params['inputImagePath'] = 'test.png'
    params['resultPath'] = 'testResult.png'
    params['size'] = 3
    
    run(params)
