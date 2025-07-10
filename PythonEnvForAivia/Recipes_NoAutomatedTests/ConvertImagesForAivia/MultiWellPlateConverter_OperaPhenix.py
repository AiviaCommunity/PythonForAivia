# -------- Activate virtual environment -------------------------
import os
import ctypes
import sys
from pathlib import Path


def search_activation_path():
    for i in range(5):
        final_path = str(Path(__file__).parents[i]) + '\\env\\Scripts\\activate_this.py'
        if os.path.exists(final_path):
            return final_path
    return ''


activate_path = search_activation_path()

if os.path.exists(activate_path):
    exec(open(activate_path).read(), {'__file__': activate_path})
    print(f'Aivia virtual environment activated\nUsing python: {activate_path}')
else:
    error_mess = f'Error: {activate_path} was not found.\n\nPlease check that:\n' \
                 f'   1/ The \'FirstTimeSetup.py\' script was already run in Aivia,\n' \
                 f'   2/ The current python recipe is in one of the "\\PythonEnvForAivia\\" subfolders.'
    ctypes.windll.user32.MessageBoxW(0, error_mess, 'Error', 0)
    sys.exit(error_mess)
# ---------------------------------------------------------------

import wx
import numpy as np
import concurrent.futures
import re
import time
from xml.dom import pulldom     # TODO: speed up with xml.etree.ElementTree as ET ???
from tifffile import imread, imwrite, TiffFile
from magicgui import magicgui

# Folder to quickly run the script on all Excel files in it
DEFAULT_FILE = r''

# File patterns vary depending on the acquisition system and version
# .* at the beginning for the file path. All in brackets for image name comparison.
# Example: r04c02f01p01-ch01t01.tiff
file_patterns_info = {'r01c01f01p01-ch01t01.tiff': {
    'pattern': r'.*(r)(\d{2})(c)(\d{2})(f)(\d{2})(p)(\d{2})(-ch)(\d{2})(t)(\d{2})\.tiff',
    'constant_parts': [1, 2, 3, 4, 5, 6],  # To detect files from the same stack. Starts at index = 1!!
    'metadata_parts': {'Well row': 2,
                       'Well column': 4,
                       'Fov': 6,
                       'Tp': 12,
                       'Z': 8,
                       'Ch': 10,
                       }
    },
            'r01c01f01p01-ch1sk1fk1fl1.tiff': {
    'pattern': r'.*(r)(\d{2})(c)(\d{2})(f)(\d{2})(p)(\d{2})(-ch)(\d{1,2})(sk)(\d{1,2})(fk1fl1)\.tiff',
    'constant_parts': [1, 2, 3, 4, 5, 6],  # To detect files from the same stack. Starts at index = 1!!
    'metadata_parts': {'Well row': 2,
                       'Well column': 4,
                       'Fov': 6,
                       'Tp': 12,
                       'Z': 8,
                       'Ch': 10,
                       }
    }
}

image_extension = '.tiff'

# Plate layouts, returning: [number of wells in x, in y, start_x, start_y, well_dist_x, well_dist_y,
#                           well_size_x, well_size_y], name, plate ID
# WARNING: start_x is the center of the well, not the corner. A factor of 1000 is applied from the doc to these layouts.
LAYOUTS = {
    '6': [[3, 2, 24000, 22000, 40000, 40000, 36000, 36000], '6 Wellplate Nucleon Surface',       # Nunclon model
          'b3c04cb7-a10d-471a-b2cb-429d0e139244'],
    '8': [[4, 2, 11300, 7150, 11580, 11580, 10500, 10500], 'LabTek 8 Chamber',
          'eca369bd-ea6a-406b-94f6-599f27ec4ac0'],
    '24': [[6, 4, 15130, 13490, 19500, 19500, 15660, 15660], '24 Wellplate Type CELLSTAR',
           'a06df3e5-a9f2-49c3-b74f-61fa6c3079ee'],
    '96': [[12, 8, 14380, 11240, 9000, 9000, 6580, 6580], '96 Wellplate Type Sensoplate',
           '6c3b16e9-8361-4b95-86a7-61b0cb1e90bc'],
    '384': [[24, 26, 12130, 8990, 4500, 4500, 3300, 3300], '384 Wellplate Type Sensoplate',
            'd9bba488-59bc-429b-8b28-818aacf38a12']
    }
LAYOUTS_WELL_LIST = list(LAYOUTS.keys())

# Output file fixed parts
PREFIX = r'{"serializedVersion":0,"minSupportedVersion":0,"Plates":[{"Sectors":['
WELL_PREFIX = '{"Fields":['
TAGS = ['{"HintPath":', ',"FilePath":', ',"Name":', ',"PositionX":', ',"PositionY":', ',"HierarchyPath":']
WELL_TAGS = ['}],"Label":', ',"Tags":{', '}}']  # needs a comma between fields == wells
SUFFIX = ['],"FilePath":', ',"HintPath":',
          ',"VesselName":', ',"VesselId":', ',"Label":', ',"AdjustmentX":', ',"AdjustmentY":', '}]}']

