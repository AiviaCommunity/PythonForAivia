import os.path
import numpy as np
from tifffile import imread, imwrite
from cellpose import models
from skimage.exposure import rescale_intensity
from skimage.util import img_as_ubyte, img_as_uint
"""
This Aivia python recipe applyies the Cellpose deep learning model to
generate segmentation for cells/nucleus in 2D or 3D images.

Cellpose is set up with some parameters provided by the user:
    - Model: the user chooses whether to use the cytoplasm or nuclei model
    - Diameter: the user provides an approximation of object size

Note that the GPU model is called, but will not run unless Cellpose is properly
installed as described here: http://www.cellpose.org/static/docs/installation.html
Example of installation:
    pip install cellpose == 0.0.2.0
    pip uinstall mxnet-mkl
    pip uinstall mxnet
    pip install mxnet-cu100
    pip install mxnet-cu100mkl

Sources of the pretrained cellpose models are listed below:
    Cellpsoe GitHub: https://github.com/mpicbg-csbd/stardist
    Cellpose ducumentation: http://www.cellpose.org/static/docs/index.html
    Cellpsoe paper: https://www.biorxiv.org/content/10.1101/2020.02.02.931238v1

Requirements
------------
numpy (comes with Aivia installer)
scikit-image (comes with Aivia installer)
tifffile (installed with scikit-image)
Cellpose 0.0.2.0 (the recipe is only tested in this version)
CUDA 10.x
mxnet-cu10x (remove mxnet and install gpu version of mxnet​)
mxnet-cu10xmkl (remove mxnet-mkl and install gpu version of mxnet​-mkl)


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

Returns
-------
Confidence Map : Aivia channel
    The flow that is output by Cellpose. This represents a confidence that each voxel
    belongs to the segmentation.

Mask : Aivia channel
    Segmented result

"""

# [INPUT Name:inputImagePath Type:string DisplayName:'Input Image']
# [INPUT Name:diameter Type:double DisplayName:'Diameter (px)' Default:30.0 Min:0.0 Max:1000.0]
# [INPUT Name:modelType Type:int DisplayName:'Model Type (0=ctyo, 1=nuc)' Default:0 Min:0 Max:1]
# [OUTPUT Name:resultPath Type:string DisplayName:'Confidence Map']
# [OUTPUT Name:resultPath2 Type:string DisplayName:'Mask']
def run(params):

    # Check if input image exists
    inputImagePath = params['inputImagePath']
    if not os.path.exists(inputImagePath):
        raise ValueError('Error: {inputImagePath} does not exist')

    result_location = params['resultPath']
    result_location2 = params['resultPath2']
    diameter = float(params['diameter'])

    # Get Z count and T count
    zCount = int(params['ZCount'])
    tCount = int(params['TCount'])

    # Load input image
    image_data = imread(inputImagePath)
    dtype = image_data.dtype
    dims = image_data.shape

    # confidence = np.empty(shape=dims, dtype=dtype)
    confidence = np.empty_like(image_data)
    mask = np.empty_like(image_data, dtype=dtype)

    # Get model type
    model_type = int(params['modelType'])
    if model_type == 0:
        cellpose_model = models.Cellpose(gpu=True, model_type='cyto')
    elif model_type == 1:
        cellpose_model = models.Cellpose(gpu=True, model_type='nuclei')
    else:
        raise ValueError('Invalid model selected - use 0 for cytoplasm and 1 for nuclei.')

    # Channel to segment: [0, 0] means grey scale image
    channels = [0, 0]

    # 3D+T
    if tCount > 1 and zCount > 1:
        print(f"Applying to 3D+T case with dims: {dims}")
        for t in range(tCount):
            mask_i, flow, _, _ = cellpose_model.eval(image_data[t],
                                                     channels=channels,
                                                     diameter=diameter,
                                                     do_3D=True)
            confidence[t] = flow[2]
            mask[t] = mask_i
        axes = 'YXZT'

    # 3D
    elif tCount == 1 and zCount > 1:
        print(f"Applying to 2D+T or 3D case with dims: {dims}")
        mask, flow, _, _ = cellpose_model.eval(image_data,
                                               channels=channels,
                                               diameter=diameter,
                                               do_3D=True)
        confidence = flow[2]
        axes = 'YXZ'

    # 2D+T
    elif tCount > 1 and zCount == 1:
        for t in range(tCount):
            mask_i, flow, _, _ = cellpose_model.eval(image_data[t],
                                                     channels=channels,
                                                     diameter=diameter)
            confidence[t] = flow[0][2].astype(dtype)
            mask[t] = mask_i[0].astype(dtype)
        axes = 'YXT'

    # 2D
    else:
        print(f"Applying to 2D case with dims: {dims}")
        mask, flow, _, _ = cellpose_model.eval(image_data,
                                               channels=channels,
                                               diameter=diameter)
        confidence = flow[0][2]
        mask = mask[0].astype(dtype)
        axes = 'YX'

    # Rescale confidence to unsign
    if np.min(confidence) < 0:
        confidence = rescale_intensity(confidence, out_range='float')

    if image_data.dtype == np.uint16:
        # radomnize mask ouput, otherwise the default mask is gradient-like
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
    imwrite(result_location,
            confidence,
            photometric='minisblack',
            metadata={'axes': axes})

    # Save mask
    imwrite(result_location2,
            mask,
            photometric='minisblack',
            metadata={'axes': axes})


if __name__ == '__main__':
    params = {}
    run(params)
