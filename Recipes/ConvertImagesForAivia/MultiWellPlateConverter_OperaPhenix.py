# -------- Activate virtual environment -------------------------
import os
import ctypes
import sys
from pathlib import Path

parentFolder = str(Path(__file__).parent.parent)
activate_path = parentFolder + '\\env\\Scripts\\activate_this.py'
if os.path.exists(activate_path):
    exec(open(activate_path).read(), {'__file__': activate_path})
    print(f'Aivia virtual environment activated\nUsing python: {activate_path}')
else:
    error_mess = f'Error: {activate_path} was not found.\n\nPlease check that:\n' \
                 f'   1/ The \'FirstTimeSetup.py\' script was already run in Aivia,\n' \
                 f'   2/ The current python recipe is in the "\\PythonVenvForAivia\\Recipes" subfolder.'
    ctypes.windll.user32.MessageBoxW(0, error_mess, 'Error', 0)
    sys.exit(error_mess)
# ---------------------------------------------------------------

import wx
import numpy as np
import concurrent.futures
import re
import math
from xml.dom import minidom
from tifffile import imread, imwrite, TiffFile

# Folder to quickly run the script on all Excel files in it
DEFAULT_FILE = r''

# Plate layouts, returning: [number of wells in x, in y, start_x, start_y, well_dist_x, well_dist_y,
#                           well_size_x, well_size_y], name, plate ID
# WARNING: start_x is the center of the well, not the corner. A factor of 1000 is applied from the doc to these layouts.
LAYOUTS = {'24': [[6, 4, 15130, 13490, 19500, 19500, 15660, 15660], '24 Wellplate Type CELLSTAR', 'a06df3e5-a9f2-49c3-b74f-61fa6c3079ee'],
           '96': [[12, 8, 14380, 11240, 9000, 9000, 6580, 6580], '96 Wellplate Type Sensoplate', '6c3b16e9-8361-4b95-86a7-61b0cb1e90bc'],
           '384': [[24, 26, 12130, 8990, 4500, 4500, 3300, 3300], '384 Wellplate Type Sensoplate', 'd9bba488-59bc-429b-8b28-818aacf38a12']
           }
LAYOUTS_WELL_LIST = list(LAYOUTS.keys())

# Output file fixed parts
PREFIX = r'{"serializedVersion":0,"minSupportedVersion":0,"Plates":[{"Sectors":['
WELL_PREFIX = '{"Fields":['
TAGS = ['{"HintPath":', ',"FilePath":', ',"Name":', ',"PositionX":', ',"PositionY":', ',"HierarchyPath":']
WELL_TAGS = ['}],"Label":', ',"Tags":{', '}}']        # needs a comma between fields == wells
SUFFIX = ['],"FilePath":', ',"HintPath":',
          ',"VesselName":', ',"VesselId":', ',"Label":', ',"AdjustmentX":', ',"AdjustmentY":', '}]}']


