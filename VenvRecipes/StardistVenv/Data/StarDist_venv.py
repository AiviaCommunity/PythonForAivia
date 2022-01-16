import sys
import logging
import numexpr
import numpy as np
import pathlib
import tifffile
from numba import jit

from csbdeep.utils.tf import limit_gpu_memory
from stardist.models import StarDist2D, StarDist3D

"""
This python script must be executed in the StarDist_venv virtual environment.
It applies the StraDist 2D or 3D deep learning model to
generate segmentation for convex shape objects in 2D or 3D images.

StarDist GitHub: https://github.com/mpicbg-csbd/stardist

The source of the pre-trained 2D and 3D StarDist Models are listed below:
(1) 2D_demo model:
    https://github.com/mpicbg-csbd/stardist/tree/master/models/examples/2D_demo
(2) 2D_dsb_2018:
    https://github.com/mpicbg-csbd/stardist/tree/master/models/paper/2D_dsb2018
(3) 2D_fluor_nuc:
    https://drive.switch.ch/index.php/s/oCGZJaM949hMzjJ
    Please also check:
    https://github.com/mpicbg-csbd/stardist/issues/46
(4) 3D_demo model:
    https://github.com/mpicbg-csbd/stardist/tree/master/models/examples/3D_demo

Above models and associated files must be stored in following file structure
along with this python script.

Folder:
│
│   StarDist_venv.py
│
├───2D_demo
│       config.json
│       thresholds.json
│       weights_best.h5
│       weights_last.h5
│
├───2D_dsb2018
│       config.json
│       thresholds.json
│       weights_last.h5
│
├───2D_fluor_nuc
│       config.json
│       thresholds.json
│       weights_best.h5
│
└───3D_demo
        config.json
        thresholds.json
        weights_best.h5
        weights_last.h5

StarDist is set up with some parameters provided by the user:
    - Model: The user chooses model to use

    - Probability Threshold:
      Confidence lower than this threshold will be removed. Higher probability
      threshold values lead to fewer segmented objects, but will likely avoid
      false positives.

    - NMS Threshold:
      NMS stands for Non-maximum suppression threshold. A higher NMS threshold
      allows segmented objects to overlap substantially. A lower NMS threshold
      suppresses the object with lower confidence.

    - Percentile Normalization:
      We provide percentile-base normalization for users.
      The default is 2.0 for percentile_low and 99.9 for percentile_high.
      If percentile_low is higher than or equal to percentile_high, the recipe
      will choose the default value.

Requirements
------------
Check https://github.com/AiviaCommunity/PythonForAivia/blob/master/VenvRecipes/StardistVenv/requirements.txt

Parameters
----------
Input Image : Aivia channel
    Input channel to segment.

Diameter : double
    Approximate size of the structures you wish to segment (in pixels).

Model : int
    To determine which StarDist model you wish to run.
    0 : 2D_demo
    1 : 2D_fluor_nuc
    2 : 2D_DSB
    3 : 3D_demo

Probability Threshold : double
    If an object's confidence is lower than this threshold, it will be removed.

NMS Threshold : double
    Non maximum suppression threshold

percentile_high : int
    The percentile to be normalized to 1.

percentile_low : int
    The percentile to be normalized to 0.

Returns
-------
Aivia channel
    The segmentation is output by StarDist model.
"""

