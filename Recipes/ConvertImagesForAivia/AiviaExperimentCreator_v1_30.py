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
from tifffile import TiffFile
import numpy as np
import math
import datetime
import re
import concurrent.futures

# Folder to quickly run the script on all Excel files in it
DEFAULT_FOLDER = ''     # r''

# Plate layouts, returning: [number of wells in x, in y, start_x, start_y, well_dist_x, well_dist_y,
#                           well_size_x, well_size_y], name, plate ID
# WARNING: start_x is the center of the well, not the corner. A factor of 1000 is applied from the doc to these layouts.
LAYOUTS = {'1': [[1, 1, 28590, 12750, 0, 0, 45050, 20450], 'LabTek 1 Chamber', 'c2b5b936-1513-4e68-80d2-5a9af773864d'],
           '2': [[2, 1, 16600, 12750, 24000, 0, 22400, 21500], 'LabTek 2 Chamber', 'f2a482b5-9578-4f46-ae0a-6769e1f7252c'],
           '': []}

# Output file fixed parts
PREFIX = r'{"serializedVersion":0,"minSupportedVersion":0,"Plates":[{"Sectors":['
WELL_PREFIX = '{"Fields":['
TAGS = ['{"HintPath":', ',"FilePath":', ',"Name":', ',"PositionX":', ',"PositionY":', ',"HierarchyPath":']
WELL_TAGS = ['}],"Label":', ',"Tags":{', '}}']        # needs a comma between fields == wells
SUFFIX = ['],"FilePath":', ',"HintPath":',
          ',"VesselName":', ',"VesselId":', ',"Label":', ',"AdjustmentX":', ',"AdjustmentY":', '}]}']


"""
Creates an .aiviaexperiment file listing the different sample conditions (Control, Sample, etc.) as different wells.
Grouping is done by asking to select files in the same group.
Expects images having the same size and calibration.

Requirements
------------
wxPython

Returns
-------
Aiviaexperiment file with automated format picked from the number of image groups selected by user.

"""


