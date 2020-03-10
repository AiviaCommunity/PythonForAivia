import os.path
import numpy as np
from skimage.io import imread, imsave

"""
Computes the luminance of an RGB image and returns that as a new channel.

Useful when images are saved as RGB (e.g. histopathology, photographs, etc.)
and the user desires to apply a recipe or pixel classifier to only one
channel, but wishes to retain the maximum amount of information from each.

The luminance has a 30% contribution from the red channel, 59%
contribution from the green channel, and 11% contribution from the
blue channel.
"""

# [INPUT Name:red_c Type:string DisplayName:'Red Channel']
# [INPUT Name:blue_c Type:string DisplayName:'Blue Channel']
# [INPUT Name:green_c Type:string DisplayName:'Green Channel']
# [OUTPUT Name:gray_c Type:string DisplayName:'Luminance']
def run(params):
    red_c = params['red_c']
    blue_c = params['blue_c']
    green_c = params['green_c']
    gray_c = params['gray_c']
    if not os.path.exists(red_c):
        print(f'Error: {red_c} does not exist')
        return;
    if not os.path.exists(blue_c):
        print(f'Error: {blue_c} does not exist')
        return;
    if not os.path.exists(green_c):
        print(f'Error: {green_c} does not exist')
        return;
        
    red_data = imread(red_c)
    blue_data = imread(blue_c)
    green_data = imread(green_c)
    
    gray_data = np.empty_like(red_data)
    
    print(f'Red: {red_data.nbytes}')
    print(f'Blue: {blue_data.nbytes}')
    print(f'Green: {green_data.nbytes}')
    print(f'Gray: {gray_data.nbytes}')
    
    gray_data = (0.3*red_data + 0.59*green_data + 0.11*blue_data).astype(red_data.dtype)

    imsave(gray_c, gray_data)


if __name__ == '__main__':
    params = {}
    params['red_c'] = 'test.png'
    params['blue_c'] = 'test.png'
    params['green_c'] = 'test.png'
    params['gray_c'] = 'testResult.png';
    
    run(params)

# CHANGELOG
# v1.00 TL - Original script by Trevor Lancon (trevorl@drvtechnologies.com)
#