"""
Creates an .aiviaexperiment file from a metadata file ("index.xml") and a folder of tif files (same location) from an 
Opera Phenix equipment (Harmony v6, software version = Python NGen 5.1.2167.302).
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
    global DEFAULT_FOLDER, LAYOUTS, LAYOUTS_WELL_LIST, PREFIX, WELL_PREFIX, TAGS, WELL_TAGS, SUFFIX

    sp = os.path.sep

    image_extension = '.tiff'

    print('Starting wxPython app')
    app = wx.App()
    frame = wx.Frame(None, -1, 'Folder picker')

    if not DEFAULT_FILE:
        metadata_file_p = pick_file(frame)        # To select metadata file
    else:
        metadata_file_p = DEFAULT_FILE

    input_folder = os.path.dirname(metadata_file_p)
    input_files = os.listdir(input_folder)

    # Select subfolders containing images
    img_subfolders = [os.path.join(input_folder, f) for f in input_files if os.path.isdir(os.path.join(input_folder, f))]

    if not img_subfolders:
        mess = 'No image subfolder was found. Cancelling script.'
        concurrent.futures.ThreadPoolExecutor().submit(Mbox, 'Process aborted', mess, 0)
        sys.exit(mess)  # for log

    print('Detected multiwell plate file: {}'.format(metadata_file_p))  # for log

    # Collect plate info
    # XY relative position is stored with the Well and FOV number. Image size is [w, h]
    image_metadata = {}
    (n_wells, image_metadata['Image size'], image_metadata['XY resolution'], image_metadata['Z step'],
     image_metadata['T step'], image_metadata['Channel names'], image_metadata['Channel wv'],
     image_metadata['XY relative positions']) = read_plate_info(metadata_file_p)

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
    combine_files = True        # Used for link between final image names and metadata (position, etc.)  # TODO: Useful, no position in metadata?

    # .+ at the beginning for the file path. All in brackets for image name comparison.
    # Example: r04c02f01p01-ch01t01.tiff
    pattern = r'.*(r)(\d{2})(c)(\d{2})(f)(\d{2})(p)(\d{2})(-ch)(\d{2})(t)(\d{2})\.tiff'

    constant_parts = [1, 2, 3, 4, 5, 6]         # for the same stack. Starts at index = 1!!
    # IDs in the tif metadata (in ImageDescription) and positions in pattern for FOV location info
    metadata_parts = {'Well row': 2,        # see block position in pattern
                      'Well column': 4,
                      'Fov': 6,
                      'Tp': 12,
                      'Z': 8,
                      'Ch': 10,
                      }
    list_image_info = reconstruct_multidim_images(input_folder, LAYOUTS[n_wells][0], image_files, pattern,
                                                  constant_parts, metadata_parts, image_metadata, output_folder)
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
    well_indexes_tmp = np.mgrid[1:n_well_y+1, 1:n_well_x+1]
    well_indexes = np.transpose(well_indexes_tmp.reshape((2, n_well_x * n_well_y))).tolist()

    # Init output file
    output_file = open(output_folder + sp + os.path.basename(os.path.dirname(input_folder)) + '.aiviaexperiment', 'w+')
    output_file.write(str(PREFIX))

    # Init grouping of images per well
    well_name = ''
    well_name_ref = 'A0'
    i = 0                       # to count number of images in the same well

    for img_info in list_image_info:
        # Check well name
        well_lett = img_info['Well row']
        well_numb = str(img_info['Well column'])
        well_name = well_lett + well_numb

        if well_name != well_name_ref:          # start a new well
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

        else:                                   # same well, new image
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

        tag_entries = ['"'+img_name+'"',
                       '"'+full_img_path.replace('\\', '\\\\')+'"',
                       '"'+img_name+'"', img_x, img_y, hierarchy]
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


def read_plate_info(xml_data_path):
    # The following regex extracts all info depending on the file format.
    # Output: n_wells, image_size, image_metadata['XY resolution'], image_metadata['Z step'], image_metadata['T step'],
    #      image_metadata['Channel names'], image_metadata['Channel wv'],
    #      image_metadata['XY relative positions']

    # Reading XML info
    parser = minidom.parse(xml_data_path)

    # Plate format
    main_tag = parser.getElementsByTagName('EvaluationInputData')[0]
    tag = main_tag.getElementsByTagName('Plates')[0].getElementsByTagName('Plate')[0]
    n_rows = int(tag.getElementsByTagName('PlateRows')[0].firstChild.data)
    n_columns = int(tag.getElementsByTagName('PlateColumns')[0].firstChild.data)
    n_wells = str(n_rows * n_columns)

    # Channel info (supposedly in the right order) and image info
    channel_names, channel_wv = [], []
    pixel_size, image_size_X, image_size_Y = 0, 0, 0
    map_tags = main_tag.getElementsByTagName('Maps')[0].getElementsByTagName('Map')
    # Searching for the "Map" group with the info of interest
    for map_tag in map_tags:
        entry_tags = map_tag.getElementsByTagName('Entry')

        # Now scanning "entry" to see if correct group is selected
        for t in entry_tags:
            if t.getElementsByTagName('ChannelName'):
                channel_names.append(t.getElementsByTagName('ChannelName')[0].firstChild.data)
                channel_wv.append(t.getElementsByTagName('MainEmissionWavelength')[0].firstChild.data)
                if not pixel_size:
                    pixel_size = float(t.getElementsByTagName('ImageResolutionX')[0].firstChild.data)
                    pixel_size *= 1E6           # !!!!! dimensions are in METERS for this format !!!!!
                if not image_size_X:
                    image_size_X = int(t.getElementsByTagName('ImageSizeX')[0].firstChild.data)
                if not image_size_Y:
                    image_size_Y = int(t.getElementsByTagName('ImageSizeY')[0].firstChild.data)

    # Preparing output for image size
    image_size = [image_size_X, image_size_Y]

    # Searching for z-step (t-step unknown due to lack of image example)
    z_step, z_start, current_z, t_step = 0, 0, 0, 0
    xy_rel_positions = {}
    image_tags = main_tag.getElementsByTagName('Images')[0].getElementsByTagName('Image')
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

                # Check it's FOV 1
                current_z = int(image_tag.getElementsByTagName('PlaneID')[0].firstChild.data)
                if not z_step and fov == 1:
                    if current_z == 1:
                        z_start = float(image_tag.getElementsByTagName('PositionZ')[0].firstChild.data)
                    if current_z == 2:
                        z_step = abs(float(image_tag.getElementsByTagName('PositionZ')[0].firstChild.data) - z_start)
                        z_step *= 1E6  # !!!!! dimensions are in METERS for this format !!!!!

                # Collecting XY well relative FOV positions only for z == 1
                if current_z == 1:
                    # !!!!! dimensions are in METERS for this format !!!!!
                    xy_rel_positions[fov_name] = [float(image_tag.getElementsByTagName('PositionX')[0].firstChild.data) * 1E6,
                                                  float(image_tag.getElementsByTagName('PositionY')[0].firstChild.data) * 1E6]

            # 2D acquisitions
            else:
                # Collecting XY well relative FOV positions
                xy_rel_positions[fov_name] = [float(image_tag.getElementsByTagName('PositionX')[0].firstChild.data),
                                              float(image_tag.getElementsByTagName('PositionY')[0].firstChild.data)]

    return n_wells, image_size, pixel_size, z_step, t_step, channel_names, channel_wv, xy_rel_positions


def read_image_info(s, extra_args):     # Extra_args = [metadata_parts]     // NOT USED HERE
    # The following regex extracts all info of each captured FOV. Expected format of s is TIFF tags dictionary
    metadata_ids = ''
    all_info = {}
    if extra_args:
        metadata_ids = extra_args

    for key, value in metadata_ids.items():
        if isinstance(key, int):
            tag_value = str(s[key])
            pattern = re.compile(r'{}(?P<val>\d+){}'.format(value[0], value[1]))
            match = pattern.search(tag_value)

            all_info[str(key)] = int(match.group('val'))

    return all_info


def reconstruct_multidim_images(input_folder, plate_info, image_files_paths, pattern, constant_parts, metadata_parts,
                                img_metadata, output_dir):
    # This function reconstructs 3D to 5D stacks and outputs metadata per stack.
    # Input "img_metadata" dictionary contains common info for all FOV.
    # Output adds extra FOV info to "img_metadata" and stores it as a dictionary list matching the list of reconstructed
    # images.

    fname_base = ''       # init base for name comparison
    old_fname_base = ''   # used when writing stack
    new_stack = False     # trigger to start new stack
    stack_list = []       # List of images for the same final image (TZCXY)
    img_metadata_bkup = img_metadata.copy()       # When img_metadata is reset
    plane_metadata = {}   # Dictionary for individual image plane metadata (from tif tags)
    name_dim_len = []     # Number of char in the filenames for each dimension (may vary depending on experiment length)
    metadata_all_images = []  # This function captures and output image metadata (list of dict, one list item per image)

    f_count = 0

    # Filter image list using name pattern. Also collecting detected dimensions
    filtered_image_list = []      # Only files matching the template
    filtered_image_list_info = []         # list of dictionaries for filename base, dimensions
    file_parts = []           # To get constant parts for further name reconstruction

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
            file_parts = in_match
            file_parts[0] = f_p[:f_p.find(''.join([in_match[i] for i in range(1, 5)]))]    # 1st part was not captured

            # Extract useful metadata
            [img_width, img_height] = img_metadata['Image size']

            # Collect info from file name (current dimension captured as 'TZCYX')
            tmp_info_dict['image_dim'] = [int(in_match[metadata_parts['Tp']]), int(in_match[metadata_parts['Z']]),
                                          int(in_match[metadata_parts['Ch']]), img_height, img_width]
            all_row_numbers.append(int(in_match[metadata_parts['Well row']]))                           # !!!! expecting a number here !!!!
            all_col_numbers.append(int(in_match[metadata_parts['Well column']]))
            all_fov_numbers.append(int(in_match[metadata_parts['Fov']]))

            # Collect number of char for each dimension, to be able to iterate later [Row, Col, Fov, T, Z, C]
            if not name_dim_len:
                name_dim_len = [len(in_match[metadata_parts['Well row']]), len(in_match[metadata_parts['Well column']]),
                                len(in_match[metadata_parts['Fov']]), len(in_match[metadata_parts['Tp']]),
                                len(in_match[metadata_parts['Z']]), len(in_match[metadata_parts['Ch']])]

            # Save filtered list
            filtered_image_list.append(f_p)
            filtered_image_list_info.append(tmp_info_dict)

    # Getting max dimensions for iterations below           # TZC
    image_dims_all = [[*(filtered_image_list_info[k]['image_dim'])] for k in range(len(filtered_image_list_info))]
    image_dims = [max([image_dims_all[k][i] for k in range(len(image_dims_all))])
                  for i in range(len(image_dims_all[0]))]

    # Clean list of numbers for loops below
    all_row_numbers = list(set(all_row_numbers))
    all_col_numbers = list(set(all_col_numbers))
    all_fov_numbers = list(set(all_fov_numbers))

    for ro in all_row_numbers:      # Rows
        for co in all_col_numbers:
            row_name = str(ro).zfill(name_dim_len[0])
            col_name = str(co).zfill(name_dim_len[1])

            # Search for FOV
            missing_no = 0
            for fo in all_fov_numbers:
                fov_name = str(fo).zfill(name_dim_len[2])

                # Detection of Fov existence is done with corresponding parts of the file names (TO ADAPT UPON NAMING) !!!!!
                # Well name and Fov separated in case first Fov is missing for one well (expected with timelapses)
                searching_items = [file_parts[metadata_parts['Well row'] - 1] + row_name +
                                   file_parts[metadata_parts['Well column'] - 1] + col_name,
                                   file_parts[metadata_parts['Fov'] - 1] + fov_name]

                if all([x in ','.join(filtered_image_list) for x in searching_items]):
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

                    # Iterating over dimensions
                    for t in range(1, image_dims[0] + 1):
                        for z in range(1, image_dims[1] + 1):
                            for c in range(1, image_dims[2] + 1):
                                # Detection of image existence done with dimensions in name (TO ADAPT UPON NAMING) !!!!!!!!!!
                                searching_items = [file_parts[metadata_parts['Well row'] - 1] + row_name +
                                                   file_parts[metadata_parts['Well column'] - 1] + col_name,
                                                   file_parts[metadata_parts['Fov'] - 1] + fov_name,
                                                   file_parts[metadata_parts['Tp'] - 1] + str(t).zfill(name_dim_len[3]),
                                                   file_parts[metadata_parts['Z'] - 1] + str(z).zfill(name_dim_len[4]) +
                                                   file_parts[metadata_parts['Ch'] - 1] + str(c).zfill(name_dim_len[5])]

                                f_status = [all([x in f for x in searching_items]) for f in filtered_image_list]

                                if not any(f_status):          # File Not Found!
                                    print('Expected image was not found for these dimensions: T={}, Z={}, C={}'.format(t, z, c))
                                    stack_list.append('')

                                else:
                                    f_ind = f_status.index(True)
                                    f = filtered_image_list[f_ind]
                                    f_count += 1

                                    # Progress info
                                    print('Processing file {} ({} / {})'.format(f, f_count, str(len(filtered_image_list))))

                                    # Adding image
                                    stack_list.append(os.path.join(input_folder, f))

                    # Save stack if existing (can also be 2 dimensions = YX)
                    if len(stack_list) > 0:
                        # Refining output file name
                        outname = img_metadata['Well row'] + col_name + file_parts[metadata_parts['Fov'] - 1].upper() + fov_name + '.tif'
                        img_metadata['Filename'] = outname

                        # open all images into one stack (IMPORTANT: dimensions are TZCYX)
                        stack_data = stk_read_with_empty(stack_list, image_dims[3], image_dims[4])

                        # Remodel numpy array thanks to collected dimensions
                        final_data = np.reshape(stack_data, image_dims)

                        # WARNING: remove axes upon dimensions (ex : 1 Z => remove Z axis) -------------------
                        final_dims = final_data.shape
                        axes = 'TZCYX'
                        if final_dims[2] == 1:          # Only one channel
                            final_data_tmp = final_data
                            final_data = np.squeeze(final_data_tmp, axis=2)
                            axes = axes.replace('C', '')

                        if final_dims[1] == 1:          # No Z
                            final_data_tmp = final_data
                            final_data = np.squeeze(final_data_tmp, axis=1)
                            axes = axes.replace('Z', '')

                        if final_dims[0] == 1:          # No T
                            final_data_tmp = final_data
                            final_data = np.squeeze(final_data_tmp, axis=0)
                            axes = axes.replace('T', '')

                        # ------------------------------------------------------------------------------------

                        # define metadata
                        outpath = os.path.join(output_dir, outname)
                        channel_labels = []
                        ij_tags = []

                        # Define image calibration
                        x_res = float(img_metadata['XY resolution'])
                        x_res_factor = 1         # for microns
                        z_step = img_metadata['Z step']
                        t_step = img_metadata['T step']

                        # Resolution
                        out_metadata = {'axes': axes}              # unit here for compatibility with ImageJ
                        if 'Z' in axes:
                            out_metadata['spacing'] = str(z_step)
                            out_metadata['unit'] = 'um'

                        if 'T' in axes:
                            out_metadata['fps'] = float(1 / t_step)         # Specific to IJ metadata
                            # out_metadata['TimeIncrement'] = float(t_step)   # Specific to OME metadata

                        final_x_res = 1 / (x_res / x_res_factor)
                        resolution_values = (final_x_res, final_x_res)      # in 1/microns

                        # Color channels
                        if 'Channel names' in img_metadata.keys() and 'C' in axes:
                            channel_labels = img_metadata['Channel names']
                            if image_dims[0] > 1 or image_dims[1] > 1:
                                channel_labels = channel_labels * image_dims[0] * image_dims[1]

                            # Color maps from excitation wavelength
                            all_LUTS = [create_lut(wavelength_to_RGB(int(wv)))
                                        for wv in img_metadata['Channel wv']]
                            ij_tags = {'LUTs': all_LUTS, 'Labels': channel_labels}

                            out_metadata['Labels'] = channel_labels
                            out_metadata['mode'] = 'composite'

                        imwrite(outpath, final_data, metadata=out_metadata, ijmetadata=ij_tags,
                                resolution=resolution_values, imagej=True, photometric='minisblack')

                        metadata_all_images.append(img_metadata)

                else:
                    missing_no += 1
                    if missing_no > 2:
                        break            # End Fov loop and go to next well

    return metadata_all_images


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


def create_lut(args):
    Rmax, Gmax, Bmax = args
    R_range = np.linspace(0, Rmax, 256, dtype=np.uint8)
    G_range = np.linspace(0, Gmax, 256, dtype=np.uint8)
    B_range = np.linspace(0, Bmax, 256, dtype=np.uint8)

    return np.stack([R_range, G_range, B_range], axis=0)


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


def wavelength_to_RGB(wavelength):
    # Taken from Earl F.Glynn's web page: "http://www.efg2.com/Lab/ScienceAndEngineering/Spectra.htm"
    gamma = 0.80
    int_max = 255

    if (wavelength >= 380) and (wavelength < 440):
        Red = - (wavelength - 440) / (440 - 380)
        Green = 0.0
        Blue = 1.0
    elif (wavelength >= 440) and (wavelength < 490):
        Red = 0.0
        Green = (wavelength - 440) / (490 - 440)
        Blue = 1.0
    elif (wavelength >= 490) and (wavelength < 510):
        Red = 0.0
        Green = 1.0
        Blue = - (wavelength - 510) / (510 - 490)
    elif (wavelength >= 510) and (wavelength < 580):
        Red = (wavelength - 510) / (580 - 510)
        Green = 1.0
        Blue = 0.0
    elif (wavelength >= 580) and (wavelength < 645):
        Red = 1.0
        Green = - (wavelength - 645) / (645 - 580)
        Blue = 0.0
    elif (wavelength >= 645) and (wavelength < 781):
        Red = 1.0
        Green = 0.0
        Blue = 0.0
    else:
        Red = 0.0
        Green = 0.0
        Blue = 0.0

    # Let the intensity fall off near the vision limits

    if (wavelength >= 380) and (wavelength < 420):
        factor = 0.3 + 0.7 * (wavelength - 380) / (420 - 380)
    elif (wavelength >= 420) and (wavelength < 701):
        factor = 1.0
    elif (wavelength >= 701) and (wavelength < 781):
        factor = 0.3 + 0.7 * (780 - wavelength) / (780 - 700)
    else:
        factor = 0.0

    rgb = [0] * 3

    # Don't want 0^x = 1 for x != 0
    rgb[0] = round(int_max * pow(Red * factor, gamma)) if Red > 0.0 else 0
    rgb[1] = round(int_max * pow(Green * factor, gamma)) if Green > 0.0 else 0
    rgb[2] = round(int_max * pow(Blue * factor, gamma)) if Blue > 0.0 else 0

    return rgb


if __name__ == '__main__':
    params = {}
    run(params)

# Changelog:
# v1.00: - For opera Phenix (script comes from MultiWellPlateConverter_Yokogawa_v1_20.py)
