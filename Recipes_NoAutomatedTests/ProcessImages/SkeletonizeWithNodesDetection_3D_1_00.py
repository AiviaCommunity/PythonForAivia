import os.path
import numpy as np
from skimage.io import imread, imsave
from skimage.morphology import skeletonize, skeletonize_3d, binary_dilation
from skimage.morphology import closing, opening, disk, ball, square, cube
from skimage.filters import gaussian, median
from scipy.ndimage import label
import math
from datetime import datetime

np.seterr(divide='ignore', invalid='ignore')

skeleton_dilation_size = 2
node_dilation_size = 4

"""
See: https://scikit-image.org/docs/dev/api/skimage.morphology.html#skimage.morphology.skeletonize
and https://scikit-image.org/docs/dev/api/skimage.morphology.html#skimage.morphology.skeletonize_3d

Computes a skeleton of the input image based on the thinning of its binarization (user threshold).
Open or close filters can be used to process the skeleton.
Then branching nodes are detected and dilated to be subtracted to the dilated skeleton, thus giving
branches with some thickness for Aivia to pick them as objects.

Requirements
------------
numpy (comes with Aivia installer)
scikit-image (comes with Aivia installer)

Parameters
----------
Input Image : Aivia channel
    Input channel to use for the transform.

Threshold : int
    Grayvalue above which to mask.

Closing Radius : int (negative value for opening)
    Size of kernel used to "fill in" concavities or connect close ends of the skeleton.

Returns
-------
Aivia channel
    Result of the transform
    
# [OUTPUT Name:resultPath3 Type:string DisplayName:'Branches']
"""