"""
Creates an .aiviaexperiment file from a metadata file ("index.xml") and a folder of tif files (same location) from an 
Opera Phenix equipment (Harmony v6, software version = Python NGen 5.1.2167.302/5.2.2180.259).
Testing set does not contain timepoints so script was built for 3D + ch mainly.
Metadata file contains: well plate format, image size, channel names and em wv, xy resolution, z positions and 
relative xy positions.
Automated false color is calculated from the wavelength.

Requirements
------------
wxPython
tifffile

Parameters
----------
n.a.

Returns
-------
.aiviaexperiment file to drag & drop in Aivia.

"""


# [INPUT Name:inputPath Type:string DisplayName:'Any channel']
# [OUTPUT Name:resultPath Type:string DisplayName:'Dummy to delete']
def run(params):
    global DEFAULT_FILE, LAYOUTS, LAYOUTS_WELL_LIST, PREFIX, WELL_PREFIX, TAGS, WELL_TAGS, SUFFIX

    sp = os.path.sep

    if not DEFAULT_FILE:
        print('Starting wxPython app')
        app = wx.App()
        frame = wx.Frame(None, -1, 'Folder picker')
        metadata_file_p = pick_file(frame)  # To select metadata file
    else:
        metadata_file_p = DEFAULT_FILE

    input_folder = os.path.dirname(metadata_file_p)
    input_files = os.listdir(input_folder)

    # Select subfolders containing images
    img_subfolders = [os.path.join(input_folder, f) for f in input_files if (
            os.path.isdir(os.path.join(input_folder, f)) and not f.startswith('Converted for Aivia')
    )]

    if not img_subfolders:
        image_files_eval = [f for f in os.listdir(input_folder) if f.endswith(image_extension)]
        if len(image_files_eval) < 5:
            mess = f'{image_extension} image subfolder or images in the same folder are expected but were not found. ' \
                   f'Cancelling script.'
            concurrent.futures.ThreadPoolExecutor().submit(Mbox, 'Process aborted', mess, 0)
            sys.exit(mess)  # for log
        else:
            img_subfolders = [input_folder]
            print(f'Image subfolder was not found, but {image_extension} files were found in the same folder')

    print('Detected multiwell plate file: {}'.format(metadata_file_p))  # for log

    # Other parameter selection
    file_pattern_choice, flip_img_X, flip_img_Y, do_max_proj = param_gui()
    file_pattern_info = file_patterns_info[file_pattern_choice]

    # Collect plate info
    # XY relative position is stored with the Well and FOV number. Image size is [w, h]
    t_xml_read = time.perf_counter()
    image_metadata = {}
    (n_wells, image_metadata['Image size'], image_metadata['XY resolution'], image_metadata['PixelSizeZ'],
     image_metadata['TimeStep'], image_metadata['ChannelNames'], image_metadata['ChannelEmWv'],
     image_metadata['XY relative positions'], image_metadata['BitDepth']) = read_plate_info(metadata_file_p)

    print('XML reading was done in {:d} seconds'.format(round(time.perf_counter() - t_xml_read)))

    # Define image file list
    image_files = []
    for img_subfolder in img_subfolders:
        image_files += [img_subfolder + sp + f for f in os.listdir(img_subfolder) if f.endswith(image_extension)]

    # Define main output folder
    output_folder = input_folder + sp + 'Converted for Aivia'
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    # Init in case there is no combination of individual files
    # --------------------------------------------------------------------------------------------------------------
    # Combine files as channels are saved independently
    combine_files = True  # Used for link between final image names and metadata (position, etc.)  # TODO: Useful, no position in metadata?

    # File pattern recognition
    # .* at the beginning for the file path. All in brackets for image name comparison.
    # Example: r04c02f01p01-ch01t01.tiff
    pattern = file_pattern_info['pattern']

    constant_parts = file_pattern_info['constant_parts']  # for the same stack. Starts at index = 1!!
    # IDs in the tif metadata (in ImageDescription) and positions in pattern for FOV location info
    metadata_parts = file_pattern_info['metadata_parts']

    list_image_info = reconstruct_multidim_images(input_folder, file_pattern_choice, image_files, pattern,
                                                  constant_parts, metadata_parts, image_metadata, output_folder,
                                                  flip_img_X, flip_img_Y, do_max_proj)
    # --------------------------------------------------------------------------------------------------------------

    # replace_str = {' - ': '---', ' ': '-', '(': '', ')': ''}          # Kept here for potential future use

    # Auto choice of the layout, returning
    # [number of wells in x, in y, start_x, start_y, well_dist_x, well_dist_y, well_size_x, well_size_y]
    plate_box_info = LAYOUTS[n_wells][0]
    plate_name = LAYOUTS[n_wells][1]
    plate_id = LAYOUTS[n_wells][2]

    # Get the coordinates of the center of wells [y, x]
    well_centers = well_coord(plate_box_info)

    # Define well XY indexes
    n_well_y = int(plate_box_info[1])
    n_well_x = int(plate_box_info[0])
    well_indexes_tmp = np.mgrid[1:n_well_y + 1, 1:n_well_x + 1]
    well_indexes = np.transpose(well_indexes_tmp.reshape((2, n_well_x * n_well_y))).tolist()

    # Init output file
    output_file = open(output_folder + sp + os.path.basename(os.path.dirname(input_folder)) + '.aiviaexperiment', 'w+')
    output_file.write(str(PREFIX))

    # Init grouping of images per well
    well_name = ''
    well_name_ref = 'A0'
    i = 0  # to count number of images in the same well

    for img_info in list_image_info:
        # Check well name
        well_lett = img_info['Well row']
        well_numb = str(img_info['Well column'])
        well_name = well_lett + well_numb

        if well_name != well_name_ref:  # start a new well
            # End previous well if one was already existing
            if well_name_ref != 'A0':
                # Write junction between different wells
                well_tag_entries = ['"' + well_name + '"', '', '']
                str_to_write = ''.join([x + str(y) for (x, y) in zip(WELL_TAGS, well_tag_entries)])
                output_file.write(str_to_write)

                # Put a comma between wells
                output_file.write(',')

            # Init well block in output file
            output_file.write(str(WELL_PREFIX))

            well_name_ref = well_name
            i = 1

        else:  # same well, new image
            # Write junction between different images
            output_file.write('},')
            i += 1

        fov = int(img_info['Fov'])

        # Write coordinates and image path in final file
        img_name = img_info['Filename']
        w_index = well_indexes.index([int(ord(img_info['Well row']) - 64), int(img_info['Well column'])])
        w_centers = well_centers[:, w_index]
        [img_offset_x, img_offset_y] = img_info['XY relative position']  # 0 is X, 1 is Y

        # Final fov positions calculated by moving image coordinates from center to top-left
        img_x = w_centers[1] + float(img_offset_x) - (float(img_info['Width']) / 2 * img_info['XY resolution'])
        img_y = w_centers[0] + float(img_offset_y) - (float(img_info['Height']) / 2 * img_info['XY resolution'])

        hierarchy = '["{}","{}","R{}"]'.format(well_lett, well_numb, i)

        full_img_path = output_folder + sp + img_name

        tag_entries = ['"' + img_name + '"',
                       '"' + full_img_path.replace('\\', '\\\\') + '"',
                       '"' + img_name + '"', img_x, img_y, hierarchy]
        str_to_write = ''.join([x + str(y) for (x, y) in zip(TAGS, tag_entries)])
        output_file.write(str_to_write)

    # Write suffix for last well
    well_tag_entries = ['"' + well_name + '"', '', '']
    str_to_write = ''.join([x + str(y) for (x, y) in zip(WELL_TAGS, well_tag_entries)])
    output_file.write(str_to_write)

    # Closing the output file after writing the suffix part
    # suffix_entries = ['"'+(input_folder + sp + group_list[0][0]).replace('\\', '\\\\')+'"', '"'+group_list[0][0]+'"',
    #                   '"'+plate_name+'"', '"'+plate_id+'"', '""', '0.0', '0.0', '']
    suffix_entries = ['""', '""',
                      '"' + plate_name + '"', '"' + plate_id + '"', '""', '0.0', '0.0', '']
    str_to_write = ''.join([x + str(y) for (x, y) in zip(SUFFIX, suffix_entries)])
    output_file.write(str_to_write)
    output_file.close()

    mess = 'The experiment file was saved as:\n{}'.format(output_file.name)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(Mbox, 'Process completed', mess, 0)
    print(mess)  # for log

    # Opening the output folder in Windows
    os.startfile(output_folder)


