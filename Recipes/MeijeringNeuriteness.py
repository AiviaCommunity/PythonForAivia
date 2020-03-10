import os.path
import numpy as np
from skimage.io import imread, imsave
from skimage.filters import meijering
from skimage.exposure import rescale_intensity

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
"""

print('Imports complete')

# [INPUT Name:inputImagePath Type:string DisplayName:'Input Image']
# [INPUT Name:sigma_min Type:double DisplayName:'Min Sigma' Default:0.5 Min:0.0 Max:25.0]
# [INPUT Name:sigma_max Type:double DisplayName:'Max Sigma' Default:1.5 Min:0.0 Max:25.0]
# [OUTPUT Name:resultPath Type:string DisplayName:'Neuriteness']
def run(params):
    image_location = params['inputImagePath']
    result_location = params['resultPath']
    sigma_min = float(params['sigma_min'])
    sigma_max = float(params['sigma_max'])
    
    print('inputs defined')
    
    if not os.path.exists(image_location):
        print(f'Error: {image_location} does not exist')
        return;
        
    image_data = imread(image_location)
    
    output_data = np.empty_like(image_data)
    
    print('arrays set up')
    
    # Tried to allow user to input another double to represent the increment of
    # sigma scales, but it broke everything. Here I replace that with an
    # automatic increment to go from minimum to maximum sigma with 5 steps
    sigmas = np.arange(sigma_min, sigma_max, round((sigma_max-sigma_min)/5,1))
    
    meijering_image = meijering(image_data, sigmas=sigmas, black_ridges=False)
    
    # Four corners of Meijering image are pure white and throw off the histogram
    # Erase them based on the max of 1% of the image size or 4, whichever is more
    crop_size = max(int(max(list(image_data.shape))/100),4)
    meijering_image[0:crop_size, 0:crop_size] = 0
    meijering_image[0:crop_size, -crop_size:] = 0
    meijering_image[-crop_size:, 0:crop_size] = 0
    meijering_image[-crop_size:, -crop_size:] = 0
    
    output_data = rescale_intensity(meijering_image, out_range='uint8').astype(image_data.dtype)

    imsave(result_location, output_data)


if __name__ == '__main__':
    params = {}
    params['inputImagePath'] = 'test.png'
    params['resultPath'] = 'testResult.png'
    params['sigma_min'] = 0.5
    params['sigma_max'] = 1.5
    
    run(params)

# CHANGELOG
# v1.00 TL - Original script by Trevor Lancon (trevorl@drvtechnologies.com)
#