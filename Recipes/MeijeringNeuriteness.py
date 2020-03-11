import os.path
import numpy as np
from skimage.io import imread, imsave
from skimage.filters import meijering
from skimage.util import img_as_uint, img_as_ubyte

np.seterr(divide='ignore', invalid='ignore')

"""
See: https://scikit-image.org/docs/dev/api/skimage.filters.html#skimage.filters.meijering

Finds and enhances bright ridges within the image that are within a reasonable
range of the size given by the user. Returns a max projection through scale space
for 5 evenly-spaced Gaussian sigmas.

Because np.arange() is used to contruct the array of sigma values, the largest
sigma is excluded.
https://docs.scipy.org/doc/numpy/reference/generated/numpy.arange.html

For example, if the user specifies min and max sigmas of 0.1 and 0.6, respectively,
the transform is performed for Gaussian sigma values of 0.1, 0.2, 0.3, 0.4, 0.5.
The maximum values from all of the transforms is output at every voxel.

Requirements
------------
numpy
scikit-image

Parameters
----------
Input Image : Aivia channel
    Input channel to use for the transform.

Min Sigma : double
    Mininim kernel size for Gaussian smoothing.

Max Sigma : double
    Maximum kernel size for Gaussian smoothing.

Returns
-------
Aivia channel
    Result of the transform
"""

# [INPUT Name:inputImagePath Type:string DisplayName:'Input Image']
# [INPUT Name:sigma_min Type:double DisplayName:'Min Sigma' Default:0.5 Min:0.0 Max:25.0]
# [INPUT Name:sigma_max Type:double DisplayName:'Max Sigma' Default:1.5 Min:0.0 Max:25.0]
# [OUTPUT Name:resultPath Type:string DisplayName:'Neuriteness']
def run(params):
    image_location = params['inputImagePath']
    result_location = params['resultPath']
    sigma_min = float(params['sigma_min'])
    sigma_max = float(params['sigma_max'])
    tCount = int(params['TCount'])
    zCount = int(params['ZCount'])
    
    if not os.path.exists(image_location):
        print(f'Error: {image_location} does not exist')
        return;
        
    image_data = imread(image_location)
    dims = image_data.shape
    meijering_image = np.empty_like(image_data)
    output_data = np.empty_like(image_data)
    
    sigmas = np.arange(sigma_min, sigma_max, round((sigma_max-sigma_min)/5, 1))
    
    if tCount > 1:
        print('Time series are currently not supported.')
        return
            
    meijering_image = meijering(image_data, sigmas=sigmas, black_ridges=False)
    
    # Cropping is performed in 2D to get rid of bright pixels at edges of the image.
    
    if zCount > 1:
        crop_size = max(int(max(list(dims[1:]))/100), 4)
        meijering_image[:, 0:crop_size, 0:crop_size] = 0
        meijering_image[: ,0:crop_size, -crop_size:] = 0
        meijering_image[: ,-crop_size:, 0:crop_size] = 0
        meijering_image[: ,-crop_size:, -crop_size:] = 0
    else:
        crop_size = max(int(max(list(dims))/100), 4)
        meijering_image[0:crop_size, 0:crop_size] = 0
        meijering_image[0:crop_size, -crop_size:] = 0
        meijering_image[-crop_size:, 0:crop_size] = 0
        meijering_image[-crop_size:, -crop_size:] = 0
    
    if image_data.dtype == np.uint16:
        output_data = img_as_uint(meijering_image)
    else:
        output_data = img_as_ubyte(meijering_image)

    imsave(result_location, output_data)


if __name__ == '__main__':
    params = {}
    params['inputImagePath'] = 'test.png'
    params['resultPath'] = 'testResult.png'
    params['sigma_min'] = 0.5
    params['sigma_max'] = 1.5
    
    run(params)
