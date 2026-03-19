import ctypes
import math
import sys
import os.path
import numpy as np
from skimage.io import imread, imsave
from skimage.measure import label, regionprops
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree


# DEFAULT PARAMETERS
BATCH_MODE_COMPATIBLE = False
DEFAULT_MAX_OBJECT_COUNT = 10       # 0 = skip maximum

ACTIVATE_OPTION_1 = True            # OPTION 1 = Check selected objects partially overlap with the reference mask

activate_option_2 = True            # OPTION 2 = Avoid selection of two objects within a given calibrated distance
DEFAULT_EXCLUSION_DISTANCE = 20     # in µm

activate_option_3 = True            # OPTION 3 = Expand object mask to a target area, following the boundaries of a larger binary mask (reference mask)
DEFAULT_DILATION_AREA = 150         # in µm2

BBOX_DILATION_FACTOR = 10           # To be able to extend the mask in a crop avoiding processing the full image

"""
Process a binary mask input of non-touching objects to perform a random spatial selection of objects.
Options:
    - Check selected objects partially overlap with the reference mask. If mask does not exist, provide the same mask as the first binary mask
    - Avoid selection of two objects within a given calibrated distance
    - Expand object mask to a specific area, following the boundaries of a larger binary mask (reference mask)
    
Distance for exclusion is also used to remove objects close to image borders.
Batch mode can be activated above to use default values also provided above.

Works only for 2D images (no timepoint).

Guidelines
------------
Prerequisite: binary mask of your objects (can be done with the save button in the 'Objects' panel)
- In the recipe input, you have the ability to put a reference mask for the tissue. If you don't have it, put the object mask.
- If you let 0 for 'Max Object Count', all objects will be selected, upon following the other rules if active
- If you let 0 for other parameters, the rules are ignored

Requirements
------------
numpy (comes with Aivia installer)
scikit-image (comes with Aivia installer)
ctypes

Parameters
----------
Input channel:
    Input channel with binary mask of non-touching objects.
    Reference mask
    
Values:
    Proximity Exclusion distance
    Target area

Returns
-------
Object Set in Aivia

Note: replace output with one of the line below to change output type (objects or mask)
# [OUTPUT Name:resultPath Type:string DisplayName:'Split Labeled Mask']
# [OUTPUT Name:resultPath Type:string DisplayName:'Random Object Selection' Objects:2D MinSize:0.5 MaxSize:50000.0]
"""

DEBUG_MODE = False


