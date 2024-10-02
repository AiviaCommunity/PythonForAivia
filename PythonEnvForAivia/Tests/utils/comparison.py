import tifffile as tif
import numpy as np


def isIdentical(image_path1, image_path2):
    """
    Compare two TIFF images to check if they are equal in every value.
    
    Args:
    image_path1 (str): Path to the first TIFF image
    image_path2 (str): Path to the second TIFF image
    
    Returns:
    bool: True if images are identical, False otherwise
    """
    with tif.TiffFile(image_path1) as tif1, tif.TiffFile(image_path2) as tif2:
        # Read the image data
        data1 = tif1.asarray()
        data2 = tif2.asarray()
        
        # Compare the arrays
        return np.array_equal(data1, data2)