import os.path
import numpy as np
from skimage.io import imread, imsave
from skimage.exposure import adjust_sigmoid, rescale_intensity

np.seterr(divide='ignore', invalid='ignore')

"""
See: https://scikit-image.org/docs/dev/api/skimage.exposure.html#skimage.exposure.adjust_sigmoid

Performs a Sigmoid contrast adjustment. Think of the "cutoff" being a number 0 - 1,
representing a percentile of the histogram, above and below which the histogram is
"squished" to its bounds. The gain controls the amount of "squishing".

In mathematical terms, O = 1 / (1 + exp*(gain*(cutoff - I))).
"""

# [INPUT Name:inputImagePath Type:string DisplayName:'Input Image']
# [INPUT Name:cutoff Type:double DisplayName:'Cutoff (%)' Default:0.5 Min:0.0 Max:1.0]
# [INPUT Name:gain Type:double DisplayName:'Gain' Default:10.0 Min:0.0 Max:20.0]
# [OUTPUT Name:resultPath Type:string DisplayName:'Sigmoid']
def run(params):
    image_location = params['inputImagePath']
    result_location = params['resultPath']
    cutoff = float(params['cutoff'])
    gain = float(params['gain'])
    if not os.path.exists(image_location):
        print(f'Error: {image_location} does not exist')
        return;
        
    image_data = imread(image_location)
    
    output_data = np.empty_like(image_data)
    
    sigmoid_image = adjust_sigmoid(image_data, cutoff=cutoff, gain=gain, inv=False)
    
    output_data = rescale_intensity(sigmoid_image, out_range='uint8').astype(image_data.dtype)

    imsave(result_location, output_data)


if __name__ == '__main__':
    params = {}
    params['inputImagePath'] = 'test.png'
    params['resultPath'] = 'testResult.png'
    params['cutoff'] = 0.5
    params['gain'] = 10.0
    
    run(params)

# CHANGELOG
# v1.00 TL - Original script by Trevor Lancon (trevorl@drvtechnologies.com)
#