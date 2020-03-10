import os.path
import numpy as np
from skimage.io import imread, imsave
from skimage.feature import shape_index
from skimage.exposure import rescale_intensity

np.seterr(divide='ignore', invalid='ignore')

"""
See: https://scikit-image.org/docs/dev/api/skimage.feature.html#skimage.feature.shape_index

Computes the shape index as derived from the eigenvalues of the Hessian
and returns it as a new channel scaled to 8bit space.

Different values indicate convexity/concavitiy and shapes:
 - cups / caps
 - troughs / domes
 - ruts / ridges
 - saddle ruts / saddle ridges
 - saddles
 
In Aivia, this is useful as a way to compute an extra channel to use for
training a pixel classifier.

For more information, see Koenderink & van Doorn as linked in the skimage documentation.
"""

# [INPUT Name:inputImagePath Type:string DisplayName:'Input Image']
# [INPUT Name:sigma Type:double DisplayName:'Gaussian Sigma' Default:3.0 Min:0.0 Max:50.0]
# [OUTPUT Name:resultPath Type:string DisplayName:'Shape Index']
def run(params):
    image_location = params['inputImagePath']
    result_location = params['resultPath']
    sigma = float(params['sigma'])
    if not os.path.exists(image_location):
        print(f'Error: {image_location} does not exist')
        return;
        
    image_data = imread(image_location)
    output_data = np.empty_like(image_data)
    shape_image = np.empty(image_data.shape)
    
    # Returns -1:1 floats describing the shape index
    if len(image_data.shape) == 2:
        shape_image = shape_index(image_data, sigma=sigma, mode='reflect')
    else:
        for i in np.arange(0, int(image_data.shape[0])):
            shape_image[i,:,:] = shape_index(image_data[i,:,:], sigma=sigma, mode='reflect')
    
    # NaNs are usually returned - convert these to possible pixel values
    shape_image = np.nan_to_num(shape_image)
    
    # Need to rescale this shape index image to make sense in 8bit space
    output_data = rescale_intensity(shape_image, out_range='uint8').astype(image_data.dtype)

    imsave(result_location, output_data)


if __name__ == '__main__':
    params = {}
    params['inputImagePath'] = 'test.png'
    params['resultPath'] = 'testResult.png'
    params['sigma'] = 3.0;
    
    run(params)

# CHANGELOG
# v1.00 TL - Original script by Trevor Lancon (trevorl@drvtechnologies.com)
#