# [INPUT Name:dilateArea Type:double DisplayName:'Dilate to reach area (calibrated)' Default:1.0 Min:0.0 Max:65535.0]
# [INPUT Name:exclusionDistance Type:double DisplayName:'Exclusion distance (calibrated)' Default:1.0 Min:0.0 Max:65535.0]
# [INPUT Name:maxObjectCount Type:int DisplayName:'Max Object Count' Default:1 Min:0 Max:65535]
# [INPUT Name:refImagePath Type:string DisplayName:'Reference Mask']
# [INPUT Name:inputImagePath Type:string DisplayName:'Binary Mask']
# [OUTPUT Name:resultPath Type:string DisplayName:'Objects from labels' Objects:2D MinSize:0.0 MaxSize:50000.0]
def run(params):
    global activate_option_2, activate_option_3
    image_location = params['inputImagePath']
    ref_location = params['refImagePath']
    result_location = params['resultPath']
    zCount = int(params['ZCount'])
    tCount = int(params['TCount'])
    if not os.path.exists(image_location):
        print(f"Error: {image_location} does not exist")
        return

    pixel_cal_tmp = params['Calibration']
    pixel_cal = pixel_cal_tmp[6:].split(', ')           # Expects calibration with 'XYZT: ' in front
    XY_cal = float(pixel_cal[0].split(' ')[0])

    max_object_count = int(params['maxObjectCount'])
    if max_object_count == 0 and BATCH_MODE_COMPATIBLE:
        max_object_count = DEFAULT_MAX_OBJECT_COUNT

    exclusion_distance = float(params['exclusionDistance'])
    if exclusion_distance == 0.0 and BATCH_MODE_COMPATIBLE:
        exclusion_distance = DEFAULT_EXCLUSION_DISTANCE
    exclusion_distance_px = exclusion_distance / XY_cal

    if activate_option_2 and exclusion_distance_px == 0:
        activate_option_2 = False
        print("PARAM: Exclusion step based on distance to other objects was skipped due to value being 0.")

    dilate_target_area = float(params['dilateArea'])
    if dilate_target_area == 0.0 and BATCH_MODE_COMPATIBLE:
        dilate_target_area = DEFAULT_DILATION_AREA
    dilate_target_area = dilate_target_area / XY_cal / XY_cal

    if activate_option_3 and dilate_target_area == 0.0:
        activate_option_3 = False
        print("PARAM: Dilation step was skipped due to target area being 0.0.")

    # Reading masks
    input_mask = imread(image_location)
    ref_mask = imread(ref_location).astype(bool)
    dims = input_mask.shape
    print('-- Input dimensions (expected (Z), Y, X): ', np.asarray(dims), ' --')

    # Checking image is not 2D+t or 3D+t
    if zCount > 1 or tCount > 1:
        mess = 'This recipes currently only supports 2D images without time dimension.'
        Mbox('Error', mess, 0)
        sys.exit(mess)

    # Checking the provided masks are binary
    if len(np.unique(input_mask)) != 2:
        error_mess = 'Error: provided channel seems not to be a binary mask.'
        ctypes.windll.user32.MessageBoxW(0, error_mess, 'Error', 0)
        sys.exit(error_mess)

    if len(np.unique(input_mask)) != 2:
        error_mess = 'Error: provided channel seems not to be a binary mask.'
        ctypes.windll.user32.MessageBoxW(0, error_mess, 'Error', 0)
        sys.exit(error_mess)

    # Transforming input mask into labeled mask
    labels = label(input_mask, connectivity=1)

    # random order processing
    label_ids = np.unique(labels[labels > 0])
    np.random.shuffle(label_ids)

    if ACTIVATE_OPTION_1:
        # precompute overlap per label (vectorized, once) with the reference mask
        overlap_flag = np.zeros(labels.max() + 1, dtype=bool)
        overlap_flag[np.unique(labels[ref_mask & (labels > 0)])] = True

    # Loop over candidates
    obj_count = 0
    kept_centroids = []
    output_data = np.zeros_like(input_mask)
    img_h, img_w = input_mask.shape
    pad_dist = int(math.sqrt(dilate_target_area / math.pi) * BBOX_DILATION_FACTOR)      # For OPTION 3

    props = regionprops(labels)

    for lid in label_ids:
        if ACTIVATE_OPTION_1:   # Check partial overlap with the reference mask
            if not overlap_flag[lid]:
                if DEBUG_MODE:
                    print(f"Label {lid} was discarded as it is not overlapping with the reference mask.")
                continue    # next candidate

        # Calculate centroid of current label
        centroid = props[lid - 1].centroid

        # Double check proximity to image boundaries
        if (centroid[0] < exclusion_distance_px or centroid[0] > (img_h - exclusion_distance_px) or
                centroid[1] < exclusion_distance_px or centroid[1] > (img_w - exclusion_distance_px)):
            print(f"Label {lid} was discarded as its distance to image border is lower than exclusion distance ({exclusion_distance} µm).")
            continue

        if activate_option_2:   # Avoid selection of two objects within a given calibrated distance
            if kept_centroids:
                tree = cKDTree(kept_centroids)
                if tree.query(centroid, k=1)[0] < exclusion_distance_px:     # Too close
                    continue

            # Adding centroid for comparison with the future labels
            kept_centroids.append(centroid)

        print(f"Selected label: {lid}")

        # Define bounding box of label for transfer to come
        minr, minc, maxr, maxc = props[lid - 1].bbox

        if activate_option_3:   # OPTION 3 = Expand object mask to a target area, following the boundaries of ref mask
            # Crop with padding due to extension process
            minr_crop, minc_crop, maxr_crop, maxc_crop = (max(minr - pad_dist, 0), max(minc - pad_dist, 0),
                                                          min(maxr + pad_dist, img_h), min(maxc + pad_dist, img_w))

            crop = (labels[minr_crop:maxr_crop, minc_crop:maxc_crop] == lid)
            ref_crop = ref_mask[minr_crop:maxr_crop, minc_crop:maxc_crop]

            # Extend mask
            new_crop, n_iter = extend_mask_to_area(crop, ref_crop, dilate_target_area)
            if DEBUG_MODE:
                print(f"Label {lid} was extended to reach the area {dilate_target_area} with {n_iter} dilation cycles.")

        else:
            minr_crop, minc_crop, maxr_crop, maxc_crop = minr, minc, maxr, maxc
            new_crop = (labels[minr_crop:maxr_crop, minc_crop:maxc_crop] == lid)

        # Put mask back into output
        output_data[minr_crop:maxr_crop, minc_crop:maxc_crop] |= new_crop       # add info into existing output mask

        obj_count += 1
        if DEBUG_MODE:
            print(f"Label {lid} was added to output mask with bounding box: [{[minr_crop, maxr_crop, minc_crop, maxc_crop]}]")

        if 0 < max_object_count <= obj_count:
            print(f"Reached maximum object count ({max_object_count}).")
            break

    imsave(result_location, output_data)