# [INPUT Name:inputImagePath Type:string DisplayName:'Input Image']
# [INPUT Name:closeRadius Type:int DisplayName:'Skeleton Closing Radius (<0 for Opening)' Default:0 Min:0 Max:100]
# [INPUT Name:filterRadius Type:int DisplayName:'Binary Mask Filter Radius' Default:0 Min:0 Max:100]
# [INPUT Name:filterType Type:int DisplayName:'Median or Gaussian Filter' Default:0 Min:0 Max:100]
# [INPUT Name:threshold Type:int DisplayName:'Threshold' Default:128 Min:0 Max:65535]
# [OUTPUT Name:resultPath3 Type:string DisplayName:'Branches']
# [OUTPUT Name:resultPath2 Type:string DisplayName:'Branching points']
# [OUTPUT Name:resultPath Type:string DisplayName:'Skeleton']
def run(params):
    image_location = params['inputImagePath']
    skeleton_p = params['resultPath']
    nodes_map_p = params['resultPath2']
    branches_map_p = params['resultPath3']
    threshold = int(params['threshold'])

    close_radius = int(params['closeRadius'])
    open_skeleton = False
    if close_radius < 0:
        close_radius = -close_radius
        open_skeleton = True

    filter_radius = int(params['filterRadius'])
    filter_type = int(params['filterType'])

    tCount = int(params['TCount'])
    zCount = int(params['ZCount'])
    pixel_cal_tmp = params['Calibration']
    pixel_cal = pixel_cal_tmp[6:].split(', ')           # Expects calibration with 'XYZT: ' in front

    # Calculating ratio between XY and Z                # Expecting only 'Micrometers' in this code
    # XY_cal = float(pixel_cal[0].split(' ')[0])
    # Z_cal = float(pixel_cal[2].split(' ')[0])
    # zratio = round(Z_cal / XY_cal)

    if not os.path.exists(image_location):
        print(f'Error: {image_location} does not exist')
        return
        
    image_data = imread(image_location)
    dims = image_data.shape
    print('-- Input dimensions (expected (T), Z, Y, X): ', np.asarray(dims), ' --')
    bitdepth_max = np.iinfo(image_data.dtype).max
    temp_array = np.empty_like(image_data)
    output_data = np.empty_like(image_data)
    
    thr_array = np.where(image_data > threshold, 1, 0).astype(image_data.dtype)

    # Filter binary mask to smooth skeleton
    if filter_radius > 0 and filter_type == 1:
        filtered_array = gaussian(thr_array, sigma=filter_radius, preserve_range=True)

        # Calculate gaussian filter threshold with x = 1.5 pixels, so that any single pixel wide structure is conserved
        filter_threshold = math.exp(-1.125 / (filter_radius ** 2)) / filter_radius

        temp_array = np.where(filtered_array > filter_threshold, 1, 0).astype(image_data.dtype)

    elif filter_radius > 0 and filter_type == 0:
        # Median filter doesn't enlarge structures compared to Gaussian
        temp_array = median(thr_array, disk(filter_radius))

    else:
        temp_array = thr_array

    if close_radius > 0:
        if zCount > 1:
            structure = ball(close_radius)
        else:
            structure = disk(close_radius)

    t1_sk = datetime.now()
    axes = 'YX'

    # 3D+T
    if tCount > 1 and zCount > 1:
        axes = 'TZYX'
        for t in range(0, dims[0]):
            temp_array[t, :, :, :] = skeletonize_3d(temp_array[t, :, :, :])
            if open_skeleton > 0:
                temp_array[t, :, :, :] = opening(temp_array[t, :, :, :], selem=structure)
            elif close_radius:
                temp_array[t, :, :, :] = closing(temp_array[t, :, :, :], selem=structure)

    # 2D+T
    elif tCount > 1 and zCount == 1:
        axes = 'TYX'
        for t in range(0, dims[0]):
            temp_array[t, :, :] = skeletonize(temp_array[t, :, :])
            if open_skeleton > 0:
                temp_array[t, :, :] = opening(temp_array[t, :, :], selem=structure)
            elif close_radius:
                temp_array[t, :, :] = closing(temp_array[t, :, :], selem=structure)

    # 3D
    elif tCount == 1 and zCount > 1:
        axes = 'ZYX'
        temp_array = skeletonize_3d(temp_array)
        if open_skeleton > 0:
            temp_array = opening(temp_array, selem=structure)
        elif close_radius:
            temp_array = closing(temp_array, selem=structure)

    # 2D
    else:
        temp_array = skeletonize(temp_array)
        if open_skeleton > 0:
            temp_array = opening(temp_array, selem=structure)
        elif close_radius:
            temp_array = closing(temp_array, selem=structure)

    t2_sk = datetime.now()
    print(f'Skeleton detected in {round((t2_sk - t1_sk).total_seconds())} seconds')

    # Skeleton is binarized
    bin_skeleton = np.where(temp_array.astype(image_data.dtype) > 0, 1, 0).astype(image_data.dtype)
    
    # Define a structuring element to find nodes
    if zCount > 1:
        structuring_element = cube(3)
    else:
        structuring_element = square(3)
        
    # Label connected components in the skeleton
    labeled_skeletons, num_skeletons = label(bin_skeleton, structuring_element)

    # Initialize an empty array to store node points
    nodes = np.zeros_like(bin_skeleton)

    # Distance manually defined here to search for connectivity of each skeleton pixels
    branch_dist = 1

    # Iterate over each feature and check connectivity
    no_nodes = 0
    t1 = datetime.now()

    for sk_no in range(1, num_skeletons + 1):
        single_skeleton = np.where(labeled_skeletons == sk_no)

        for i in range(len(single_skeleton[0])):
            if zCount > 1:
                px = single_skeleton[0][i], single_skeleton[1][i], single_skeleton[2][i]
            else:
                px = single_skeleton[0][i], single_skeleton[1][i]

            cropped_skeleton = crop_array(bin_skeleton, px, branch_dist)

            # A node typically has 3 or more connected components (removing one corresponding to the central pixel
            if np.sum(cropped_skeleton) >= 3 + 1:
                nodes[px] = 1
                no_nodes += 1

        ''' IDEA TO DEVELOP >> transform skeleton as point cloud in 2D/3D and assess distance of pixels with KDtree?
        from sklearn.neighbors import KDTree
        tree = KDTree(pcloud)

        # For finding K neighbors of P1 with shape (1, 3)
        indices, distances = tree.query(P1, K)
        '''

    t2 = datetime.now()
    print(f'Number of detected nodes = {no_nodes}\n...done in {round((t2 - t1).total_seconds())} seconds')

    # Dilation of maps
    # Define a structuring element for dilation
    if zCount > 1:
        largest = disk(node_dilation_size)
        inter = disk(node_dilation_size - 1)
        smallest = disk(node_dilation_size - 2)
        len_to_add_1 = int((len(largest) - len(inter)) / 2)
        len_to_add_2 = int((len(largest) - len(smallest)) / 2)
        struct_element_nodes = [np.pad(smallest, len_to_add_2),
                                np.pad(inter, len_to_add_1),
                                largest,
                                np.pad(inter, len_to_add_1),
                                np.pad(smallest, len_to_add_2)]

        largest = disk(skeleton_dilation_size)
        smallest = disk(1)
        len_to_add = int((len(largest) - len(smallest)) / 2)
        struct_element_sk = [np.pad(smallest, len_to_add), largest, np.pad(smallest, len_to_add)]
    else:
        struct_element_nodes = disk(node_dilation_size)
        struct_element_sk = disk(skeleton_dilation_size)

    dilated_bin_skeleton = binary_dilation(bin_skeleton, struct_element_sk).astype(image_data.dtype) * bitdepth_max
    dilated_nodes = binary_dilation(nodes, struct_element_nodes).astype(image_data.dtype) * bitdepth_max
    dilated_branches = np.subtract(dilated_bin_skeleton, dilated_nodes).astype(image_data.dtype)

    # Save data to go back to Aivia
    meta_info = {'axes': axes}
    imsave(skeleton_p, dilated_bin_skeleton, imagej=True, photometric='minisblack', metadata=meta_info)
    imsave(nodes_map_p, dilated_nodes, imagej=True, photometric='minisblack', metadata=meta_info)
    imsave(branches_map_p, dilated_branches, imagej=True, photometric='minisblack', metadata=meta_info)