# Logger
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
handler.setFormatter(
    logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s'))
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.propagate = False


# perform image normalization
def normalize(image, p_min=2, p_max=99.9, dtype='float32'):
    '''
    Normalizes the image intensity so that the `p_min`-th and the `p_max`-th
    percentiles are converted to 0 and 1 respectively.
    '''
    low, high = np.percentile(image, (p_min, p_max))
    return numexpr.evaluate('(image - low) / (high - low)').astype(dtype)


# Add one pixel gap between neighboring labeled masks
@jit(nopython=True)  # Speed up with just-in-time compiler
def addOnePixelGap_2D(labeledMask):
    # 2D
    xLocList = []
    yLocList = []

    # Going through all pixels except image border
    # Find pixels having neighbors with higher label to remove
    for yy in range(1, labeledMask.shape[0] - 1):
        for xx in range(1, labeledMask.shape[1] - 1):
            # Skip background
            if (labeledMask[yy, xx] == 0):
                continue
            rmPix = False
            px1 = labeledMask[yy, xx]

            # Check all pixels in the 3x3 kernel
            for yLoc in range(yy - 1, yy + 2):
                for xLoc in range(xx - 1, xx + 2):
                    # Set to remove if one neighbor with higher label
                    if (px1 < labeledMask[yLoc, xLoc]):
                        rmPix = True
                        xLocList.append(xx)
                        yLocList.append(yy)
                        break
                if (rmPix):
                    break

    # Remove pixels in gaps
    for ii in range(0, len(xLocList)):
        labeledMask[yLocList[ii], xLocList[ii]] = 0


# Add one pixel gap between neighboring labeled masks
@jit(nopython=True)  # Speed up with just-in-time compiler
def addOnePixelGap_3D(labeledMask):
    # 3D
    xLocList = []
    yLocList = []
    zLocList = []

    # Going through all voxels except image border
    # Find voxels having neighbors with higher label to remove
    for zz in range(1, labeledMask.shape[0] - 1):
        for yy in range(1, labeledMask.shape[1] - 1):
            for xx in range(1, labeledMask.shape[2] - 1):
                # Skip background
                if (labeledMask[zz, yy, xx] == 0):
                    continue
                rmPix = False
                px1 = labeledMask[zz, yy, xx]

                # Check all voxels in the 3x3x3 kernel
                for zLoc in range(zz - 1, zz + 2):
                    for yLoc in range(yy - 1, yy + 2):
                        for xLoc in range(xx - 1, xx + 2):
                            # Set to remove if one neighbor with higher label
                            if (px1 < labeledMask[zLoc, yLoc, xLoc]):
                                rmPix = True
                                xLocList.append(xx)
                                yLocList.append(yy)
                                zLocList.append(zz)
                                break
                        if (rmPix):
                            break
                    if (rmPix):
                        break

    # Remove pixels in gaps
    for ii in range(0, len(xLocList)):
        labeledMask[zLocList[ii], yLocList[ii], xLocList[ii]] = 0


# [INPUT Name:inputImagePath Type:string DisplayName:'Input Image']
# [INPUT Name:z_count Type:int DisplayName:'Z Count' Default:1 Min:1 Max:int_max]
# [INPUT Name:t_count Type:int DisplayName:'T Count' Default:1 Min:1 Max:int_max]
# [INPUT Name:modelSelection Type:int DisplayName:'Model(0:demo,1:fluor, 2:DSB,3:3D)' Default:0 Min:0 Max:4]
# [INPUT Name:probThreshold Type:double DisplayName:'Probability Threshold (0.0-1.0)' Default:0.5 Min:0.0 Max:1.0]
# [INPUT Name:nmsThreshold Type:double DisplayName:'NMS Threshold (0.0-1.0)' Default:0.5 Min:0.0 Max:1.0]
# [INPUT Name:normalizationLow Type:double DisplayName:'Percentile Normalization Low (0.0-100.0)' Default:2.0 Min:0.0 Max:100.0]
# [INPUT Name:normalizationHigh Type:double DisplayName:'Percentile Normalization High (0.0-100.0)' Default:99.9 Min:0.0 Max:100.0]
# [INPUT Name:outputType Type:int DisplayName:'Output(0:Lb,1:Msk)' Default:0 Min:0 Max:1]
# [OUTPUT Name:resultPath Type:string DisplayName:'Segmentation Result']

def run_StarDist(
        inputImagePath, z_count, t_count, model_selection,
        probThreshold, nmsThreshold, normalizationLow, normalizationHigh,
        output_type, resultPath):

    print('------------------------------------------')
    print('       StarDist Virtual Environment')
    print('------------------------------------------')
    print(f'   inputImagePath = {inputImagePath}')
    print(f'          z_count = {z_count}')
    print(f'          t_count = {t_count}')
    print(f'  model_selection = {model_selection}')
    print(f'    probThreshold = {probThreshold}')
    print(f'     nmsThreshold = {nmsThreshold}')
    print(f' normalizationLow = {normalizationLow}')
    print(f'normalizationHigh = {normalizationHigh}')
    print(f'       outputType = {output_type}')
    print(f'       resultPath = {resultPath}')

    # Limit GPU memory usage
    limit_gpu_memory(fraction=None, allow_growth=True)

    # Get the path of the folder that contains this python script
    script_folder = pathlib.Path(__file__).resolve().parent
    logger.info(f'Script Folder = {script_folder}')

    # Get the model selections
    model_dict = {0: '2D_demo', 1: '2D_fluor_nuc',
                  2: '2D_dsb2018', 3: '3D_demo'}
    if model_selection not in model_dict:
        logger.warn('Selection is not available, use 2D_demo instead')
    model_name = model_dict[model_selection]

    # Load StarDist model assuming the 3D_demo and 2D_demo folders
    # are both in `script_folder`
    if z_count > 1:
        # input image is 3D or 3D+T
        logger.warn('Input is a 3D/3D+T image, use 3D_demo model')
        # Use 3D model for 3D image
        model = StarDist3D(None, name='3D_demo', basedir=script_folder)
        # Set 3D block size
        tile_shape = (50, 256, 256)
        # Check if input is a time-lapse image
        if t_count > 1:
            axes = 'YXZT'
        else:
            axes = 'YXZ'
    elif z_count == 1:
        # Use 2D model for 2D image
        model = StarDist2D(None, name=model_name, basedir=script_folder)
        # Set 2D tile size
        tile_shape = (512, 512)
        # Check if input is a time-lapse image
        if t_count > 1:
            axes = 'TYX'
        else:
            axes = 'YX'
    else:
        raise ValueError('Z count must be positive')

    # Load input image
    image = tifffile.imread(inputImagePath)
    dtype = image.dtype

    # Current limitation: input and output should have the same depth
    if dtype == np.uint8:
        logger.warn('Label image will be saved in 8bit')

    # Not a time-lapse
    if t_count == 1:
        image = image[np.newaxis]

    # Create output labeled image
    labels = np.empty_like(image, dtype=dtype)
    n_tiles = [i // t + 1 for t, i in zip(tile_shape, image[0].shape)]

    # Get thresholds
    prob_thresh = np.clip(probThreshold, 0.0, 1.0)
    nms_thresh = np.clip(nmsThreshold, 0.0, 1.0)

    # Use default thresholds optimized for the StarDist model when both
    # thresholds are set as 0
    if prob_thresh == 0.0 and nms_thresh == 0.0:
        logger.warn(
            'Use default thresholds of the StarDist model when both '
            'thresholds are set as 0.')
        prob_thresh = nms_thresh = None

    logger.info(f'probThreshold = {prob_thresh}, nmsThreshold = {nms_thresh}')

    # Get Normalization Percentile
    p_min = np.clip(normalizationLow, 0.0, 100.0)
    p_max = np.clip(normalizationHigh, 0.0, 100.0)

    # Use default normalization for the StarDist model when p_min >= p_max
    if p_min >= p_max:
        logger.warn(
            'Use default normalization of the StarDist model '
            'when p_min >= p_max.')
        p_min, p_max = 2, 99.9

    logger.info(f'normalizationLow = {p_min}, normalizationHigh = {p_max}')

    # Apply StarDist model
    for t in range(t_count):
        labels[t] = model.predict_instances(
            normalize(image[t], p_min=p_min, p_max=p_max),
            prob_thresh=prob_thresh,
            nms_thresh=nms_thresh,
            n_tiles=n_tiles,
            show_tile_progress=False)[0].astype(dtype)

        # Convert labeled mask to binary mask
        if (output_type == 1):
            # Add two pixel gap between neighboring masks
            if (z_count > 1):
                addOnePixelGap_3D(labels[t])
            else:
                addOnePixelGap_2D(labels[t])

            # Convert to binary mask
            val = 255
            if (labels[t].dtype.type == np.uint16):
                val = 65535
            labels[t] = (labels[t] > 0) * val

    # Not a time-lapse
    if t_count == 1:
        labels = labels[0]

    # Save the labeled image
    tifffile.imwrite(resultPath,
                     labels,
                     photometric='minisblack',
                     metadata={'axes': axes})


def main():

    # Check argument count
    correctArgumentCount = 11
    if (len(sys.argv) != correctArgumentCount):
        ErrorMsg = 'Incorrect argument count ' + str(len(sys.argv)) +\
                   '(Need ' + str(correctArgumentCount) + ')'
        raise ValueError(ErrorMsg)

    # Get input, output, and parameters
    inputImagePath = sys.argv[1]
    z_count = int(sys.argv[2])
    t_count = int(sys.argv[3])
    model_selection = int(sys.argv[4])
    probThreshold = float(sys.argv[5])
    nmsThreshold = float(sys.argv[6])
    normalizationLow = float(sys.argv[7])
    normalizationHigh = float(sys.argv[8])
    output_type = int(sys.argv[9])
    resultPath = sys.argv[10]

    # Perform StarDist to generate binary mask
    run_StarDist(
        inputImagePath, z_count, t_count, model_selection,
        probThreshold, nmsThreshold, normalizationLow, normalizationHigh,
        output_type, resultPath)


if __name__ == "__main__":
    main()
