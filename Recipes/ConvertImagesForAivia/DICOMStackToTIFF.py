import os
import sys
import numpy as np
from pydicom import dcmread
from skimage.io import imsave
from skimage.util import img_as_uint, img_as_ubyte


def dicom_to_tiff(dicom_directory, bit_depth='16', output_name='Converted'):
    """
    Converts a stack of DICOM files to a single 3D TIFF for easy loading into Aivia.
    
    The converted file will be saved in the same directory as the DICOM files.
        
    Requirements
    ------------
    numpy
    skimage
    pydicom (!Warning: it is not included in the virtual environment PythonVenvForAivia by default.
              You can use 'python -m pip install pydicom' manually to use this script)
    
    Parameters
    ----------
    dicom_directory : string
        Path to the directory containing your DICOM files.
    
    bit_depth : string
        Desired bit depth of the output file. Must be '16' or '8'.
    
    output_name : string
        What to name the output file. Note that you should not specify the TIFF extension.
    
    Returns
    -------
    string  
        Path to the 3D TIFF.
        
    """

    file_list = [f for f in os.listdir(dicom_directory) if 'dcm' in f.lower() or 'dicom' in f.lower()]
    example_dcm = dcmread(os.path.join(dicom_directory, file_list[0]))
    nx, ny = example_dcm.pixel_array.shape
    nz = len(file_list)
    rx, ry = example_dcm.PixelSpacing
    rz = example_dcm.SliceThickness

    print('Dataset properties:')
    print(f"XYZ dimensions: {nx}, {ny}, {nz}")
    print(f"XYZ Resolution: {rx}, {ry}, {rz}")

    if bit_depth == '16':
        array_data = np.empty(shape=(ny, nx, nz), dtype=np.uint16)
    else:
        array_data = np.empty(shape=(ny, nx, nz), dtype=np.uint8)

    sys.stdout.write('Converting: 0.00%')
    for d, dcmfile in enumerate(file_list):
        dcm_data = dcmread(os.path.join(dicom_directory, file_list[d]))
        if bit_depth == '16':
            array_data[:,:,d] = img_as_uint(dcm_data.pixel_array).T
        else:
            array_data[:,:,d] = img_as_ubyte(dcm_data.pixel_array).T
        if d%20 == 0:
            sys.stdout.write(f"\rConverting: {(float(d)/nz)*100:.2f}%")
            sys.stdout.flush()

    print('\nSaving 3D TIFF...')
    # Need to swap some axes so that third dimension is loaded into Aivia as Z
    imsave(os.path.join(dicom_directory, f"{output_name}.tiff"), np.swapaxes(array_data, 0, 2))
    print(f"3D TIFF saved to {output_name}.tiff")
    
    return os.path.join(dicom_directory, f"{output_name}.tiff")
