import tifffile as tif
import numpy as np
import json
import os


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



def sort_json(data):
    if isinstance(data, dict):
        return {k: sort_json(v) for k, v in sorted(data.items())}
    elif isinstance(data, list):
        return sorted(sort_json(x) for x in data)
    else:
        return data


def isJsonIdentical(json_path1, json_path2):
    with open(json_path1) as f1, open(json_path2) as f2:
        json_data1 = json.load(f1)
        json_data2 = json.load(f2)
    if json_data1 == json_data2:
        return True
    return False


if __name__ == "__main__":
    fd = r'..\TransformImages\MaxIntensityProjectionRGB'
    p1 = os.path.join(fd, 'GT_Test_8bit_ZYX_Cells3D_ch2_nuc_processed.tif')
    p2 = os.path.join(fd, 'OUT_Test_8bit_ZYX_Cells3D_ch2_nuc_processed.tif')

    result = isIdentical(p1, p2)