def read_plate_info(xml_data_path):
    # The following regex extracts all info depending on the file format.
    # Output: n_wells, image_size, image_metadata['XY resolution'], image_metadata['Z step'], image_metadata['T step'],
    #      image_metadata['Channel names'], image_metadata['Channel wv'],
    #      image_metadata['XY relative positions'], image_metadata['BitDepth']
    n_wells, image_size = 0, [0, 0]
    channel_names, channel_wv = [], []
    pixel_size, image_size_X, image_size_Y = 0, 0, 0
    z_step, z_start, current_z, t_step = 0, 0, 0, 0
    abs_z_step, abs_z_start = 0, 0
    fov_name_ref = ''
    xy_rel_positions = {}
    bit_depth = ''

    # Reading XML info
    events = pulldom.parse(xml_data_path)

    for event, node in events:
        if event == pulldom.START_ELEMENT:
            if node.tagName == 'Plates':
                # Plate format
                events.expandNode(node)
                tag = node.getElementsByTagName('Plate')[0]
                n_rows = int(tag.getElementsByTagName('PlateRows')[0].firstChild.data)
                n_columns = int(tag.getElementsByTagName('PlateColumns')[0].firstChild.data)
                n_wells = str(n_rows * n_columns)

            elif node.tagName == 'Maps':
                # Channel info (supposedly in the right order) and image info
                events.expandNode(node)
                map_tags = node.getElementsByTagName('Map')
                # Searching for the "Map" group with the info of interest
                for map_tag in map_tags:
                    entry_tags = map_tag.getElementsByTagName('Entry')

                    # Now scanning "entry" to see if correct group is selected
                    for t in entry_tags:
                        if t.getElementsByTagName('ChannelName'):
                            channel_names.append(t.getElementsByTagName('ChannelName')[0].firstChild.data)
                            channel_wv.append(int(t.getElementsByTagName('MainEmissionWavelength')[0].firstChild.data))
                            if not pixel_size:
                                pixel_size = float(t.getElementsByTagName('ImageResolutionX')[0].firstChild.data)
                                pixel_size *= 1E6  # !!!!! dimensions are in METERS for this format !!!!!
                            if not image_size_X:
                                image_size_X = int(t.getElementsByTagName('ImageSizeX')[0].firstChild.data)
                            if not image_size_Y:
                                image_size_Y = int(t.getElementsByTagName('ImageSizeY')[0].firstChild.data)
                            if not bit_depth:
                                max_int = str(t.getElementsByTagName('MaxIntensity')[0].firstChild.data)
                                bit_depth = 'Uint16' if max_int == '65536' else 'Uint8'

                # Preparing output for image size
                image_size = [image_size_X, image_size_Y]

            elif node.tagName == 'Images':
                # Searching for z-step (t-step unknown due to lack of image example)
                events.expandNode(node)
                image_tags = node.getElementsByTagName('Image')
                for image_tag in image_tags:
                    # Check it's Channel 1 (no need to gather other channel info here)
                    ch = int(image_tag.getElementsByTagName('ChannelID')[0].firstChild.data)
                    if ch == 1:
                        # Collecting FOV info
                        fov = int(image_tag.getElementsByTagName('FieldID')[0].firstChild.data)
                        well_row = str(image_tag.getElementsByTagName('Row')[0].firstChild.data).zfill(2)
                        well_column = str(image_tag.getElementsByTagName('Col')[0].firstChild.data).zfill(2)
                        fov_name = 'r{}c{}f{}'.format(well_row, well_column, str(fov).zfill(2))

                        # 3D acquisitions > gathering values for z-step
                        if image_tag.getElementsByTagName('PositionZ'):

                            # Check it's with z = 1
                            current_z = int(image_tag.getElementsByTagName('PlaneID')[0].firstChild.data)
                            if not z_step:
                                if current_z == 1:
                                    z_start = float(image_tag.getElementsByTagName('PositionZ')[0].firstChild.data)
                                    abs_z_start = float(image_tag.getElementsByTagName('AbsPositionZ')[0].firstChild.data)
                                    fov_name_ref = fov_name
                                if current_z == 2 and fov_name == fov_name_ref:
                                    z_step = abs(float(image_tag.getElementsByTagName('PositionZ')[0].firstChild.data) - z_start)
                                    abs_z_step = abs(float(image_tag.getElementsByTagName('AbsPositionZ')[0].firstChild.data) - abs_z_start)
                                    z_step *= 1E6  # !!!!! dimensions are in METERS for this format !!!!!
                                    abs_z_step *= 1E6

                                    # Check discrepancy between the two values
                                    if abs(z_step - abs_z_step) > z_step * 0.1:
                                        z_step = abs_z_step

                            # Collecting XY well relative FOV positions only for z == 1
                            if current_z == 1:
                                # !!!!! dimensions are in METERS for this format !!!!!
                                xtmp = image_tag.getElementsByTagName('PositionX')[0].firstChild.data
                                ytmp = image_tag.getElementsByTagName('PositionY')[0].firstChild.data

                                try:
                                    xpos = float(xtmp)
                                except:
                                    print(f'Error detected in metadata xml for image {fov_name} for PositionX: "{xtmp}". Replaced by 0.')
                                    xpos = 0

                                try:
                                    ypos = float(ytmp)
                                except:
                                    print(f'Error detected in metadata xml for image {fov_name} for PositionY: "{ytmp}". Replaced by 0.')
                                    ypos = 0

                                xy_rel_positions[fov_name] = [float(xpos) * 1E6, float(ypos) * 1E6]

                                # Collect time step
                                if not t_step:
                                    if image_tag.getElementsByTagName('MeasurementTimeOffset'):
                                        if str(image_tag.getElementsByTagName('TimepointID')[0].firstChild.data) == '2':
                                            t_step = float(image_tag.getElementsByTagName('MeasurementTimeOffset')[
                                                               0].firstChild.data)  # in sec
                                    else:
                                        t_step = 1

                        # 2D acquisitions
                        else:
                            # Collecting XY well relative FOV positions
                            xtmp = image_tag.getElementsByTagName('PositionX')[0].firstChild.data
                            ytmp = image_tag.getElementsByTagName('PositionY')[0].firstChild.data

                            try:
                                xpos = float(xtmp)
                            except:
                                print(f'Error detected in metadata xml for image {fov_name} for PositionX: "{xtmp}". Replaced by 0.')
                                xpos = 0

                            try:
                                ypos = float(ytmp)
                            except:
                                print(f'Error detected in metadata xml for image {fov_name} for PositionY: "{ytmp}". Replaced by 0.')
                                ypos = 0

                            xy_rel_positions[fov_name] = [float(xpos), float(ypos)]
                            print(f'{xy_rel_positions[fov_name]}')

                            # Collect time step
                            if not t_step:
                                if image_tag.getElementsByTagName('MeasurementTimeOffset'):
                                    if str(image_tag.getElementsByTagName('TimepointID')[0].firstChild.data) == '2':
                                        t_step = float(image_tag.getElementsByTagName('MeasurementTimeOffset')[
                                                           0].firstChild.data)  # in sec
                                else:
                                    t_step = 1

    return n_wells, image_size, pixel_size, z_step, t_step, channel_names, channel_wv, xy_rel_positions, bit_depth


