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
from xml.dom import minidom
from tifffile import imread, imwrite, TiffFile, tiffcomment

# Folder to quickly run the script on all Excel files in it
DEFAULT_FOLDER = r''

# Plate layouts, returning: [number of wells in x, in y, start_x, start_y, well_dist_x, well_dist_y,
#                           well_size_x, well_size_y], name, plate ID
# WARNING: start_x is the center of the well, not the corner. A factor of 1000 is applied from the doc to these layouts.
LAYOUTS = {'1': [[1, 1, 28590, 12750, 0, 0, 45050, 20450], 'LabTek 1 Chamber', 'c2b5b936-1513-4e68-80d2-5a9af773864d'],
           '24': [[6, 4, 15130, 13490, 19500, 19500, 15660, 15660], '24 Wellplate Type CELLSTAR',
                  'a06df3e5-a9f2-49c3-b74f-61fa6c3079ee'],
           '96': [[12, 8, 14380, 11240, 9000, 9000, 6580, 6580], '96 Wellplate Type Sensoplate',
                  '6c3b16e9-8361-4b95-86a7-61b0cb1e90bc'],
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
Creates an .aiviaexperiment file from a folder of tif files acquired by an Evos (M5000, Thermo)
Testing set does not contain timepoints or Z so script was built for 2D + ch mainly.
Automated false color is calculated from the wavelength in the tif metadata. 
Default layout is a 24-well plate. Each well corresponds to same image name base.

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
    n_wells = '24'  # To get all images with same base name in an individual well

    print('Starting wxPython app')
    app = wx.App()
    frame = wx.Frame(None, -1, 'Folder picker')

    if not DEFAULT_FOLDER:
        input_folder = pick_folder('', frame)  # To select metadata file
    else:
        input_folder = DEFAULT_FOLDER

    image_files = [os.path.join(input_folder, f) for f in os.listdir(input_folder) if f.endswith(image_extension)]

    if not image_files:
        mess = 'No {} image was found. Cancelling script.'.format(image_extension)
        concurrent.futures.ThreadPoolExecutor().submit(Mbox, 'Process aborted', mess, 0)
        sys.exit(mess)  # for log

    print('Detected {} {} file.'.format(len(image_files), image_extension))  # for log

    # Potential common info
    image_metadata = {}
    # XY relative position is stored with the Well and FOV number. Image size is [w, h]
    """
        (image_metadata['Image size'], image_metadata['XY resolution'], image_metadata['ChannelNames'], image_metadata['ChannelEmWv'],
         image_metadata['XY relative positions']) = read_plate_info(metadata_file_p)
    """

    # Define main output folder
    output_folder = input_folder + sp + 'Converted for Aivia'
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    # Init in case there is no combination of individual files
    # --------------------------------------------------------------------------------------------------------------
    # Combine files as channels are saved independently
    combine_files = True  # Used for link between final image names and metadata (position, etc.)  # TODO: Useful, no position in metadata?

    # .+ at the beginning for the file path. All in brackets for image name comparison.
    # Example: 'XXXXXX_0003_GFP.tiff'
    pattern = r'.+\\(.+)(_)(\d{4})(_)(\w{2,6}).tiff'

    constant_parts = [1, 2, 3, 4]  # for the same stack. Starts at index = 1!!
    # IDs in the tif metadata (in ImageDescription) and positions in pattern for FOV location info
    metadata_parts = {'Fov': 3,
                      'Ch': 5
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

    # Fov are positioned from top left of well
    well_size_x, well_size_y = float(plate_box_info[6]) * 0.9, float(plate_box_info[7]) * 0.9
    rel_x_coord_start, rel_y_coord_start = 0 - well_size_x / 2, 0 - well_size_y / 2
    img_offset_x, img_offset_y = 0, 0           # will be incremented
    img_spacer = well_size_y * 0.05             # Arbitrary value

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

        # Current image size
        img_size_x = float(img_info['Image size'][0][0]) * float(img_info['XY resolution'][0])
        img_size_y = float(img_info['Image size'][0][1]) * float(img_info['XY resolution'][0])

        # Calculate relative position in well thanks to fov number and well size limit
        if fov == 1:
            img_offset_x, img_offset_y = rel_x_coord_start + img_size_x / 2, rel_y_coord_start + img_size_y / 2
        else:
            if img_offset_x + img_size_x > well_size_x * 0.66:
                img_offset_x = rel_x_coord_start + img_size_x / 2
                img_offset_y += img_size_y + img_spacer

        # Final fov positions calculated by moving image coordinates from center to top-left
        img_x = w_centers[1] + img_offset_x
        img_y = w_centers[0] + img_offset_y

        # INCREMENT in X axis for next fov positioning
        img_offset_x += img_size_x + img_spacer

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

    mess = 'The experiment file was saved as:\n{}.\n\nFolder containing the file will now open...'.format(output_file.name)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(Mbox, 'Process completed', mess, 0)
    print(mess)  # for log
    
    # Opening Windows Explorer folder containing the output file
    try:
        os.startfile(output_folder)
    except BaseException as e:
        print(e)


def read_image_info(s, extra_args):  # Extra_args = [metadata_parts]     // NOT USED HERE
    # Expected format of s is an XML + JSON
    # XML contains: size X, Y, calibrated image size, channel name
    # Also contains more detailed JSON data: objective mag, pixel size, channel "PseudoColor" and "Emission Wavelength"

    # Reading XML info
    parser = minidom.parseString(s)

    main_tag = parser.getElementsByTagName('Pixels')[0]

    # Image info
    image_size_X = int(main_tag.attributes['SizeX'].value)
    image_size_Y = int(main_tag.attributes['SizeY'].value)

    # Preparing output for image size
    image_size = [image_size_X, image_size_Y]

    # Now extracting the JSON part
    json_part = s.split('<!--')[1].replace('\r\n', '')

    # Using regex to find attributes
    pixel_size_re = re.search(r'"MicronsPerPixel":\s+(\d{1,4}\.\d*),', json_part)
    pixel_size = float(pixel_size_re.groups()[0])

    channel_name_re = re.findall(r'"ChannelSettings":\s+{\s+"Name":\s+"(.{2,6})",', json_part)
    channel_name = channel_name_re[0]

    channel_wv_re = re.findall(r'"Emission Wavelength":\s+(\d{2,4}\.\d*).{0,4}[,}]', json_part)
    channel_wv = int(float(channel_wv_re[0])) if not 'trans' in channel_name.lower() else 0


    return image_size, pixel_size, channel_name, channel_wv


def reconstruct_multidim_images(input_folder, plate_info, image_files_paths, pattern, constant_parts, metadata_parts,
                                img_metadata, output_dir):
    # This function reconstructs 3D to 5D stacks and outputs metadata per stack.
    # Input "img_metadata" dictionary contains common info for all FOV.
    # Output adds extra FOV info to "img_metadata" and stores it as a dictionary list matching the list of reconstructed
    # images.

    f_base_no_fov_ref = ''  # init base for name comparison
    fov_ref = '-1'
    old_f_base = ''  # used when writing stack
    new_stack = False  # trigger to start new stack
    stack_list = []  # List of images for the same final image (TZCXY)
    plane_metadata = {}  # Dictionary for individual image plane metadata (from tif description)
    name_dim_len = []  # Number of char in the filenames for each dimension (may vary depending on experiment length)
    metadata_all_images = []  # This function captures and output image metadata (list of dict, one list item per image)

    constant_parts_no_fov = constant_parts[:-2]

    well_count, row_no, col_no, fov_no = 0, 1, 0, 0         # final fov number in virtual multiwell plate
    col_no_max = plate_info[0]

    image_files_paths.append('list_end')  # To write the final image in the main loop

    for f_p in image_files_paths:

        # Check image name
        in_pattern = re.compile(pattern)
        in_match = in_pattern.split(f_p)
        include_image = True if len(in_match) > 1 or f_p == 'list_end' else False

        if include_image:
            # Read plane metadata
            if f_p != 'list_end':
                spacer = in_match[constant_parts[-1]]

                with TiffFile(f_p) as tif:
                    raw_metadata = tif.pages[0].description

                # Extract useful metadata
                plane_metadata['Image size'], plane_metadata['XY resolution'], plane_metadata['ChannelNames'], \
                plane_metadata['ChannelEmWv'] = read_image_info(raw_metadata, metadata_parts)

                # Compare name with previous image
                f_base_no_fov = ''.join([in_match[c] for c in constant_parts_no_fov])
                fov = in_match[metadata_parts['Fov']]

                if f_base_no_fov + fov != f_base_no_fov_ref + fov_ref:
                    # Very specific to TRANS channels being with the following FOV number instead of the same
                    condition_1 = (f_base_no_fov == f_base_no_fov_ref)   # Share same base
                    condition_2 = int(fov) == (int(fov_ref) + 1)                             # Fov is the next fov number
                    condition_3 = os.path.exists(os.path.join(input_folder, f_base_no_fov + fov + '.tiff'))  # main image exists
                    condition_4 = os.path.exists(os.path.join(input_folder, f_base_no_fov_ref + fov_ref + spacer + 'trans.tiff')) or \
                                  os.path.exists(os.path.join(input_folder, f_base_no_fov_ref + fov_ref + spacer + 'TRANS.tiff'))

                    print(os.path.join(input_folder, f_base_no_fov_ref + fov + spacer + 'trans.tiff'))

                    if not (condition_1 and condition_2 and not condition_3 and not condition_4):
                        new_stack = True

                        # Adding an extra condition to create 1 extra well if image name base changes
                        if not condition_1:
                            fov_no = 1         # final fov number in virtual multiwell plate
                            well_count += 1
                            if col_no < col_no_max:
                                col_no += 1
                            else:
                                col_no = 1
                                row_no += 1
                        else:
                            fov_no += 1         # final fov number in virtual multiwell plate

                        old_f_base = f_base_no_fov_ref + fov_ref
                        f_base_no_fov_ref = f_base_no_fov
                        fov_ref = fov       # save for next comparison

            else:
                new_stack = True        # for final image stack
                old_f_base = f_base_no_fov_ref + fov

            # Init stack if new one starts / save previous one if any
            if new_stack:
                # Save previous stack if existing
                if len(stack_list) > 0:
                    # Refining output file name
                    outname = old_f_base + '.tif'
                    img_metadata['Filename'] = outname

                    # open all channels for the first timepoint
                    stack_data = imread(stack_list)                 # CYX in that case
                    if len(stack_list) == 1:
                        stack_data = np.expand_dims(stack_data, axis=0)  # Add C dimension if single channel
                    stack_data = np.expand_dims(stack_data, axis=1)              # Add Z
                    stack_data = np.expand_dims(stack_data, axis=1)              # Add T


                    # Prepare metadata for XML string creation
                    img_metadata['DimensionOrder'] = 'XYZTC'          # opposite of numpy CYX / default is XYZTC
                    img_metadata['Dimensions'] = img_metadata['Image size'][0] + [1, 1, len(img_metadata['ChannelNames'])]
                    img_metadata['BitDepth'] = 'Uint8'      # Default for Evos
                    img_metadata['PixelSizeX'] = float(img_metadata['XY resolution'][0])    # conversion for xml meta

                    # Create metadata XML string compatible with Aivia
                    out_metadata = create_aivia_tif_xml_metadata(img_metadata)

                    # output
                    outpath = os.path.join(output_dir, outname)
                    # imwrite(outpath, stack_data, metadata=None, extratags=[(270, 's', None, out_metadata, False)],
                    #         bigtiff=True)
                    imwrite(outpath, stack_data, metadata=None, description=out_metadata, bigtiff=True)

                    metadata_all_images.append(img_metadata)
                    img_metadata = {}  # Re init

                # Init output data again for new stack
                stack_list = []

            # Fill stack
            if f_p != 'list_end':
                if new_stack:
                    stack_list = [f_p]
                    for k in [meta for meta in plane_metadata.keys()]:
                        img_metadata[k] = [plane_metadata[k]]
                    new_stack = False

                    # FOV location info
                    img_metadata['Well row'] = chr(row_no + 64)
                    img_metadata['Well column'] = col_no
                    img_metadata['Fov'] = fov_no

                else:
                    stack_list.append(f_p)
                    for k in [meta for meta in plane_metadata.keys()]:
                        img_metadata[k].append(plane_metadata[k])

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


def pick_folder(default_dir, frame):
    # Create open file dialog
    openDirDialog = wx.DirDialog(frame, "Select the folder containing the tif files",
                                 default_dir, wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)

    if openDirDialog.ShowModal() == wx.ID_CANCEL:
        sys.exit()

    folder = openDirDialog.GetPath()
    print("Selected folder: ", folder)
    openDirDialog.Destroy()
    return folder


# Function to create the XML metadata that can be pushed to the ImageDescription or ome_metadata tif tags
def create_aivia_tif_xml_metadata(meta_dict):
    # Expected metadata dictionary:
    # ['DimensionOrder'] = string, ['Dimensions'] = list as int, ['PixelSizeX'], ['BitDepth'] = 'Uint16'
    # ['ChannelNames'] = list, ['ChannelExWv'] = list of excitation wavelengths,
    # Optional: ['PixelSizeZ'], ['TimeStep'] in seconds,
    # ['ChannelEmWv'] = list of emission wavelengths which is the one used in the end

    # Init of values which are hard coded in the xml result. See line 14234 in tifffile.py
    dimorder = meta_dict['DimensionOrder']      # default = XYZTC
    ind_ref = 1         # incremented index for various entities below
    ifd = '0'           # Only for TiffData id
    samples = '1'
    res_unit = 'um'     # XYZ unit
    t_res_unit = "s"    # Time unit
    wv_unit = 'nm'      # Wavelength unit
    planes = ''         # Not used at the moment (would store Z position of indiv planes)
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

    def add_channel(ind_ch, c, chname, color, emwv, exvw, wvunit):
        attributes = (
            f' Name="{chname}"'
            f' Color="{color}"'
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
                  t_resolution, t_resolution_unit):
        if any([z_resolution == v for v in ['', 0]]):
            z_resolution = 1
        if any([t_resolution == v for v in ['', 0]]):
            t_resolution = 1

        attributes = (
            f' PhysicalSizeX="{xy_resolution}"'
            f' PhysicalSizeXUnit="{resolution_unit}"'
            f' PhysicalSizeY="{xy_resolution}"'
            f' PhysicalSizeYUnit="{resolution_unit}"'
            f' PhysicalSizeZ="{z_resolution}"'
            f' PhysicalSizeZUnit="{resolution_unit}"'
            f' TimeIncrement="{t_resolution}"'
            f' TimeIncrementUnit="{t_resolution_unit}"'
        )

        return (
            f'<Image ID="Image:{ind_img}" Name="Image {ind_img}">'
            f'<Pixels ID="Pixels:{ind_img + 1}"'
            f' DimensionOrder="{dimorder}"'
            f' Type="{dtype}"'               
            f'{sizes}'                      # space at the beginning provided with 'sizes'
            f'{attributes}>'                # space at the beginning provided with 'attributes'
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
    if not 'T' in dimorder:
        dimsizes += [int('1')]
        dimorder += 'T'

    ch_names = meta_dict['ChannelNames']
    if 'ChannelEmWv' in meta_dict.keys():
        ch_emwv = meta_dict['ChannelEmWv']
        ch_exwv = [0 for c in ch_emwv]          # Dummy values in meta
    else:
        ch_exwv = meta_dict['ChannelExWv']
        ch_emwv = [c + 40 for c in ch_exwv]                # Arbitrary addition

    ch_colors = [convert_rgb_to_byte(wavelength_to_RGB(w)) for w in ch_emwv]
    xy_res = meta_dict['PixelSizeX']
    if 'PixelSizeZ' in meta_dict.keys():
        z_res = meta_dict['PixelSizeZ']
    else:
        z_res = 1
    if 'TimeStep' in meta_dict.keys():
        t_res = meta_dict['TimeStep']
    else:
        t_res = 1

    # Define string for dimension sizes
    sizes = ''.join(
        f' Size{ax}="{size}"' for ax, size in zip(dimorder, dimsizes)
    )

    # Define string for channels
    ch_count = int(dimsizes[dimorder.index('C')])
    ch_str = ''.join([add_channel(ind_ref + 2, c, ch_names[c], ch_colors[c], ch_emwv[c], ch_exwv[c], wv_unit)
                      for c in range(ch_count)])            # ind_ref + 2 because of Image ID and Pixels ID before

    # Define larger string for images
    plane_count = int(dimsizes[dimorder.index('Z')]) * int(dimsizes[dimorder.index('T')]) * ch_count
    images = add_image(ind_ref, meta_dict['BitDepth'], ch_str, plane_count, xy_res, z_res, res_unit, t_res, t_res_unit)

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


def Mbox(title, text, style):
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)


def convert_rgb_to_byte(rgb_list):
    b = rgb_list[0] << 16 | rgb_list[1] << 8 | rgb_list[2]

    return b


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
        Red = 1.0
        Green = 1.0
        Blue = 1.0

    # Let the intensity fall off near the vision limits

    if (wavelength >= 380) and (wavelength < 420):
        factor = 0.3 + 0.7 * (wavelength - 380) / (420 - 380)
    elif (wavelength >= 420) and (wavelength < 701):
        factor = 1.0
    elif (wavelength >= 701) and (wavelength < 781):
        factor = 0.3 + 0.7 * (780 - wavelength) / (780 - 700)
    else:
        factor = 1.0

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
# v1.00: - script comes from MultiWellPlateConverter_OperaPhenix_v1_01.py
#        - Modification of metadata output (here ome-xml)
