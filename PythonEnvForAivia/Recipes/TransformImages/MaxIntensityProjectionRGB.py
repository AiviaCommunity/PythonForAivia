import os.path
import numpy as np
from tifffile import imread, imwrite
import shlex, subprocess
import sys
import re

DEFAULT_OUTPUT_FOLDER = r''

"""
Performs a maximum intensity projection through Z for a single channel. 
Repeats the operation for the two other channels of the RGB image.

Works only in 3D (not 3D+t yet).

Requirements
------------
numpy (comes with Aivia installer)
scikit-image (comes with Aivia installer)

Parameters
----------
Input channels:
    3 input channels to use for the projection.

Returns
-------
New channels in original 3D image:
    Returns a binary map of the location of max values detected in volume.

New 3-channel 2D image:
    Opens Aivia (again) to display the 2D projection as a new image.

"""


# [INPUT Name:inputRedPath Type:string DisplayName:'Red channel']
# [INPUT Name:inputGreenPath Type:string DisplayName:'Green channel']
# [INPUT Name:inputBluePath Type:string DisplayName:'Blue channel']
# [OUTPUT Name:resultPath Type:string DisplayName:'Empty channel']
def run(params):
    image_location = []
    image_location.append(params['inputRedPath'])
    image_location.append(params['inputGreenPath'])
    image_location.append(params['inputBluePath'])
    result_location = params['resultPath']

    t_count = int(params['TCount'])
    pixel_cal_tmp = params['Calibration']
    pixel_cal = pixel_cal_tmp[6:].split(', ')           # Expects calibration with 'XYZT: ' in front

    # Getting XY and Z calibration values                # Expecting only 'Micrometers' in this code
    XY_cal = float(pixel_cal[0].split(' ')[0])
    Z_cal = float(pixel_cal[2].split(' ')[0])
    T_cal = float(pixel_cal[3].split(' ')[0])

    for c in range(0, 3):
        if not os.path.exists(image_location[c]):
            sys.exit(f"Error: {image_location[c]} does not exist")
    
    first_ch = imread(image_location[0])
    input_dims = np.asarray(first_ch.shape)
    print('-- Input dimensions (expected Z, Y, X): ', input_dims, ' --')
    
    new_input_dims = np.insert(input_dims, 0, 3)
    image_data = np.zeros(new_input_dims).astype(first_ch.dtype)
    print('-- Combined input dimensions (expected C, Z, Y, X): ', new_input_dims, ' --')
    bitdepth = 'Uint8' if first_ch.dtype == np.uint8 else 'Uint16'
    
    for c in range(0, 3):
        image_data[c] = imread(image_location[c])
    
    # Checking image is not 2D or 2D+t
    if input_dims.size == 2 or (input_dims.size == 3 and t_count > 1):
        sys.exit('Error: Maximum intensity projection cannot be applied to 2D images.')
    
    output_data = np.empty_like(first_ch)
    proj_output = np.zeros([3, input_dims[1], input_dims[2]]).astype(first_ch.dtype)       # Z and T dims are needed to be read by Aivia
    
    for c in range(0, 3):
        if t_count == 1:     # (image is not 3D+t)
            # Generate 2D max projection for each channel
            proj_output[2-c, :, :] = np.amax(image_data[c], axis=0)
        else:
            sys.exit(f"Warning: Maximum intensity projection was not programmed for 3D+t images yet.")

    # Adding Z and T dummy dimensions in array
    proj_output = proj_output.reshape(3, 1, 1, input_dims[1], input_dims[2])

    # Set output metadata
    metadata_dict = {
        'DimensionOrder': 'XYZTC', 'Dimensions': [input_dims[2], input_dims[1], 1, 1, 3],
        'PixelSizeX': XY_cal, 'PixelSizeZ': Z_cal, 'TimeStep': T_cal,  # 'ChannelDescription': '',
        'BitDepth': bitdepth,
        'ChannelNames': ['Ch1', 'Ch2', 'Ch3']
    }

    # Create metadata XML string compatible with Aivia
    out_metadata = create_aivia_tif_xml_metadata(metadata_dict)
    
    # Saving 3 channel image as single tif
    if 'fileOutputPath_2' in params.keys():     # test mode
        temp_location = params['fileOutputPath_2']
    else:
        # Evaluate possible output in a user-defined folder
        if DEFAULT_OUTPUT_FOLDER:
            output_folder = DEFAULT_OUTPUT_FOLDER
        else:
            output_folder = os.path.dirname(result_location)

        # Attempt to collect name of current image (+bitdepth)
        out_path = ''
        if params.get("RawImageMetadata"):
            match = re.search(r'^(.*?)\s\(Dims\s.*?\|\sCalibration', params['RawImageMetadata'])
            img_name = ''
            if match is not None:
                img_name = match.groups()[0]
                output_name = f"{img_name}_MaxProj.tif"

                out_path = os.path.join(output_folder, output_name)

        if not out_path:
            out_path = result_location.replace('.tif', 'tmp.tif')
        
        # Dummy save to avoid error in Aivia
        imwrite(result_location, output_data)

    # Saving real output
    print('-- Output dimensions (expected C, T, Z, Y, X): ', proj_output.shape, ' --')
    imwrite(out_path, proj_output, metadata=None, description=out_metadata, bigtiff=True)
  
    aivia_path = params['CallingExecutable'].replace('.dll', '.exe')
    # Added for handling testing without opening aivia
    if aivia_path == "None":
        return
    if not os.path.exists(aivia_path):
        print(f"Error: {aivia_path} does not exist")
        return
    # Run external program
    cmdLine = 'start \"\" \"'+ aivia_path +'\" \"'+ out_path +'\"'
    
    args = shlex.split(cmdLine)
    subprocess.run(args, shell=True)


