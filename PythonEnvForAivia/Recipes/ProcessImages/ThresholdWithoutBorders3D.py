import os.path
import numpy as np
from tifffile import imread, imsave
from skimage.segmentation import clear_border
from skimage.measure import label
from skimage.morphology import closing, ball
from skimage.util import img_as_ubyte, img_as_uint

"""
See: https://scikit-image.org/docs/dev/api/skimage.segmentation.html#skimage.segmentation.clear_border

Tresholds an image for segmentation, then clears any objects intersecting the image borders before
creating an object set in Aivia.

This recipe only works in 3D. Use ThresholdWithoutBorders2D instead for 2D cases.

Aivia's mesh creation engine will not automatically label meshes it creates in 3D, so we must
explicitly label the objects we pass to Aivia. Aivia will also not accept images returned as
a different bit depth than their input. Therefore, the user is recommended to convert their
input channel to 16bit (right-click the channel > convert to > 16 bit) in Aivia before
applying this recipe if they expect more than 255 objects to be segmented.

Requirements
------------
numpy (comes with Aivia installer)
scikit-image (comes with Aivia installer)
tifffile (installed with scikit-image)

Parameters
----------
Input Image : Aivia channel
    Input channel to use for the transform.

Threshold : int
    Grayvalue above which to mask.

Closing Radius : int
    Size of kernel used to "fill in" holes or concavities in the segmentation.

Returns
-------
Aivia objects
    Result of the transform.
"""

# [INPUT Name:inputImagePath Type:string DisplayName:'Input Image']
# [INPUT Name:threshold Type:int DisplayName:'Threshold' Default:128 Min:0 Max:65535]
# [INPUT Name:radius Type:int DisplayName:'Closing Radius' Default:0 Min:0 Max:100]
# [OUTPUT Name:resultObjectPath Type:string DisplayName:'Objects' Objects:3D MinSize:0.0 MaxSize:1000000000.0]
def run(params):
    image_location = params['inputImagePath']
    result_object_location = params['resultObjectPath']
    threshold = int(params['threshold'])
    radius = int(params['radius'])
    tCount = int(params['TCount'])
    zCount = int(params['ZCount'])
    
    if not os.path.exists(image_location):
        print(f'Error: {image_location} does not exist')
        return
    
    if zCount == 1:
        print('This recipes currently only supports 3D and 3D+T images.')
        print('Try using ThresholdWithoutBorders2D.py instead.')
        return
        
    image_data = imread(image_location)
    dims = image_data.shape
    mask = np.empty(image_data.shape, dtype=image_data.dtype)
    if radius != 0:
        structure = ball(radius)
    
    # 3D+T
    if tCount > 1 and zCount > 1:
        print(f"Applying to 3D+T case with dims: {image_data.shape}")
        for t in range(0, dims[0]):
            mask[t,:,:,:] = np.where(image_data[t,:,:,:] > threshold, 1, 0)
            if radius != 0:
                mask[t,:,:,:] = closing(mask[t,:,:,:], selem=structure)
            mask[t,:,:,:] = label(clear_border(mask[t,:,:,:]))
        axes = 'YXZT'
    # 3D
    elif tCount == 1 and zCount > 1:
        print(f"Applying to 3D case with dims: {image_data.shape}")
        mask = np.where(image_data > threshold, 1, 0)
        if radius != 0:
            mask = closing(mask, selem=structure)
        mask = label(clear_border(mask))
        axes = 'YXZ'
    
    if image_data.dtype == np.uint16:
        mask = img_as_uint(mask)
    else:
        mask = img_as_ubyte(mask)

    imsave(result_object_location, mask, metadata={'axes': axes})


if __name__ == '__main__':
    params = {}
    run(params)
