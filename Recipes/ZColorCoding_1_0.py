import time

from matplotlib import cm
from collections import OrderedDict
import numpy as np
from skimage.io import imread, imsave

'''
Uses matplotlib colormaps to retrieve colors used to create color gradients applied to individual Z planes in a 3D image.
Can be used with timepoints too, but is not adapted to 4D/5D images.

Requirements
------------
numpy (comes with Aivia installer)
scikit-image (comes with Aivia installer)
matlplotlib (comes with Aivia installer)

Parameters
----------
- Input channel
- Colormap choice is hardcoded below (with index from 0 to 4)

Returns
----------
- 3 new channels for Red, Green and Blue information for proper color-code

Usage
----------
* In Aivia: modify code to select a colormap, drag & drop .py file, select input channel and press "Start"
* In python: modify code to select a colormap and modify parameters at the end of code. Run the .py file.
'''

cmaps = ['viridis', 'plasma', 'inferno', 'magma', 'cividis']
selected_map = cmaps[2]


# [INPUT Name:inputImagePath Type:string DisplayName:'Input Image']
# [OUTPUT Name:resultPathBlue Type:string DisplayName:'Z Coloring - Blue']
# [OUTPUT Name:resultPathGreen Type:string DisplayName:'Z Coloring - Green']
# [OUTPUT Name:resultPathRed Type:string DisplayName:'Z Coloring - Red']
def run(params):
    image_location = params['inputImagePath']
    result_location_red = params['resultPathRed']
    result_location_green = params['resultPathGreen']
    result_location_blue = params['resultPathBlue']
    # Extra parameters when dataset is 2D+extra dimensions
    tCount = int(params['TCount'])
    zCount = int(params['ZCount'])

    if tCount == 1 and zCount == 1:
        print(f'Error: image has no Z or T dimension detected.')
        return;

    image_data = imread(image_location)
    input_dims = np.asarray(image_data.shape)
    print('-- Input dimensions (expected Z, Y, X or T, Z, Y, X): ', input_dims, ' --')

    output_dims = np.insert(input_dims, 0, 3)
    output_data = np.zeros(output_dims).astype(image_data.dtype)

    # Get discrete values from colormap and apply
    final_color_map = cm.get_cmap(selected_map, zCount)

    if tCount == 1 or zCount == 1:
        print('-- processing 3D dataset --')
        for z in range(input_dims[0]):
            # Collect color map for precise z-slice
            current_col = final_color_map.colors[z, :3]

            for c in range(3):
                output_data[c, z, :, :] = image_data[z, :, :] * current_col[c]

    # T and Z > 1
    else:
        print('-- processing 4D dataset --')
        for z in range(input_dims[1]):
            # Collect color map for precise z-slice
            current_col = final_color_map.colors[z, :3]

            for t in range(input_dims[0]):
                # print('Time: ', time.ctime(time.time()), ' T: ', t, ' Z: ', z)
                for c in range(3):
                    output_data[c, t, z, :, :] = image_data[t, z, :, :] * current_col[c]

    imsave(result_location_red, output_data[0])
    imsave(result_location_green, output_data[1])
    imsave(result_location_blue, output_data[2])


if __name__ == '__main__':
    params = {'inputImagePath':
                  'D:\\AIVIA working directory\\_Tests\\neuronimage_Crop_ML_resized_9.0_3D-TL.aivia.tif'
        , 'resultPathRed':
                  'D:\\AIVIA working directory\\_Tests\\neuronimage_Crop_ML_resized_9.0.aivia-R.tif'
        , 'resultPathGreen':
                  'D:\\AIVIA working directory\\_Tests\\neuronimage_Crop_ML_resized_9.0.aivia-G.tif'
        , 'resultPathBlue':
                  'D:\\AIVIA working directory\\_Tests\\neuronimage_Crop_ML_resized_9.0.aivia-B.tif'
        , 'TCount': '3', 'ZCount': '100'}

    run(params)