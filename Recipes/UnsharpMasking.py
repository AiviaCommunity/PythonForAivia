import os.path
from numpy import empty_like
from skimage.io import imread, imsave
from skimage.filters import unsharp_mask

# [INPUT Name:inputImagePath Type:string DisplayName:'Input Image']
# [INPUT Name:radius Type:double DisplayName:'Radius' Default:1.0 Min:0.0 Max:100.0]
# [INPUT Name:amount Type:double DisplayName:'Amount' Default:1.0 Min:0.0 Max:100.0]
# [OUTPUT Name:resultPath Type:string DisplayName:'Sharpened']
def run(params):
    image_location = params['inputImagePath']
    result_location = params['resultPath']
    radius = float(params['radius'])
    amount = float(params['amount'])
    if not os.path.exists(image_location):
        print(f'Error: {image_location} does not exist')
        return;
        
    image_data = imread(image_location)
    
    output_data = empty_like(image_data)
    
    output_data = unsharp_mask(image_data, radius=radius, amount=amount,
        multichannel=False, preserve_range=True).astype(image_data.dtype)

    imsave(result_location, output_data)


if __name__ == '__main__':
    params = {}
    params['inputImagePath'] = 'test.png'
    params['resultPath'] = 'testResult.png'
    params['radius'] = 1.0
    params['amount'] = 1.0
    
    run(params)

# TODO: Scale better to unsigned integers. W/O this the output is useless
# TODO: Double parameters can't be negative?
# TODO: Implement in 3D

# CHANGELOG
# v0.01 TL - Original script by Trevor Lancon (trevorl@drvtechnologies.com)
#