# Function to create the XML metadata that can be pushed to the ImageDescription or ome_metadata tif tags
def create_aivia_tif_xml_metadata(meta_dict):
    # Version 1.40
    # Expected metadata dictionary:
    # ['DimensionOrder'] = str, ['Dimensions'] = list(int), ['PixelSizeX'], ['BitDepth'] = 'Uint16'
    # ['ChannelNames'] = list, ['ChannelColors'] = list, ['ChannelExWv'] = list(int) of excitation wavelengths,
    # ['ChannelEmWv'] = list(int) of emission wavelengths which is the one used in the end
    # Optional: Need one of 'ChannelColors', 'ChannelExWv', or , 'ChannelEmWv' or nothing to fall back on white
    # ['PixelSizeZ'], ['TimeStep'] in seconds, ['ChannelDescription'] = str

    # Init of values which are hard coded in the xml result. See line 14234 in tifffile.py
    dimorder = meta_dict['DimensionOrder']  # default = XYZTC
    ind_ref = 1  # incremented index for various entities below
    ifd = '0'  # Only for TiffData id
    samples = '1'
    res_unit = 'um'  # XYZ unit
    t_res_unit = "s"  # Time unit
    ch_emwv = [40] * int(meta_dict['Dimensions'][-1])  # Default value to add to ExWv if EmWv is missing
    ch_exwv = ch_emwv.copy()
    wv_unit = 'nm'  # Wavelength unit
    planes = ''  # Not used at the moment (would store Z position of indiv planes)
    # f'<Plane TheC="{c}" TheZ="{z}" TheT="{t}"{attributes}/>'
    #                     attributes being:
    #                     p,
    #                     'DeltaTUnit',
    #                     'ExposureTime',
    #                     'ExposureTimeUnit',
    #                     'PositionX',
    #                     'PositionXUnit',
    #                     'PositionY',
    #                     'PositionYUnit',
    #                     'PositionZ',
    #                     'PositionZUnit',
    declaration = '<?xml version="1.0" encoding="UTF-8"?>'
    schema = 'http://www.openmicroscopy.org/Schemas/OME/2016-06'

    def add_channel(ind_ch, c, chname, color, description, emwv, exvw, wvunit):
        attributes = (
            f' Name="{chname}"'
            f' Color="{color}"'
            f' Description="{description}"'
            f' EmissionWavelength="{emwv}"'
            f' EmissionWavelengthUnit="{wvunit}"'
            f' ExcitationWavelength="{exvw}"'
            f' ExcitationWavelengthUnit="{wvunit}"'
        )
        return (
            f'<Channel ID="Channel:{c + ind_ch}"'
            f' SamplesPerPixel="{samples}"'
            f'{attributes}>'
            '</Channel>'
        )

    def add_image(ind_img, dtype, channels_str, planecount, xy_resolution, z_resolution, resolution_unit,
                  t_resolution, t_resolution_unit, zcount, tcount, dimorder):
        if any([z_resolution == v for v in ['', 0]]):
            z_resolution = 1
        if any([t_resolution == v for v in ['', 0]]):
            t_resolution = 1

        attributes = (
            f' PhysicalSizeX="{xy_resolution}"'
            f' PhysicalSizeXUnit="{resolution_unit}"'
            f' PhysicalSizeY="{xy_resolution}"'
            f' PhysicalSizeYUnit="{resolution_unit}"'
        )
        if zcount > 1:
            attributes += (
                f' PhysicalSizeZ="{z_resolution}"'
                f' PhysicalSizeZUnit="{resolution_unit}"'
            )
        if tcount > 1:
            attributes += (
                f' TimeIncrement="{t_resolution}"'
                f' TimeIncrementUnit="{t_resolution_unit}"'
            )

        return (
            f'<Image ID="Image:{ind_img}" Name="Image {ind_img}">'
            f'<Pixels ID="Pixels:{ind_img + 1}"'
            f' DimensionOrder="{dimorder}"'
            f' Type="{dtype}"'
            f'{sizes}'  # space at the beginning provided with 'sizes'
            f'{attributes}>'  # space at the beginning provided with 'attributes'
            f'{channels_str}'
            f'<TiffData IFD="{ifd}" PlaneCount="{planecount}"/>'
            f'{planes}'
            f'</Pixels>'
            f'</Image>'
        )

    dimsizes = meta_dict['Dimensions']

    # Adding other missing dimensions if this is the case
    if not 'Z' in dimorder:
        dimsizes += [int('1')]
        dimorder += 'Z'
        z_count = 1
    else:
        z_count = int(dimsizes[dimorder.index('Z')])

    if not 'T' in dimorder:
        dimsizes += [int('1')]
        dimorder += 'T'
        t_count = 1
    else:
        t_count = int(dimsizes[dimorder.index('T')])

    ch_names = meta_dict['ChannelNames']

    if 'ChannelColors' in meta_dict.keys():
        ch_colors = meta_dict['ChannelColors']
    else:
        ex_to_em = ch_emwv[0]
        if 'ChannelEmWv' in meta_dict.keys():
            ch_emwv = meta_dict['ChannelEmWv']
            ch_exwv = [c - ex_to_em if c > ex_to_em else 0 for c in ch_emwv]  # Arbitrary subtraction
        elif 'ChannelExWv' in meta_dict.keys():
            ch_exwv = meta_dict['ChannelExWv']
            ch_emwv = [c + ex_to_em for c in ch_exwv]  # Arbitrary addition
        else:  # Default to white
            print('Channel color not detected. Falling back on grays for all channels...')

        ch_colors = [convert_rgb_to_byte(wavelength_to_RGB(w)) for w in ch_emwv]

    ch_description = [''] * len(ch_names)
    if 'ChannelDescription' in meta_dict.keys():
        ch_description = meta_dict['ChannelDescription']

    xy_res = meta_dict['PixelSizeX']
    if 'PixelSizeZ' in meta_dict.keys():
        z_res = meta_dict['PixelSizeZ']
    else:
        z_res = 1 if 'Z' in meta_dict['Dimensions'] else ''
    if 'TimeStep' in meta_dict.keys():
        t_res = meta_dict['TimeStep']
    else:
        t_res = 1 if 'T' in meta_dict['Dimensions'] else ''

    # Get the first character for bit depth to be uppercase
    bit_depth = str(meta_dict['BitDepth'])[0].upper() + meta_dict['BitDepth'][1:]

    # Define string for dimension sizes
    sizes = ''.join(
        f' Size{ax}="{size}"' for ax, size in zip(dimorder, dimsizes)
    )

    # Define string for channels
    ch_count = int(dimsizes[dimorder.index('C')])
    ch_str = ''.join(
        [add_channel(ind_ref + 2, c, ch_names[c], ch_colors[c], ch_description[c], ch_emwv[c], ch_exwv[c], wv_unit)
         for c in range(ch_count)])  # ind_ref + 2 because of Image ID and Pixels ID before

    # Define larger string for images
    plane_count = z_count * t_count * ch_count
    images = add_image(ind_ref, bit_depth, ch_str, plane_count, xy_res, z_res, res_unit, t_res, t_res_unit,
                       z_count, t_count, dimorder)

    xml_str = (
        f'{declaration}'
        f'<OME xmlns="{schema}"'
        f' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
        f' xsi:schemaLocation="{schema} {schema}/ome.xsd"'
        f' Creator="Aivia Python Script/Patrice Mascalchi">'
        f'{images}'
        f'</OME>'
    )

    return xml_str