def reconstruct_multidim_images(input_folder, file_pattern_choice, image_files_paths, pattern, constant_parts, metadata_parts,
                                img_metadata, output_dir, flip_img_X, flip_img_Y, do_max_proj):
    # This function reconstructs 3D to 5D stacks and outputs metadata per stack.
    # Input "img_metadata" dictionary contains common info for all FOV.
    # Output adds extra FOV info to "img_metadata" and stores it as a dictionary list matching the list of reconstructed
    # images.

    img_metadata_bkup = img_metadata.copy()  # When img_metadata is reset
    plane_metadata = {}  # Dictionary for individual image plane metadata (from tif tags)
    zfill_count_per_dim = [0] * 6  # Number of max zeros in the filenames for each dimension (may vary depending on experiment length)
    metadata_all_images = []  # This function captures and output image metadata (list of dict, one list item per image)

    f_count = 0

    # Filter image list using name pattern. Also collecting detected dimensions
    filtered_image_list = []  # Only files matching the template
    filtered_image_list_info = []  # list of dictionaries for filename base, dimensions
    file_parts = []  # To get constant parts for further name reconstruction

    # Preparing lists of well row, column, fov numbers for loops
    all_row_numbers, all_col_numbers, all_fov_numbers = [], [], []

    for f_p in image_files_paths:
        tmp_info_dict = {}  # Used to transfer info per file

        # Check image name
        in_pattern = re.compile(pattern)
        in_match = in_pattern.split(f_p)
        include_image = True if len(in_match) > 1 else False

        if include_image:
            # Save parts and filename base for next loop
            tmp_info_dict['f_base'] = ''.join([in_match[c] for c in constant_parts])
            file_parts = in_match       # file_parts[0] is empty

            # Extract useful metadata
            [img_width, img_height] = img_metadata['Image size']

            # Collect info from file name (current dimension captured as 'CTZYX')
            tmp_info_dict['image_dim'] = [int(in_match[metadata_parts['Ch']]), int(in_match[metadata_parts['Tp']]),
                                          int(in_match[metadata_parts['Z']]), img_height, img_width]
            all_row_numbers.append(int(in_match[metadata_parts['Well row']]))  # !!!! expecting a number here !!!!
            all_col_numbers.append(int(in_match[metadata_parts['Well column']]))
            all_fov_numbers.append(int(in_match[metadata_parts['Fov']]))

            # Collect number of zeros for each dimension, to be able to iterate later [Row, Col, Fov, T, Z, C]
            zfill_count_per_dim_tmp = [count_zero_fill(str(in_match[metadata_parts['Well row']])),
                                       count_zero_fill(str(in_match[metadata_parts['Well column']])),
                                       count_zero_fill(str(in_match[metadata_parts['Fov']])),
                                       count_zero_fill(str(in_match[metadata_parts['Tp']])),
                                       count_zero_fill(str(in_match[metadata_parts['Z']])),
                                       count_zero_fill(str(in_match[metadata_parts['Ch']]))]
            zfill_count_per_dim = [max(li) for li in zip(zfill_count_per_dim, zfill_count_per_dim_tmp)]

            # Save filtered list
            filtered_image_list.append(f_p)
            filtered_image_list_info.append(tmp_info_dict)

    # Check on image file pattern
    if not filtered_image_list:
        err_mess = f'The image file pattern {file_pattern_choice} seems not to correspond to your files (e.g. {f_p}).\n' \
                   f'Conversion will stop.\n\nPlease try to select a different file pattern.'
        Mbox('Error', err_mess, 0)
        sys.exit(err_mess)

    # Getting max dimensions for iterations below           # CTZ
    image_dims_all = [[*(filtered_image_list_info[k]['image_dim'])] for k in range(len(filtered_image_list_info))]
    image_dims = [max([image_dims_all[k][i] for k in range(len(image_dims_all))])
                  for i in range(len(image_dims_all[0]))]

    # Store in metadata for XML string creation
    img_metadata_bkup['DimensionOrder'] = 'XYZTC'  # opposite of numpy CYX / default is XYZTC
    img_metadata_bkup['Dimensions'] = [image_dims[4], image_dims[3], image_dims[2], image_dims[1], image_dims[0]]
    img_metadata_bkup['PixelSizeX'] = float(img_metadata['XY resolution'])  # conversion for xml meta

    # Clean list of numbers for loops below
    all_row_numbers = list(set(all_row_numbers))
    all_col_numbers = list(set(all_col_numbers))
    all_fov_numbers = list(set(all_fov_numbers))

    # Preparing file list as str for fast(?) search
    joined_file_list_as_str = ','.join(filtered_image_list)

    # zfill_count_per_dim is number of zeros, so need to add +1 for the zfill function
    zfill_count_per_dim = [v + 1 for v in zfill_count_per_dim]

    for ro in all_row_numbers:  # Rows
        for co in all_col_numbers:
            row_name = str(ro).zfill(zfill_count_per_dim[0])
            col_name = str(co).zfill(zfill_count_per_dim[1])
            well_name = file_parts[metadata_parts['Well row'] - 1] + row_name + \
                        file_parts[metadata_parts['Well column'] - 1] + col_name

            # Search for FOV
            missing_no = 0
            for fo in all_fov_numbers:
                fov_name = str(fo).zfill(zfill_count_per_dim[2])

                # Detection of Fov existence is done with corresponding parts of the file names (TO ADAPT UPON NAMING) !!!!!
                # Well name and Fov separated in case first Fov is missing for one well (expected with timelapses)
                common_name_part = file_parts[metadata_parts['Well row'] - 1] + row_name \
                                   + file_parts[metadata_parts['Well column'] - 1] + col_name \
                                   + file_parts[metadata_parts['Fov'] - 1] + fov_name

                if common_name_part in joined_file_list_as_str:         # TODO: change to list of wells instead of searching for them
                    # Init output data for new stack
                    stack_list = []
                    img_metadata = img_metadata_bkup.copy()  # Init

                    # Info to be pushed to internal metadata for further use in the main code
                    img_metadata['Well row'] = chr(ro + 64)
                    img_metadata['Well column'] = str(co)
                    img_metadata['Fov'] = str(fo)
                    img_metadata['Height'] = image_dims[3]  # in pixels
                    img_metadata['Width'] = image_dims[4]
                    f_base = 'r{}c{}f{}'.format(row_name, col_name, fov_name)
                    img_metadata['XY relative position'] = img_metadata['XY relative positions'][f_base]
                    del img_metadata['XY relative positions']

                    # Prepare reconstruction of file names
                    updated_file_parts = file_parts.copy() + [image_extension]
                    updated_file_parts[metadata_parts['Well row']] = str(row_name).zfill(zfill_count_per_dim[0])
                    updated_file_parts[metadata_parts['Well column']] = str(col_name).zfill(zfill_count_per_dim[1])
                    updated_file_parts[metadata_parts['Fov']] = str(fov_name).zfill(zfill_count_per_dim[2])

                    # Iterating over dimensions
                    for c in range(1, image_dims[0] + 1):
                        for t in range(1, image_dims[1] + 1):
                            for z in range(1, image_dims[2] + 1):
                                # Reconstruct expected file name
                                updated_file_parts[metadata_parts['Tp']] = str(t).zfill(zfill_count_per_dim[3])
                                updated_file_parts[metadata_parts['Z']] = str(z).zfill(zfill_count_per_dim[4])
                                updated_file_parts[metadata_parts['Ch']] = str(c).zfill(zfill_count_per_dim[5])
                                f_name_search = ''.join(updated_file_parts)

                                # Two known scenarios for files: in subfolder with wellname (r02c02) or directly in main
                                f_path_search_1 = os.path.join(input_folder, f_name_search)
                                f_path_search_2 = os.path.join(input_folder, well_name, f_name_search)

                                if not os.path.exists(f_path_search_1) and not os.path.exists(f_path_search_2):  # File Not Found!
                                    print(f'Expected image was not found in:\n{f_path_search_1}\n{f_path_search_2}')
                                    stack_list.append('')
                                else:
                                    f = f_path_search_2 if os.path.exists(f_path_search_2) else f_path_search_1
                                    f_count += 1

                                    # Progress info
                                    print('Processing file {} ({} / {})'.format(f, f_count,
                                                                                str(len(filtered_image_list))))

                                    # Adding image
                                    stack_list.append(os.path.join(input_folder, f))

                    # Save stack if existing (can also be 2 dimensions = YX)
                    if len(stack_list) > 0:
                        t_recons = time.perf_counter()

                        # Refining output file name
                        outname = img_metadata['Well row'] + col_name + file_parts[
                            metadata_parts['Fov'] - 1].upper() + fov_name + '.tif'
                        img_metadata['Filename'] = outname

                        # open all images into one stack (IMPORTANT: dimensions are CTZYX)
                        stack_data = stk_read_with_empty(stack_list, image_dims[3], image_dims[4])

                        # Remodel numpy array thanks to collected dimensions
                        final_data = np.reshape(stack_data, image_dims)

                        # Flip image according to selected option
                        if flip_img_X and flip_img_Y:
                            final_data = np.flip(final_data, (3, 4))
                        elif flip_img_X:
                            final_data = np.flip(final_data, 4)
                        elif flip_img_Y:
                            final_data = np.flip(final_data, 3)

                        # Optional Max Projection
                        if do_max_proj:
                            processed_final_data = np.max(final_data, axis=2, keepdims=True)

                            # Update of metadata
                            img_metadata['Dimensions'][img_metadata_bkup['DimensionOrder'].index('Z')] = 1
                        else:
                            processed_final_data = final_data

                        # ------------------------------------------------------------------------------------
                        # define metadata
                        outpath = os.path.join(output_dir, outname)

                        # Create metadata XML string compatible with Aivia
                        out_metadata = create_aivia_tif_xml_metadata(img_metadata)

                        # Write reconstructed image
                        imwrite(outpath, processed_final_data, metadata=None, description=out_metadata, bigtiff=True,
                                photometric='minisblack')

                        # Specify time per reconstructed image
                        print('File {} was reconstructed in {:d} seconds'.format(outname,
                                                                                 round(time.perf_counter() - t_recons)))

                        metadata_all_images.append(img_metadata)

                else:
                    missing_no += 1
                    if missing_no > 2:
                        break  # End Fov loop and go to next well

    return metadata_all_images


