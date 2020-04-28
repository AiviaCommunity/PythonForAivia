import os.path
import numpy as np
from tifffile import imread, imsave
from skimage.feature import shape_index
from skimage.util import img_as_ubyte, img_as_uint

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

Requirements
------------
numpy
scikit-image

Parameters
----------
Input Image : Aivia channel
    Input channel to use for the transform.

Gaussian Sigma : double
    Gaussian smoothing size to use to determine local shape.

Returns
-------
Aivia channel
    Result of the transform normalized to 8bit or 16bit space according to the input.
"""

# [INPUT Name:inputImagePath Type:string DisplayName:'Input Image']
# [INPUT Name:sigma Type:double DisplayName:'Gaussian Sigma' Default:3.0 Min:0.0 Max:50.0]
# [OUTPUT Name:resultPath Type:string DisplayName:'Shape Index']
def run(params):
    image_location = params['inputImagePath']
    result_location = params['resultPath']
    sigma = float(params['sigma'])
    tCount = int(params['TCount'])
    zCount = int(params['ZCount'])
    if not os.path.exists(image_location):
        print(f"Error: {image_location} does not exist")
        return;
        
    image_data = imread(image_location)
    dims = image_data.shape
    shape_image = np.empty(image_data.shape, dtype=np.float32)
    
    # 3D+T
    if tCount > 1 and zCount > 1:
        print(f"Applying to 3D+T case with dims: {image_data.shape}")
        for t in range(0, dims[0]):
            for z in range(0, dims[1]):
                shape_image[t,z,:,:] = shape_index(image_data[t,z,:,:], sigma=sigma, mode='reflect').astype(np.float32)
        axes = 'YXZT'
    # 2D+T or 3D
    elif (tCount > 1 and zCount == 1) or (tCount == 1 and zCount > 1):
        print(f"Applying to 2D+T or 3D case with dims: {image_data.shape}")
        for d in range(0, dims[0]):
            shape_image[d,:,:] = shape_index(image_data[d,:,:], sigma=sigma, mode='reflect').astype(np.float32)
        if tCount > 1:
            axes = 'YXT'
        else:
            axes = 'YXZ'
    # 2D
    else:
        print(f"Applying to 2D case with dims: {image_data.shape}")
        shape_image = shape_index(image_data, sigma=sigma, mode='reflect')
        axes = 'YX'
    
    # NaNs are usually returned - convert these to possible pixel values
    shape_image = np.nan_to_num(shape_image)
    
    if image_data.dtype == np.uint16:
        shape_image = img_as_uint(shape_image)
    else:
        shape_image = img_as_ubyte(shape_image)

    imsave(result_location, shape_image, metadata={'axes': axes})


if __name__ == '__main__':
    params = {}
    params['inputImagePath'] = 'test.png'
    params['resultPath'] = 'testResult.png'
    params['sigma'] = 3.0;
    
    run(params)
