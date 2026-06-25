import os.path
import numpy as np
from tifffile import imread, imsave
from skimage.exposure import equalize_hist, equalize_adapthist, cumulative_distribution, rescale_intensity
from skimage.util import img_as_ubyte, img_as_uint
import ctypes


processing_options = {1: 'Use Quantile',
                      2: 'CLAHE (Contrast Limited Adaptive Histogram Equalization)',
                      3: 'Equalize histogram'}
selected_processing = 2
parameters = {'min_val': 0.2, 'max_val': 1.0, 'k_size_val': (1, 500, 500)}

"""
Process a single channel image to auto-adjust intensities.
Some intensities can be saturated depending on the default quantile setting.

Requirements
------------
numpy (comes with Aivia installer)
scikit-image (comes with Aivia installer)
tifffile (installed with scikit-image)

Parameters
----------
Input Image : Aivia channel
    Input channel to use for the processing.

Returns
-------
Aivia image
    Adjusted channel.
"""


def process_img(img_array, process_no, param_d: dict):
    in_dtype = img_array.dtype
    proc_data = np.empty_like(img_array)

    if process_no == 1:         # Quantile and Cumulative Distribution
        q_min = np.percentile(img_array, int(param_d['min_val'] * 100))
        q_max = np.percentile(img_array, int(param_d['max_val'] * 100))

        proc_data = rescale_intensity(img_array, in_range=(q_min, q_max), out_range='dtype')
        print(f"Processed image using Quantiles (min = {param_d['min_val']}, max = {param_d['max_val']})")

    elif process_no == 2:  # CLAHE
        # Define kernel size for local evaluation. Default is a 1/8 of the image size
        k_size_min = 100
        k_size = tuple(min(img_array.shape[d], k_size_min) // 8 for d in range(img_array.ndim))
        if 'k_size_val' in param_d.keys():
            if param_d['k_size_val']:
                k_size = param_d['k_size_val']
        print(f'CLAHE kernel size is: {k_size}')

        # Normalize image (0-1)
        img_array = (img_array - img_array.min()) / (img_array.max() - img_array.min())
        
        proc_data_tmp = equalize_adapthist(img_array, kernel_size=k_size)
        if str(in_dtype) == 'uint16':
            proc_data = img_as_uint(proc_data_tmp)
        else:
            proc_data = img_as_ubyte(proc_data_tmp)

        print(f"Processed image with CLAHE (Contrast Limited Adaptive Histogram Equalization) with a kernel size of {k_size}")

    elif process_no == 3:         # Equalize
        proc_data_tmp = equalize_hist(img_array)
        if str(in_dtype) == 'uint16':
            proc_data = img_as_uint(proc_data_tmp)
        else:
            proc_data = img_as_ubyte(proc_data_tmp)
        print(f'Processed image with histogram equalization')

    return proc_data
    

# [INPUT Name:inputImagePath Type:string DisplayName:'Input Channel']
# [OUTPUT Name:resultImagePath Type:string DisplayName:'AutoAdjusted Channel']
def run(params):
    image_location = params['inputImagePath']
    result_location = params['resultImagePath']
    
    tCount = int(params['TCount'])
    zCount = int(params['ZCount'])
    
    if not os.path.exists(image_location):
        print(f'Error: {image_location} does not exist')
        return
        
    image_data = imread(image_location)
    dims = image_data.shape
    
    processed = np.empty_like(image_data)
    if zCount == 1:
        parameters['k_size_val'] = parameters['k_size_val'][1:]

    # 2D+T
    if tCount > 1 and zCount == 1:
        print(f"Applying to 2D+T case with dims: {image_data.shape}")
        for t in range(0, dims[0]):
            if dims[0] == tCount:
                processed[t, :, :] = process_img(image_data[t, :, :], selected_processing, parameters).astype(image_data.dtype)
                axes = 'YXT'  # Format from tifffile
            else:
                processed[:, :, t] = process_img(image_data[:, :, t], selected_processing, parameters).astype(image_data.dtype)
                axes = 'TYX'
                print('Processing an unconventional timelapse with YXT dimensions')

    # 3D+T
    if tCount > 1 and zCount > 1:
        print(f"Applying to 3D+T case with dims: {dims}")
        for t in range(0, dims[0]):
            processed[t, :, :, :] = process_img(image_data[t, :, :, :], selected_processing, parameters).astype(image_data.dtype)
            axes = 'TZYX'  # Format from tifffile

    # 2D
    elif tCount == 1:
        if zCount == 1:
            axes = 'YX'
            print(f"Applying to 2D case with dims: {image_data.shape}")
            processed = process_img(image_data, selected_processing, parameters).astype(image_data.dtype)
        
        # 3D
        else:
            axes = 'ZYX'
            print(f"Applying to 3D case with dims: {image_data.shape}")
            processed = process_img(image_data, selected_processing, parameters).astype(image_data.dtype)

    # Reporting
    max_val = np.iinfo(image_data.dtype).max
    print(f'Number of saturated pixels before processing: {np.sum(image_data == max_val)}\n'
          f'Number of saturated pixels after processing: {np.sum(processed == max_val)}')

    imsave(result_location, processed, metadata={'axes': axes})


def Mbox(title, text):
    return ctypes.windll.user32.MessageBoxW(0, text, title, 0)


if __name__ == '__main__':
    params = {'inputImagePath': r'',
              'resultImagePath': r'',
              'TCount': 1, 'ZCount': 1
    }
    run(params)

# CHANGELOG
#   v1_00: - From Threshold_for_3DObjects.py