def convert_rgb_to_byte(rgb_list):
    b = rgb_list[0] << 24 | rgb_list[1] << 16 | rgb_list[2] << 8 | 0xff  # Aivia 15.0+
    # Convert to signed if necessary
    b = b - 2 ** 32 if b >= 2 ** 31 else b

    return b


# Expected to be emission wavelength as input
def wavelength_to_RGB(wavelength):
    # Version 1.30
    # Taken from Earl F.Glynn's web page: "http://www.efg2.com/Lab/ScienceAndEngineering/Spectra.htm"
    # Modified the version to have pink after 650 nm and to have red sooner (more adapted to usual false colors)
    gamma = 0.80
    int_max = 255

    # Defining color ranges with following limits. 0 = black, 0 < l1 OR > l8 = white
    # l1=pink, l2=blue, l3=cyan, l4=green, l5=yellow, l6=red, l7=red, l8=pink
    # l1, l2, l3, l4, l5, l6, l7 = 380, 440, 490, 510, 580, 645, 670, 781
    l1, l2, l3, l4, l5, l6, l7, l8 = 380, 440, 490, 510, 570, 600, 660, 781

    if wavelength == 0:
        Red = 0.0
        Green = 0.0
        Blue = 0.0
    elif l1 <= wavelength < l2:
        Red = - (wavelength - l2) / (l2 - l1)
        Green = 0.0
        Blue = 1.0
    elif l2 <= wavelength < l3:
        Red = 0.0
        Green = (wavelength - l2) / (l3 - l2)
        Blue = 1.0
    elif l3 <= wavelength < l4:
        Red = 0.0
        Green = 1.0
        Blue = - (wavelength - l4) / (l4 - l3)
    elif l4 <= wavelength < l5:
        Red = (wavelength - l4) / (l5 - l4)
        Green = 1.0
        Blue = 0.0
    elif l5 <= wavelength < l6:
        Red = 1.0
        Green = - (wavelength - l6) / (l6 - l5)
        Blue = 0.0
    elif l6 <= wavelength < l7:
        Red = 1.0
        Green = 0.0
        Blue = 0.0
    elif l7 <= wavelength < l8:
        Red = 1.0
        Green = 0.0
        Blue = 1.0
    else:
        Red = 1.0
        Green = 1.0
        Blue = 1.0

    rgb = [0] * 3

    # Don't want 0^x = 1 for x != 0
    rgb[0] = round(int_max * pow(Red, gamma)) if Red > 0.0 else 0
    rgb[1] = round(int_max * pow(Green, gamma)) if Green > 0.0 else 0
    rgb[2] = round(int_max * pow(Blue, gamma)) if Blue > 0.0 else 0

    return rgb