def crop_array(arr, central_coords, crop_radius):
    dims = arr.shape
    if len(dims) == 2:
        x_start = max(central_coords[1] - crop_radius, 0)
        x_end = min(central_coords[1] + crop_radius, dims[1])
        y_start = max(central_coords[0] - crop_radius, 0)
        y_end = min(central_coords[0] + crop_radius, dims[0])
        cropped_arr = arr[y_start:y_end+1, x_start:x_end+1]

    elif len(dims) == 3:
        x_start = max(central_coords[2] - crop_radius, 0)
        x_end = min(central_coords[2] + crop_radius, dims[2])
        y_start = max(central_coords[1] - crop_radius, 0)
        y_end = min(central_coords[1] + crop_radius, dims[1])
        z_start = max(central_coords[0] - crop_radius, 0)
        z_end = min(central_coords[0] + crop_radius, dims[0])
        cropped_arr = arr[z_start:z_end+1, y_start:y_end+1, x_start:x_end+1]

    return cropped_arr


if __name__ == '__main__':
    params = {
        'inputImagePath': r'UntitledZ.aivia.tif',
        'resultPath': r'testResult.tif',
        'resultPath2': r'testResult_nodes.tif',
        'resultPath3': r'testResult_branches.tif',
        'threshold': 16,
        'closeRadius': 0,
        'filterRadius': 0,
        'filterType': 1,
        'TCount': 1,
        'ZCount': 3,
        'Calibration': 'XYZT: 0.46 micrometers, 0.46 micrometers, 0.46 micrometers, 1 Default'
    }
    run(params)

# CHANGELOG:
#   v1.00: - Version using cropped 3*3 kernels on each pixel/voxel of the skeleton to detect nodes