# [INPUT Name:inputPath Type:string DisplayName:'Any channel']
# [OUTPUT Name:resultPath Type:string DisplayName:'Dummy to delete']
def run(params):
    global DEFAULT_FOLDER, LAYOUTS, PREFIX, WELL_PREFIX, TAGS, WELL_TAGS, SUFFIX

    sp = os.path.sep

    # Choose files (or rely on an hard coded default folder)
    input_folder = DEFAULT_FOLDER
    ans = 6         # init for OK answer
    group_list = []
    n_groups = 0

    while ans == 6 and n_groups < 96:
        new_list = pick_files(input_folder)
        group_list.append(new_list)
        input_folder = os.path.dirname(group_list[n_groups][0])
        ans = Mbox("Continue?", "Do you want to add another group of images?", 3)
        n_groups += 1

    if ans == 2:        # CANCEL
        sys.exit('Script aborted by user.')

    if len(group_list) < 1:
        error_msg = 'No files selected. Aborting...'.format(input_folder)
        Mbox('Error', error_msg, 0)
        sys.exit(error_msg)

    # Prompt for user to see how many tables will be processed
    mess = '{} groups of files were selected.\nPress OK to continue.'.format(n_groups) + \
           '\nA confirmation popup message will inform you when the process is complete.'
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(Mbox, 'Detected tables', mess, 1)
        ans = future.result()

    print(mess)  # for log

    if ans == 2:
        sys.exit('Process terminated by user')

    # Default image size = 3000 * 3000 px with a resolution of 0.33 µm / px >> 1000 * 1000 µm
    image_size_x = image_size_y = 1000       # value in MICRONS!

    # Attempt to collect real size from first image
    try:
        with TiffFile(group_list[0][0]) as tmp_img:
            tmp_tif_tags = tmp_img.pages[0].tags
            tmp_width = int(tmp_tif_tags[256].value)
            tmp_height = int(tmp_tif_tags[257].value)
            # now getting XZ pixel resolution from image description
            try:
                tmp_img_desc = tmp_tif_tags[270].value
                tmp_pix_size = float(re.search(r' PixelSizeX="(?P<pxsize>.+)"\sPixelSizeY', tmp_img_desc).group('pxsize'))
            except Exception as e:
                print('Could not read image pixel resolution. Set to 1.\nError code: ', e)
                tmp_px_size = 1

            image_size_x = tmp_pix_size * tmp_width
            image_size_y = tmp_pix_size * tmp_height

    except Exception as e:
        print('Image metadata reading failed. Falling back on manual entry of image size.\nError code: ', e)

    # Auto choice of the layout, returning
    # [number of wells in x, in y, start_x, start_y, well_dist_x, well_dist_y, well_size_x, well_size_y]
    n_groups = str(n_groups)
    plate_box_info = LAYOUTS[n_groups][0]
    plate_name = LAYOUTS[n_groups][1]
    plate_id = LAYOUTS[n_groups][2]

    # Get the coordinates of the center of wells
    well_centers = well_coord(plate_box_info)
    well_sx, well_sy = plate_box_info[-2:]

    # Main LOOP -----------------------------------------------------------------------------------------------
    # Init output file
    output_file = open(input_folder + sp + 'Experiment_{}.aiviaexperiment'.format(datetime.date.today()), 'w+')
    output_file.write(str(PREFIX))

    # Define well XY indexes
    n_well_y = int(plate_box_info[1])
    n_well_x = int(plate_box_info[0])
    well_indexes_tmp = np.mgrid[1:n_well_y+1, 1:n_well_x+1]
    well_indexes = well_indexes_tmp.reshape((2, n_well_x * n_well_y))
    w = 0

    for single_list in group_list:
        # Init well block in output file
        output_file.write(str(WELL_PREFIX))

        # Well name
        well_lett = chr(well_indexes[w][0] + 64)
        well_numb = str(well_indexes[w][1])
        well_name = well_lett + well_numb

        # Calculate how many images go in x and in y axis
        ratio_yx = float(well_sy / well_sx)
        n_img_x = math.ceil(math.sqrt(len(single_list) / ratio_yx))
        n_img_y = math.ceil(n_img_x * ratio_yx)                         # check ceil usage?

        # Calculate size of image gallery and check it's not beyond well size. Applying a factor to include some space
        gall_size_x = (image_size_x * n_img_x) * 1.05
        if gall_size_x > well_sx:
            gall_size_x = well_sx
        gall_size_y = (image_size_y * n_img_y) * 1.05
        if gall_size_y > well_sy:
            gall_size_y = well_sy

        # Get coordinates of the top left corner of the images (1 is X, 0 is Y)
        img_coord = grid_coord(n_img_x, n_img_y,
                               well_centers[1, w], gall_size_x,
                               well_centers[0, w], gall_size_y)

        # Loop to write coordinates and image path in final file
        i = 0
        for img in single_list:
            img_name = os.path.basename(single_list[i])
            [img_x, img_y] = [img_coord[1, i], img_coord[0, i]]         # 1 is X, 0 is Y
            hierarchy = '["{}","{}","R{}"]'.format(well_lett, well_numb, i+1)

            tag_entries = ['"'+img_name+'"',
                           '"'+single_list[i].replace('\\', '\\\\')+'"',
                           '"'+img_name+'"', img_x, img_y, hierarchy]
            str_to_write = ''.join([x + str(y) for (x, y) in zip(TAGS, tag_entries)])
            output_file.write(str_to_write)

            # Write junction between different images
            if img != single_list[-1]:
                output_file.write('},')

            # Increment i
            i += 1

        # Write junction between different wells
        well_tag_entries = ['"'+well_name+'"', '', '']
        str_to_write = ''.join([x + str(y) for (x, y) in zip(WELL_TAGS, well_tag_entries)])
        output_file.write(str_to_write)

        # Put a comma between wells
        if w < len(group_list)-1:
            output_file.write(',')

        # Increment well index
        w += 1

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


def well_coord(args):
    # Returns [y, x] well center coordinates as a list
    [nx, ny, start_x, start_y, well_dist_x, well_dist_y, well_size_x, well_size_y] = args

    end_x = start_x + well_dist_x * (nx - 1)
    end_y = start_y + well_dist_y * (ny - 1)

    coord = np.mgrid[start_y:end_y:ny * 1j, start_x:end_x:nx * 1j]
    return coord.reshape(2, nx * ny)


def grid_coord(nx, ny, cen_x, gal_size_x, cen_y, gal_size_y):
    # Returns [y, x] image corner coordinates as a list
    start_x = cen_x - gal_size_x / 2
    end_x = start_x + gal_size_x
    start_y = cen_y - gal_size_y / 2
    end_y = start_y + gal_size_y

    coord = np.mgrid[start_y:end_y:ny * 1j, start_x:end_x:nx * 1j]
    return coord.reshape(2, nx * ny)


def pick_files(default_dir):
    print('Starting wxPython app')
    app = wx.App()

    # Create open file dialog
    openFileDialog = wx.FileDialog(None, "Select a list of images representing the same experimental conditions",
                                   default_dir, "", "Image files (*.*)|*.*",
                                   wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE)

    openFileDialog.ShowModal()
    filenames = openFileDialog.GetPaths()
    print("Selected table(s): ", filenames)
    openFileDialog.Destroy()
    return filenames


def Mbox(title, text, style):
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)


if __name__ == '__main__':
    params = {}
    run(params)

# Changelog:
# v1.00: - Layout of wells defined with well spacing distance
# v1.10: - Layout of wells now fitting definition in Aivia: distance between wells instead of space between wells
# v1.20: - Using well centers as reference instead of corner. Easier to pull image gallery in the center
# v1.30: - Add attempt to detect calibrated size of image. Fallback on a GUI if not successful