def param_gui():
    global file_patterns_info

    # Persist is to keep last values
    @magicgui(persist=True,
              patt={"label": "Select the image file name pattern that matches yours:",
                   "widget_type": "RadioButtons", 'choices': file_patterns_info.keys()},
              flipX={"widget_type": "CheckBox", "label": "Flip the image over the X axis?"},
              flipY={"widget_type": "CheckBox", "label": "Flip the image over the Y axis?"},
              zProj={"widget_type": "CheckBox", "label": "Perform max projection over the Z axis?"},
              call_button="Run")
    def get_info(patt=list(file_patterns_info.keys())[0], flipX=False, flipY=True, zProj=True):
        pass

    @get_info.called.connect
    def close_GUI_callback():
        get_info.close()

    get_info.show(run=True)
    selected_pattern = get_info.patt.value
    do_flip_X = get_info.flipX.value
    do_flip_Y = get_info.flipY.value
    do_Z_proj = get_info.zProj.value

    return selected_pattern, do_flip_X, do_flip_Y, do_Z_proj


def stk_read_with_empty(imlist, height, width):
    arr = np.zeros((len(imlist), height, width))
    d_type = ''

    for li_i, li in enumerate(imlist):
        if li:
            arr[li_i] = imread(li)
            if not d_type:
                d_type = imread(li).dtype

    return arr.astype(d_type)


