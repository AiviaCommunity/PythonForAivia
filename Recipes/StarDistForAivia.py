import drvdeeplearning as drv
import logging
import numpy as np
import pathlib
import tifffile

from csbdeep.utils.tf import limit_gpu_memory
from stardist.models import StarDist2D, StarDist3D

"""
This Aivia python recipe applyies the StraDist 2D or 3D deep learning model to
generate segmentation for convex shape objects in 2D or 3D images.

StarDist GitHub: https://github.com/mpicbg-csbd/stardist

The source of the pre-trained 2D and 3D StarDist Models are listed below:
(1) 2D_demo model: https://github.com/mpicbg-csbd/stardist/tree/master/models/examples/2D_demo
(2) 2D_dsb_2018: https://github.com/mpicbg-csbd/stardist/tree/master/models/paper/2D_dsb2018
(3) 2D_fluor_nuc: https://drive.switch.ch/index.php/s/oCGZJaM949hMzjJ
    Please also check: https://github.com/mpicbg-csbd/stardist/issues/46
(4) 3D_demo model: https://github.com/mpicbg-csbd/stardist/tree/master/models/examples/3D_demo

Please put this recipe along with above models in following file structure
Folder:
│
│   StarDistForAivia.py
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
numpy (comes with Aivia installer)
scikit-image (comes with Aivia installer)
tifffile (installed with scikit-image)
TensorFlow 1.X (StarDist is developed in TF 1.x, please do not use TensorFlow 2.x.
If you want GPU acceleration, please install tensorflow-gpu and respective version
of CUDA and cuDNN)
drvdeeplearning (comes with Aivia installer)
StarDist 0.5.0
CSBDeep (installed with StarDist)

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

handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
handler.setFormatter(
    logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s'))
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.propagate = False

# [INPUT Name:inputImagePath Type:string DisplayName:'Input Image']
# [INPUT Name:modelSelection Type:int DisplayName:'Model(0:demo,1:fluor, 2:DSB,3:3D)' Default:0 Min:0 Max:4]
# [INPUT Name:probThreshold Type:double DisplayName:'Probability Threshold (0.0-1.0)' Default:0.5 Min:0.0 Max:1.0]
# [INPUT Name:nmsThreshold Type:double DisplayName:'NMS Threshold (0.0-1.0)' Default:0.5 Min:0.0 Max:1.0]
# [INPUT Name:normalizationLow Type:double DisplayName:'Percentile Normalization Low (0.0-100.0)' Default:2.0 Min:0.0 Max:100.0]
# [INPUT Name:normalizationHigh Type:double DisplayName:'Percentile Normalization High (0.0-100.0)' Default:99.9 Min:0.0 Max:100.0]
# [OUTPUT Name:resultPath Type:string DisplayName:'Segmentation Result']
def run(params):
    # Limit GPU memory usage
    limit_gpu_memory(fraction=None, allow_growth=True)

    # Get Z count and T count
    z_count, t_count = [int(params[f'{s}Count']) for s in ['Z', 'T']]

    # Get the path of the folder that contains this python script
    script_folder = pathlib.Path(__file__).resolve().parent
    logger.info(f'Script Folder = {script_folder}')

    # Get the model selections
    model_dict = {0: '2D_demo', 1: '2D_fluor_nuc',
                  2: '2D_dsb2018', 3: '3D_demo'}
    model_selection = int(params['modelSelection'])
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
    image = tifffile.imread(params['inputImagePath'])
    dtype = image.dtype

    # Current limitation: input and output should have the same depth
    if dtype == np.uint8:
        logger.warn('Label image will be saved in 8bit')

    # Not a time-lpase
    if t_count == 1:
        image = image[np.newaxis]

    # Create output labeled image
    labels = np.empty_like(image, dtype=dtype)
    n_tiles = [i // t + 1 for t, i in zip(tile_shape, image[0].shape)]

    # Get threesholds
    prob_thresh, nms_thresh = [
        np.clip(float(params[f'{t}Threshold']), 0.0, 1.0)
        for t in ['prob', 'nms']]

    # Use default thresholds optimized for the StarDist model when both
    # thresholds are set as 0
    if prob_thresh == 0.0 and nms_thresh == 0.0:
        logger.warn(
            'Use default thresholds of the StarDist model when both '
            'thresholds are set as 0.')
        prob_thresh = nms_thresh = None

    logger.info(f'probThreshold = {prob_thresh}, nmsThreshold = {nms_thresh}')

    # Get Normalization Percentile
    p_min, p_max = [
        np.clip(float(params[f'normalization{t}']), 0.0, 100.0)
        for t in ['Low', 'High']]

    # Use default normaliztion for the StarDist model when p_min >= p_max
    if p_min >= p_max:
        logger.warn(
            'Use default normalization of the StarDist model '
            'when p_min >= p_max.')
        p_min, p_max = 2, 99.9

    logger.info(f'normalizationLow = {p_min}, normalizationHigh = {p_max}')

    # Apply StartDist model to generate labeled image
    for t in range(t_count):
        labels[t] = model.predict_instances(
            drv.utils.normalize(image[t], p_min=p_min, p_max=p_max),
            prob_thresh=prob_thresh,
            nms_thresh=nms_thresh,
            n_tiles=n_tiles,
            show_tile_progress=False)[0].astype(dtype)

    # Not a time-lapse
    if t_count == 1:
        labels = labels[0]

    # Save the labeled image
    tifffile.imwrite(params['resultPath'],
                     labels,
                     photometric='minisblack',
                     metadata={'axes': axes})
