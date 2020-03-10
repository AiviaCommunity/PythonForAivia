import os.path
from numpy import empty_like
from skimage.io import imread, imsave
from skimage.exposure import adjust_gamma

"""
See: https://scikit-image.org/docs/dev/api/skimage.exposure.html#skimage.exposure.adjust_gamma

Adjusts gamma of the input channel pixelwise according to O = I**gamma.
"""

# [INPUT Name:inputImagePath Type:string DisplayName:'Input Image']
# [INPUT Name:gamma Type:double DisplayName:'Gamma' Default:0.75 Min:0.0 Max:2.0]
# [OUTPUT Name:resultPath Type:string DisplayName:'Gamma Adjusted']
def run(params):
    image_location = params['inputImagePath']
    result_location = params['resultPath']
    gamma = float(params['gamma'])
    if not os.path.exists(image_location):
        print(f'Error: {image_location} does not exist')
        return;
        
    image_data = imread(image_location)
    
    output_data = empty_like(image_data)
    
    output_data = adjust_gamma(image_data, gamma, 1)

    imsave(result_location, output_data)


if __name__ == '__main__':
    params = {}
    params['inputImagePath'] = 'test.png'
    params['resultPath'] = 'testResult.png'
    params['gamma'] = 1.0;
    
    run(params)

# TODO: why doesn't gamma default to 0.75? truncates to 0

# CHANGELOG
# v1.00 TL - Original script by Trevor Lancon (trevorl@drvtechnologies.com)
#