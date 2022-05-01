import sys
import os.path
import numpy as np
from tifffile import imread, imwrite
from cellpose import models
from skimage.exposure import rescale_intensity
from skimage.util import img_as_ubyte, img_as_uint
from skimage.transform import resize
from scipy.special import expit

"""
This python script must be executed in the Cellpose_venv virtual environment.
It applies the Cellpose 2D or 3D deep learning model to
generate segmentation for convex shape objects in 2D or 3D images.

Sources of the pre-trained cellpose models are listed below:
    Cellpose Website: http://www.cellpose.org/
    Cellpsoe GitHub: https://github.com/MouseLand/cellpose
    Cellpose ducumentation: http://www.cellpose.org/static/docs/index.html
    Cellpsoe paper: https://www.biorxiv.org/content/10.1101/2020.02.02.931238v1

Requirements
------------
Check https://github.com/AiviaCommunity/PythonForAivia/blob/master/VenvRecipes/CellposeVenv/requirements.txt


Parameters
----------
Input Image : Aivia channel
    Input channel to segment.

Diameter : double
    Approximate size of the structures you wish to segment (in pixels).

Model : int (bool)
    Boolean to determine which Cellpose model you wish to run.
    0 : Choose the cytoplasm model (segment the whole cell).
    1 : Choose the nuclei model

Mask threshold Threshold (Cell Probability Threshold)) : double, -6.0 to 6.0
    https://cellpose.readthedocs.io/en/latest/settings.html#mask-threshold
    The pixels greater than the mask_threshold are used to run dynamics and determine masks. The predictions 
    the network makes of the probability are the inputs to a sigmoid centered at zero (1 / (1 + e^-x)), so 
    they vary from around -6 to +6.  The default is mask_threshold=0.0.


Flow Threshold : double, default is 0.4
    https://cellpose.readthedocs.io/en/latest/settings.html?highlight=threshold#flow-threshold
    The Flow Threshold is the maximum allowed error of the flows for each mask.
    Increase this threshold if cellpose is not returning as many masks as
    expected.

Returns
-------
Confidence Map : Aivia channel
    The flow that is output by Cellpose. This represents a confidence that
    each voxel belongs to the segmentation.

Mask : Aivia channel
    Segmented result

"""


def run_Cellpose(inputImagePath, z_count, t_count, diameter, model_type,
                 conf_map_path, mask_path, mask_threshold, flow_threshold):

    print('------------------------------------------')
    print('       Cellpose Virtual Environment')
    print('------------------------------------------')
    print(f'   inputImagePath = {inputImagePath}')
    print(f'          z_count = {z_count}')
    print(f'          t_count = {t_count}')
    print(f'         diameter = {diameter}')
    print(f'       model_type = {model_type}')
    print(f'    conf_map_path = {conf_map_path}')
    print(f'        mask_path = {mask_path}')
    print(f'   mask_threshold = {mask_threshold}')
    print(f'   flow_threshold = {flow_threshold}')

    # Check if input image exists
    if not os.path.exists(inputImagePath):
        raise ValueError('Error: {inputImagePath} does not exist')

    # Load input image
    image_data = imread(inputImagePath)
    image_type = image_data.dtype
    dims = image_data.shape

    confidence = np.empty_like(image_data, dtype=float)
    mask = np.empty_like(image_data, dtype=image_type)

    # Get model type
    if model_type == 0:
        cellpose_model = models.Cellpose(gpu=True, model_type='cyto')
    elif model_type == 1:
        cellpose_model = models.Cellpose(gpu=True, model_type='nuclei')
    else:
        raise ValueError('Invalid model selected'
                         '- use 0 for cytoplasm and 1 for nuclei.')

    # Channel to segment: [0, 0] means grey scale image
    channels = [0, 0]

    # 3D+T
    if t_count > 1 and z_count > 1:
        print(f"Applying to 3D+T case with dims: {dims}")
        for t in range(t_count):
            mask_i, flow, _, _ = cellpose_model.eval(
                                    image_data[t],
                                    channels=channels,
                                    diameter=diameter,
                                    do_3D=True,
                                    mask_threshold=mask_threshold,
                                    flow_threshold=flow_threshold,
                                    resample=True)
            confidence[t] = flow[2]
            mask[t] = mask_i
        axes = 'YXZT'

    # 3D
    elif t_count == 1 and z_count > 1:
        print(f"Applying to 3D case with dims: {dims}")
        mask, flow, _, _ = cellpose_model.eval(
                                        image_data,
                                        channels=channels,
                                        diameter=diameter,
                                        do_3D=True,
                                        mask_threshold=mask_threshold,
                                        flow_threshold=flow_threshold,
                                        resample=True)
        confidence = flow[2]
        axes = 'YXZ'

    # 2D+T
    elif t_count > 1 and z_count == 1:
        print(f"Applying to 2D+T case with dims: {dims}")
        for t in range(t_count):
            mask_i, flow, _, _ = cellpose_model.eval(
                                        image_data[t],
                                        channels=channels,
                                        diameter=diameter,
                                        mask_threshold=mask_threshold,
                                        flow_threshold=flow_threshold,
                                        resample=True)
            confidence[t] = flow[2]
            mask[t] = mask_i.astype(image_type)
        axes = 'YXT'

    # 2D
    else:
        print(f"Applying to 2D case with dims: {dims}")
        mask, flow, _, _ = cellpose_model.eval(
                                        image_data,
                                        channels=channels,
                                        diameter=diameter,
                                        mask_threshold=mask_threshold,
                                        flow_threshold=flow_threshold,
                                        resample=True)
        confidence = flow[2]
        mask = mask.astype(image_type)
        axes = 'YX'

    # Convert raw model output to 0-1 using expit
    confidence = expit(confidence)

    # Re-scale confidence to input image range
    confidence = rescale_intensity(confidence, in_range=(0.0, 1.0), 
                                   out_range=image_type.name).astype(image_type)
    
    if image_type == np.uint16:
        # randomize mask output, otherwise the default mask is gradient-like
        mask_permute = np.append([0], np.random.permutation(65535)+1)
        mask = mask_permute[mask]
        confidence = img_as_uint(confidence)
        mask = img_as_uint(mask)
    else:
        mask_permute = np.append([0], np.random.permutation(255)+1)
        mask = mask_permute[mask]

        confidence = img_as_ubyte(confidence)
        mask = img_as_ubyte(mask)

    # Save confidence
    imwrite(conf_map_path,
            confidence,
            photometric='minisblack',
            metadata={'axes': axes})

    # Save mask
    imwrite(mask_path,
            mask,
            photometric='minisblack',
            metadata={'axes': axes})


def main():

    # Check argument count
    correctArgumentCount = 10
    if (len(sys.argv) != correctArgumentCount):
        ErrorMsg = 'Incorrect argument count ' + str(len(sys.argv)) + '(Need ' + str(correctArgumentCount) + ')'
        raise ValueError(ErrorMsg)

    # Get input, output, and parameters
    inputImagePath = sys.argv[1]
    z_count = int(sys.argv[2])
    t_count = int(sys.argv[3])
    diameter = float(sys.argv[4])
    model_type = int(sys.argv[5])
    conf_map_path = sys.argv[6]
    mask_path = sys.argv[7]
    mask_threshold = float(sys.argv[8])
    flow_threshold = float(sys.argv[9])

    # Perform Cellpose
    run_Cellpose(inputImagePath,
                 z_count,
                 t_count,
                 diameter,
                 model_type,
                 conf_map_path,
                 mask_path,
                 mask_threshold,
                 flow_threshold)


if __name__ == "__main__":
    main()
