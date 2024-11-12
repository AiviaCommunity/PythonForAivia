import os.path
import numpy as np
from skimage.io import imread, imsave
from skimage.exposure import rescale_intensity
from scipy.ndimage import distance_transform_edt, label
from skimage.segmentation import watershed
from skimage.feature import peak_local_max
from skimage.filters import gaussian


# FIXED PARAMETERS
gauss_sigma = 3


"""
Simple watershed.

Requirements
------------
numpy (comes with Aivia installer)
scikit-image (comes with Aivia installer)
ctypes

Parameters
----------
Input channel:
    Input channel to be transformed. Prefer a binary mask.

Returns
-------
Channel in Aivia
"""


# [INPUT Name:inputImagePath Type:string DisplayName:'Binary Mask']
# [OUTPUT Name:resultPath Type:string DisplayName:'Watershed Result']
def run(params):
    image_location = params['inputImagePath']
    result_location = params['resultPath']
    zCount = int(params['ZCount'])
    tCount = int(params['TCount'])
    if not os.path.exists(image_location):
        print(f"Error: {image_location} does not exist")
        return

    image_data = imread(image_location)
    dims = image_data.shape
    img_dtype = image_data.dtype
    print('-- Input dimensions (expected (T,) (Z,) Y, X): ', np.asarray(dims), ' --')

    # Check if max is the max of the bit depth (otherwise invert function won't work)
    img_max = np.max(image_data)
    if np.iinfo(img_dtype).max != img_max:
        print('Image max found: ', img_max, '\nAdjusting max to the max of the bit depth.')
        image_data = rescale_intensity(image_data, in_range=(0, img_max), out_range=(0, np.iinfo(img_dtype).max))
        image_data = image_data.astype(img_dtype)

    # Distance transform with default options
    distance_map = distance_transform_edt(image_data)

    # Blur to smooth map
    blurred_distance = gaussian(distance_map, sigma=gauss_sigma)
    
    # Find local maximas
    max_coords = peak_local_max(blurred_distance, exclude_border=0)     # , footprint=np.ones((3, 3))
    local_maxima = np.zeros_like(image_data, dtype=bool)
    local_maxima[tuple(max_coords.T)] = True
    markers = label(local_maxima)[0]

    # Watershed operation
    watershed_map = watershed(-blurred_distance, markers, mask=image_data, watershed_line=True, connectivity=2)

    # Labeled mask to binary
    output_data = np.where(watershed_map > 0, img_max, 0).astype(img_dtype)

    imsave(result_location, output_data)


if __name__ == '__main__':
    params = {'inputImagePath': r'D:\PythonCode\_tests\XY_378x255_1ch_8bit_binarymask_nucleus_APP-nuc-separation_A14.0.aivia.tif',
              'resultPath': r'D:\PythonCode\_tests\_test_result.tif',
              'ZCount': 1, 'TCount': 1}

    run(params)