def clean_xml_start(s):
    # Removes characters in front of xml data up to the '<' character
    final_s = s
    v = s[0]

    while v != '<' and len(final_s) > 1:
        final_s = final_s[1:]
        v = final_s[0]

    return final_s if '<' in final_s else 'invalid_xml'


def well_coord(args):
    # Returns [y, x] well center coordinates as a list
    [nx, ny, start_x, start_y, well_dist_x, well_dist_y, well_size_x, well_size_y] = args

    end_x = start_x + well_dist_x * (nx - 1)
    end_y = start_y + well_dist_y * (ny - 1)

    coord = np.mgrid[start_y:end_y:ny * 1j, start_x:end_x:nx * 1j]
    return coord.reshape(2, nx * ny)


def grid_coord(nx, ny, cen_x, gal_size_x, cen_y, gal_size_y):
    # Returns [y, x] image corner coordinates as a list / expected to be calibrated distances in microns
    start_x = cen_x - gal_size_x / 2
    end_x = start_x + gal_size_x
    start_y = cen_y - gal_size_y / 2
    end_y = start_y + gal_size_y

    coord = np.mgrid[start_y:end_y:ny * 1j, start_x:end_x:nx * 1j]
    return coord.reshape(2, nx * ny).transpose()


# Function to create the XML metadata that can be pushed to the ImageDescription or ome_metadata tif tags
def create_aivia_tif_xml_metadata(meta_dict):
    # Expected metadata dictionary:
    # ['DimensionOrder'] = str, ['Dimensions'] = list(int), ['PixelSizeX'], ['BitDepth'] = 'Uint16'
    # ['ChannelNames'] = list, ['ChannelColors'] = list, ['ChannelExWv'] = list of excitation wavelengths,
    # ['ChannelEmWv'] = list of emission wavelengths which is the one used in the end
    # Optional: Need one of 'ChannelColors', 'ChannelExWv', or , 'ChannelEmWv'
    # ['PixelSizeZ'], ['TimeStep'] in seconds, ['ChannelDescription'] = str

    # Init of values which are hard coded in the xml result. See line 14234 in tifffile.py
    dimorder = meta_dict['DimensionOrder']  # default = XYZTC
    ind_ref = 1  # incremented index for various entities below
    ifd = '0'  # Only for TiffData id
    samples = '1'
    res_unit = 'um'  # XYZ unit
    t_res_unit = "s"  # Time unit
    ch_emwv = [40] * int(meta_dict['Dimensions'][-1])  # Default value to add to ExWv if EmWv is missing
    ch_exwv = ch_emwv
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
        else:
            ch_exwv = meta_dict['ChannelExWv']
            ch_emwv = [c + ex_to_em for c in ch_exwv]  # Arbitrary addition
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
    ch_str = ''.join([add_channel(ind_ref + 2, c, ch_names[c], ch_colors[c], ch_description[c], ch_emwv[c], ch_exwv[c], wv_unit)
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
    b = rgb_list[0] << 16 | rgb_list[1] << 8 | rgb_list[2]

    return b


# Expected to be emission wavelength as input
def wavelength_to_RGB(wavelength):
    # Taken from Earl F.Glynn's web page: "http://www.efg2.com/Lab/ScienceAndEngineering/Spectra.htm"
    # Modified the version to have pink after 650 nm and to have red sooner (more adapted to usual false colors)
    gamma = 0.80
    int_max = 255

    # Defining color ranges with following limits
    # l1=pink, l2=blue, l3=cyan, l4=green, l5=yellow, l6=red, l7=red, l8=pink
    # l1, l2, l3, l4, l5, l6, l7 = 380, 440, 490, 510, 580, 645, 670, 781
    l1, l2, l3, l4, l5, l6, l7, l8 = 380, 440, 490, 510, 570, 600, 660, 781

    if l1 <= wavelength < l2:
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


def count_zero_fill(in_str):
    look_for = r'^(0{1,})\d+$'
    res = re.match(look_for, in_str)
    if res:
        return len(res.groups()[0])
    else:
        return 0


def pick_file(frame):
    # Create open file dialog
    openFileDialog = wx.FileDialog(frame, "Select the 'index.xml' file in the 'images' subfolder", "", "",
                                   "Metadata XML files (*.xml)|*.xml",
                                   wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

    if openFileDialog.ShowModal() == wx.ID_CANCEL:
        sys.exit()

    file = openFileDialog.GetPath()
    print("Selected file: ", file)
    openFileDialog.Destroy()
    return file


def Mbox(title, text, style):
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)


if __name__ == '__main__':
    params = {}
    run(params)

# Changelog:
# v1.00: - For opera Phenix (script comes from MultiWellPlateConverter_Yokogawa_v1_20.py)
# v1.01: - New virtual env code for auto-activation
#        - Bug fix: line 533 t_step = 0 was creating an error due to division by 0
#        - Bug fix: image subfolder could be confused with converted images
# v1.02: - Images are sometimes in the same subfolder as the index.xml file. Now compatible with this.
#        - Added duration for XML reading and for image conversion in log.
# v1.10: - Changing IJ saving style to aivia.tif style for reconstructed images
#        - Replaced 'name_dim_len' by 'zfill_count_per_dim' as some values are not z_filled in some cases
#        - Replaced minidom parser by pulldom (to avoid long reading with large XML)
#        - Z step reading can show some weird behavior, so backup established with absolute z position (if diff > 10%).
# v1.11: - TZCYX image stack reading order changed to CTZYX
#        - Adding flip image X or Y option as hard coded
# v1.12: - Adding some xml metadata compatibility for version 5.2.2180.259
# v1.13: - Adding exception for aberrant values for XY positions, such as '-' (where it becomes 0)
#        - Added a stop point if no image name is detected from the selected pattern
# v1.14: - UI added for choice of the image file pattern.
# v1.15: - New UI entry for flip and max proj. Fixing a bug with subfolder of images not detected
# v1.16: - Previous bug with subfolders was not fixed entirely. It is now fixed.
