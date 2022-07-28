import os.path
import subprocess
import pathlib
from pathlib import Path
from shutil import copyfile
import sys
from PIL import Image, ImageDraw, ImageFont
from skimage.io import imread, imsave
import numpy as np
import textwrap

"""
This Aivia python recipe will create the required virtual environment for all recipes available
on our GitHub: https://github.com/AiviaCommunity/PythonForAivia.

Unzip the content of PythonVenvForAivia.zip in a folder WITHOUT admin access restrictions.
"""

# [INPUT Name:inputImagePath Type:string DisplayName:'Any 2D Image']
# [OUTPUT Name:outputImagePath Type:string DisplayName:'Image with text']
def run(params):

    env_dir = pathlib.Path(os.path.dirname(os.path.realpath(__file__))) / 'env'

    if not os.path.exists(env_dir):
        # create a virtual environment
        env_dir.mkdir(parents=False, exist_ok=True)
        subprocess.check_call([str(Path(sys.executable).parent / 'Scripts/virtualenv.exe'), f'{env_dir}'])
        
        # copy essential python packages(python39.zip) to virtual environment
        # see https://github.com/pypa/virtualenv/issues/1185
        if not os.path.exists(env_dir/'Scripts/python39.zip'):
            copyfile(Path(sys.executable).parent / 'python39.zip', env_dir/'Scripts/python39.zip')

        # install requirements
        pip_path = env_dir / 'Scripts' / 'pip.exe'
        requirement_dir = pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
        subprocess.check_call(
            [str(pip_path), 'install', '-r', str(requirement_dir/'requirements.txt')])
                    
    # Check if input image exists
    inputImagePath_ = params['inputImagePath']
    outputImagePath_ = params['outputImagePath']
    if not os.path.exists(inputImagePath_):
        raise ValueError('Error: {inputImagePath_} does not exist')

    # Get the path of the folder that contains this python script
    parentFolder = str(Path(__file__).parent)

    # Get the path of python executable in the virtual environment
    pythonExec_ = parentFolder + '\\env\\Scripts\\python.exe'

    # Log
    message = f'Python was installed here:\n{pythonExec_}'
    print(message)
    
    # Load image
    input_img = imread(inputImagePath_)

    # Write text
    output_img = add_text(input_img, message)
    
    imsave(outputImagePath_, output_img)
    

def add_text(input_img, raw_text):
    # defining sizes with wrapped text
    [height, width] = input_img.shape
    size_x = width // 2
    text = textwrap.fill(raw_text, width=size_x//6, replace_whitespace=False)        # Wrap text
    size_y = height // 8 + (height // 16) * text.count('\n')
    start_w = width // 2 - size_x // 2
    start_h = height // 2 - size_y // 2
    
    # Availability is platform dependent
    font = 'calibri'
    
    # Check length of text
    lines_list = text.split('\n')
    ref_line = max(lines_list, key=len)
    len_text = len(ref_line)
        
    # Create font
    font_size = size_x // len_text if size_x // len_text > 12 else 12
    pil_font = ImageFont.truetype(font + ".ttf", size=font_size, encoding="unic")
    text_width, text_height = pil_font.getsize(ref_line)

    # Create empty image to put text
    text_img = np.zeros_like(input_img)

    # create a blank canvas with extra space between lines
    canvas = Image.new('L', (size_x, size_y))

    # draw the text onto the canvas
    draw = ImageDraw.Draw(canvas)
    offset = ((size_x - text_width) // 2,
              (size_y - text_height * len(lines_list)) // 2)
    draw.text(offset, text, font=pil_font, fill=1)
    
    # Use max intensity as writing intensity
    txt_intensity = input_img.max() + 10 if input_img.max() + 10 < np.iinfo(input_img.dtype).max else np.iinfo(input_img.dtype).max
    
    # Convert the canvas into an array
    text_img_canvas = np.asarray(canvas) * txt_intensity
    
    # Use min intensity to create some background to text
    min_img_int = input_img.min()
    
    # Add some background to text                               (OPTIONAL, can be bypassed)
    text_img_canvas = np.where(text_img_canvas == 0, (txt_intensity - min_img_int) // 4 + min_img_int, text_img_canvas)
    
    # Put text array in image 
    text_img[start_h:start_h+size_y, start_w:start_w+size_x] = text_img_canvas
    output_array = np.maximum(input_img, text_img)
    
    return output_array


if __name__ == '__main__':
    params = {}
    params['inputImagePath'] = 'test_8b.tif'
    params['outputImagePath'] = 'testResult.tif'

    run(params)