if __name__ == '__main__':
    params = {'inputRedPath': r'D:\PythonCode\_tests\XYZ_50x50x51_1ch_8bit_binarymask_synthetic_A9.0.aivia.tif',
              'inputGreenPath': r'D:\PythonCode\_tests\XYZ_50x50x51_1ch_8bit_binarymask_synthetic_A9.0.aivia.tif',
              'inputBluePath': r'D:\PythonCode\_tests\XYZ_50x50x51_1ch_8bit_binarymask_synthetic_A9.0.aivia.tif',
              'resultPath': r'D:\PythonCode\_tests\dummy.aivia.tif',
              'fileOutputPath_2': r'D:\PythonCode\_tests\3DMaxMap.tif',
              'ZCount': 51, 'TCount': 1,
              "Calibration": "XYZT: 1 Micrometers, 1 Micrometers, 1 Micrometers, 1 Default",
              "RawImageMetadata": "Test (Dims 50×50×51×1×1 | Precision 8 | Calibration 1 Micrometers..."
    }
    
    run(params)

# CHANGELOG
# v1.01: - Added an extra key in params for Unit test output
# v1.10: - Changed output format to be as GT during tests (CYX order)
# v1.11: - params['CallingExecutable'] points to a dll file instead of exe in Aivia 16+
# v1.20: - Change in way to save the file, to avoid losing pixel calibration