def extend_mask_to_area(mask, large_mask, target_area):
    bool_mask = mask.astype(bool)
    m = bool_mask.copy()
    m &= large_mask  # enforce overlap constraint

    # Defining max iter to avoid endless loop
    target_area_radius = math.sqrt(target_area / math.pi) - math.sqrt(m.sum() / math.pi)
    curr_radius = max(int(target_area_radius) - 1, 0)
    max_iter = 50                  # Arbitrary 20 times

    for iter in range(max_iter):
        # Iterate on radius
        curr_radius += 1

        curr_labels = label(m)
        if np.max(curr_labels) > 1:
            m = extract_largest_2D_object_mask(m)
            if DEBUG_MODE:
                print(f"--> Found {np.max(curr_labels)} shapes after dilation fitting tissue mask. Keeping largest one only."
                      f"\n-->    New area is {m.sum()}")

        if m.sum() >= target_area:
            break
        if DEBUG_MODE:
            print(f"Current area = {m.sum()}")
        m = distance_transform_edt(~bool_mask) <= curr_radius
        m &= large_mask  # enforce overlap constraint

    if DEBUG_MODE:
        print(f"Dilation ended with final area = {m.sum()} (vs target = {target_area})")

    return m, iter


def extract_largest_2D_object_mask(bin_image):
    # Label connected components in the binary image
    labeled_image = label(bin_image)
    props = regionprops(labeled_image)

    # Find the largest object based on area
    max_val = 0
    largest_object = None
    for ind, prop in enumerate(props):
        if DEBUG_MODE:
            print(f'Object {ind+1} area is: {prop.area}')
        if prop.area > max_val:
            max_val = prop.area
            largest_object = prop

    # Log
    if DEBUG_MODE:
        print(f'Found {len(props)} objects. Selecting the largest with area = {max_val}.')

    new_mask = (labeled_image == largest_object.label)
    return new_mask


def Mbox(title, text, style):
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)


if __name__ == '__main__':
    params = {'inputImagePath': r'D:\PythonCode\_tests\XY_975x640_1ch_8bit_BinaryMask_Cells-in-DAB-tissue_A15.0.aivia.tif',
              'refImagePath': r'D:\PythonCode\_tests\XY_975x640_1ch_8bit_BinaryMask_DAB-tissue-mask_A15.0.aivia.tif',
              'resultPath': r'D:\PythonCode\_tests\output.tif',
              'TCount': 1,
              'ZCount': 1,
              'dilateArea': 5000,
              'exclusionDistance': 100,
              'maxObjectCount': 0,
              'Calibration': 'XYZT: 1 micrometers, 1 micrometers, 1 micrometers, 1 Default'
              }
    run(params)

# CHANGELOG
#   v1_00: - First version, with several options already
#   v1_10: - Replaced dilation to be round-shaped instead of cross-based from the iterative dilation
#   v1_20: - Speeding up dilation with scipy distance transform
