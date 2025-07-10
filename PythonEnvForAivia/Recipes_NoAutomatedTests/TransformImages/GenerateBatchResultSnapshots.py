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

import numpy as np
import pandas as pd
import wx
import concurrent.futures
from magicgui import magicgui, widgets
import re
from tifffile import imread, imwrite, TiffFile
from skimage.exposure import rescale_intensity
from skimage.measure import find_contours
from skimage.util import img_as_ubyte
from skimage.morphology import binary_dilation, disk
from PIL import Image, ImageDraw, ImageFont
from xml.dom import minidom
from datetime import datetime

# Folder to quickly run the script on all Excel files in it
DEFAULT_FOLDER = r""

# Default parameters
downscale_f = 2  # Downscaling factor of crops generated with above size
quantile_values = {'min_val': 0.5, 'max_val': 0.9995, 'binary_val': 0.8}

img_ext = '.tif'
output_styles = ['png', 'jpg', 'aivia.tif', 'tif']
display_type = ['Original image', 'Outline of mask', 'Binary mask']

# Choice lists for the interactive form
choice_list1 = ['Result images are in subfolders, from a batch analysis [From Workflow / Aivia 11.0+]',
                'Result images are in the same folder']

ui_message = "Notes for multiwell plate:" \
             "\n* If a multiwell format exists, data of images in the same well are combined altogether" \
             "\n(becomes 1 well = 1 gallery)."

color_values = {'Blue': [0, 0, 255], 'Dark Blue': [0, 109, 185], 'Cyan': [0, 255, 255], 'Green': [0, 255, 0],
                'Dark Green': [0, 185, 109], 'Yellow': [255, 255, 0], 'Orange': [255, 170, 0], 'Red': [255, 0, 0],
                'Pink': [255, 0, 255], 'Purple': [185, 0, 109], 'Gray': [185, 185, 185], 'White': [255, 255, 255]}

color_list = ['Original from file'] + list(color_values.keys())


@magicgui(persist=True, layout='form',
          ch1={"label": "Excel table location:\n(tooltip available)", "widget_type": "RadioButtons",
               'choices': choice_list1},
          spacer={"label": "  ", "widget_type": "Label"},
          text={"label": ui_message, "widget_type": "Label"},
          call_button="Run")
def get_scenario(ch1=choice_list1[0], spacer='', text=''):
    pass


@get_scenario.called.connect
def close_GUI_callback():
    get_scenario.close()


get_scenario.show(run=True)
choice_1 = get_scenario.ch1.value


"""
Create color-coded snapshots of channels in an Aivia image. Each binary mask can be converted to a color-coded outline.
When "Original Image" output is selected, an autoscale of the intensities is done thanks to quantile (see above min and max).
When "Binary mask" output is selected, threshold is selected using quantile (see binary_val above).
Not compatible with 3D images and timelapses.
All images are expected to have the same metadata (channel no, names, pixel size).

WARNING: This currently works only under the following conditions:
    - There is no time dimension
    - Filenames do not contain '.' characters
    - Color from file can be read only from Aivia 14+
    - Color chooser is available only if final image has less than 13 channels

The generated files will be saved with the same name and put in the main batch folder.

0. GUI with info of first image (channel names and colors) >> selection of channels (tick box to skip and convert all)
1. Transform mask as contour if necessary
2. Downscale
3. Color-code
4. RGB output

Requirements
------------
pandas
openpyxl
xlrd
wxPython
magicgui

Returns
-------
Images
"""


# [INPUT Name:inputPath Type:string DisplayName:'Any channel']
# [OUTPUT Name:resultPath Type:string DisplayName:'Dummy to delete']
def run(params):
    global choice_list1, downscale_f, img_ext, display_type, quantile_values

    data_from_batch = False  # relative to batch analysis in Aivia 11.0+
    white_text = True   # text annotation on top of image

    if choice_1 == choice_list1[0]:
        data_from_batch = True

    contains_tps = False  # If tables contain timepoints        # TODO: harmonize all code about timepoints

    # Choose files (or rely on an hard coded default folder)
    if DEFAULT_FOLDER != "":
        # Preparing file list
        input_folder = DEFAULT_FOLDER
        all_files = os.listdir(input_folder)
        indiv_path_list = [os.path.join(os.path.abspath(input_folder), f) for f in all_files
                           if (f.endswith(img_ext) and not f.startswith('~'))]

    else:
        indiv_path_list = [pick_file(DEFAULT_FOLDER)]       # SINGLE file selection
        input_folder = os.path.dirname(indiv_path_list[0])

    # Scenario 'do_scan_workflow_folders': Collecting main folder
    batch_path = ''
    multiwell_mode = False
    file_list_per_well = []  # Expected structure when multiwell = batch \ A1 \ Job 1 \ Measurements \
    tmp_indiv_path_list = []  # Used to transfer paths to the grouped list per well

    if data_from_batch:
        indiv_path_list = []

        # Detect batch folder
        expected_well_folder = str(Path(input_folder).parents[0])  # 1 level up (A1 \ Job 1 \ )
        if is_multiwell(os.path.basename(expected_well_folder)):
            batch_path = str(Path(expected_well_folder).parent)  # 1 level up
            multiwell_mode = True
        else:
            batch_path = expected_well_folder

        # Search files in subfolders
        if multiwell_mode:
            main_subfolders = [os.path.join(batch_path, wf) for wf in os.listdir(batch_path)
                               if os.path.isdir(os.path.join(batch_path, wf))]
        else:
            main_subfolders = [batch_path]

        # Sort subfolders with correct numbers (lack of 0 for 1-9)
        if len(main_subfolders) > 1:
            main_subfolders = num_sort_by_folder(main_subfolders, 0)

        for well_f in main_subfolders:  # well level if multiwell

            for fov_f in [os.path.join(well_f, fov) for fov in os.listdir(well_f)
                          if os.path.isdir(os.path.join(well_f, fov))]:  # FOV level

                for f in [x for x in os.listdir(fov_f) if x.endswith(img_ext)]:
                    current_file_path = str(Path(fov_f, f))
                    indiv_path_list.append(current_file_path)
                    tmp_indiv_path_list.append(current_file_path)  # to transfer to the grouped list

            file_list_per_well.append(tmp_indiv_path_list)
            tmp_indiv_path_list = []  # reinit

    if len(indiv_path_list) < 1:
        error_msg = 'No result images found in the selected folder:\n{}\nTry to select another folder'.format(input_folder)
        Mbox('Error', error_msg, 0)
        sys.exit(error_msg)

    # Prompt for user to see how many tables will be processed
    mess = '{} result images were detected.\nPress OK to continue.'.format(len(indiv_path_list)) + \
           '\nA confirmation popup message will inform you when the process is complete.'
    print(mess)  # for log
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(Mbox, 'Detected tables', mess, 1)
        ans = future.result()

    if ans == 2:
        sys.exit('Process terminated by user')

    # OUTPUT folder
    output_folder = batch_path if data_from_batch else os.path.abspath(input_folder)

    img_meta = read_aivia_tif_metadata(indiv_path_list[0])

    # Define GUI with collected table names
    @magicgui(outformat={"label": "Select the output image format:",
                         "widget_type": "RadioButtons", 'choices': output_styles},
              chanchoices={"label": "Select 1 or multiple image channels to use (with Ctrl):",
                           "widget_type": "Select", 'choices': img_meta['ChannelNames']},
              downscalefactor={"label": "Downscaling factor of snapshot:",
                               "min": 0, "max": 20, "step": 2},
              skipselection={"label": "Tick the box to skip the color selection per channel",
                             "widget_type": "CheckBox"},
              persist=True, call_button="Run")
    def get_choices(outformat=output_styles[0], chanchoices=img_meta['ChannelNames'][0], downscalefactor=downscale_f,
                    skipselection=False):
        pass

    @get_choices.called.connect
    def close_GUI_tabs_callback_1():
        get_choices.close()

    get_choices.show(run=True)
    output_format = get_choices.outformat.value
    downscale_f = int(get_choices.downscalefactor.value)  # Pixels

    channels_names = get_choices.chanchoices.value
    channels = [img_meta['ChannelNames'].index(g) for g in channels_names]

    # Transform colors into RGB format for better visualisation
    if 'ChannelColors' in img_meta.keys():
        channel_raw_colors = [img_meta['ChannelColors'].index(g) for g in channels_names]
    else:
        channel_raw_colors = [0] * len(channels)

    # Converting byte colors to RGB
    channel_rgb_colors = [convert_byte_to_rgb(b_val) for b_val in channel_raw_colors]

    skip_color_select = get_choices.skipselection.value  # if too many channels in output, skip color selection
    if len(channels) > 12:
        skip_color_select = True

    if not skip_color_select:
        # Prepare next GUI for color choices (max of 12 channels)

        # Create list of widgets
        col_choice_widgets = [widgets.ComboBox(
            label=f"Select a color for {channels_names[ch]} (original RGB color is {channel_rgb_colors[ch]}):",
            choices=color_list)
            for ch in range(len(channels))
        ]
        disp_choice_widgets = [widgets.RadioButtons(
            label=f"Select the type of display:", choices=display_type, tooltip=channels_names[ch], value=display_type[0])
            for ch in range(len(channels))
        ]

        # dilation_choices
        dilation_lbl = widgets.Label(value="Thickness of outline display (1 to 15 px):")
        dilation_widget = widgets.SpinBox(min=1.0, max=15.0, step=2.0, value=3.0)

        # Push button
        push_butt = widgets.PushButton(text='Proceed')

        # Create containers
        sub_container_list = [widgets.Container(
            widgets=[col_choice_widgets[ch], disp_choice_widgets[ch]], layout="horizontal"
            ) for ch in range(len(channels))
        ] + [dilation_lbl, dilation_widget] + [push_butt]

        main_container = widgets.Container(
            widgets=sub_container_list, layout="vertical", scrollable=True, labels=False
        )

        # Create function to close GUI
        def close_GUI2_callback():
            main_container.close()

        push_butt.changed.connect(close_GUI2_callback)

        # Show GUI
        main_container.show(run=True)

        # Collect values
        display_selection = [wid.value for wid in disp_choice_widgets]
        color_selection_from_wid = [wid.value for wid in col_choice_widgets]
        dilation_dist = int((int(dilation_widget.value) - 1) / 2)

        # Convert colors to RGB values
        color_selection = []
        for ind, c_choice in enumerate(color_selection_from_wid):
            if c_choice == color_list[0]:
                try:
                    color_from_img = channel_rgb_colors[ind]
                    assert color_from_img != [0, 0, 0]
                except:
                    color_from_img = [255, 255, 255]
            else:
                color_from_img = color_values[c_choice]

            color_selection.append(color_from_img)

    else:
        color_selection = channel_rgb_colors
        display_selection = [display_type[0]] * len(channels)

    # Aivia metadata if output is aivia.tif
    if output_format == "aivia.tif":
        # Transferring metadata from first input image to galeries
        out_meta = img_meta.copy()

        # Modify channel names TODO
        # Modify channel colors TODO

        # New pixel dimension (for saved gallery)
        if downscale_f > 0:
            out_meta['PixelSizeX'] *= downscale_f

    # Init for main loop
    img_count = 0
    main_err_mess = '\n'  # To provide final info to users when errors happened but script continues

    # Evaluate time if number of file is > 10
    if len(indiv_path_list[:]) > 10:
        t1 = datetime.now()

    # Main LOOP -----------------------------------------------------------------------------------------------
    for file_index, input_file in enumerate(indiv_path_list):

        # defining output name
        if multiwell_mode or len(indiv_path_list) > 1:
            output_basename = str(
                Path(indiv_path_list[0]).parents[2].name)  # Well name or Batch folder when not multiwell
        else:
            output_basename = os.path.basename(indiv_path_list[0])[:-3]
            # output_basename = output_basename.replace('', '')
        output_file_base = os.path.join(output_folder, output_basename)  # name is incomplete!

        # Name specific to the current image
        output_img_name = os.path.basename(input_file)[:-3].replace('.aivia', '').replace('Results_', '')

        # Read image (CYX) and isolate selected channels
        sel_pyr_level = int(downscale_f / 2) if downscale_f > 1 else 0
        with TiffFile(input_file) as tif:
            is_pyramidal = tif.series[0].is_pyramidal
            n_levels = len(tif.series[0].levels)

            if is_pyramidal and n_levels >= sel_pyr_level:
                full_scaled_img_arr = tif.series[0].levels[sel_pyr_level].asarray()

                scaled_img_arr = full_scaled_img_arr[channels]

            else:
                raw_img_arr = np.stack([imread(input_file, key=ch) for ch in channels], axis=0)

                # Downscale image (CYX format)
                scaled_img_arr = raw_img_arr[:, ::downscale_f, ::downscale_f]

        # Adjust brightness / contrast
        for c in range(len(channels)):
            print(f"*** Processing channel {c+1} out of {len(channels)} ")
            if display_selection[c] == display_type[0]:     # As original but with quantile-based autoscale
                # Using quantile values
                q_min = np.percentile(scaled_img_arr[c], int(quantile_values['min_val'] * 100))
                q_max = np.percentile(scaled_img_arr[c], int(quantile_values['max_val'] * 100))

                if q_min != np.min(scaled_img_arr[c]) or q_max != np.max(scaled_img_arr[c]):
                    scaled_img_arr[c] = rescale_intensity(scaled_img_arr[c], in_range=(q_min, q_max), out_range='dtype')
                    print(f"Processed image using Quantiles (min = {quantile_values['min_val']}, max = {quantile_values['max_val']})")

            # Convert masks to outlines if requested
            elif display_selection[c] == display_type[1]:     # Outline of mask
                input_mask = scaled_img_arr[c]

                # Checking the provided mask is binary
                if len(np.unique(input_mask)) == 2:
                    # Check if max is the max of the bit depth (otherwise invert function won't work)
                    img_max = np.max(input_mask)
                    if np.iinfo(input_mask.dtype).max != img_max:
                        print('Image max found: ', img_max, '\nAdjusting max to the max of the bit depth.')
                        binary_mask = rescale_intensity(input_mask, in_range=(0, img_max),
                                                        out_range=(0, np.iinfo(input_mask.dtype).max)
                                                        ).astype(input_mask.dtype)
                        img_max = np.iinfo(input_mask.dtype).max
                    else:
                        binary_mask = input_mask.copy()

                    # Find all contours
                    contours = find_contours(binary_mask)

                    # Sort the contours by area in descending order
                    selected_contours = sorted(contours, key=lambda x: len(x), reverse=True)

                    # Extract the outer contours
                    # selected_contours, _ = find_outer_contours(contours)

                    # Concatenate all contours
                    all_sel_contours = np.round(np.concatenate(selected_contours, axis=0)).astype(int)

                    # Creating mask of all contours
                    cont_mask = np.zeros_like(input_mask).astype(input_mask.dtype)
                    cont_mask[all_sel_contours[:, 0], all_sel_contours[:, 1]] = img_max

                    # Dilation if requested
                    if dilation_dist > 0:
                        dil_pattern = disk(dilation_dist)
                        cont_mask = np.where(binary_dilation(cont_mask, dil_pattern.astype(int)), img_max, 0)

                    scaled_img_arr[c] = cont_mask

                else:   # channel is not binary - do nothing
                    mess = f'Error: channel {channels_names[c]} in {input_file} ' \
                           f'seems not to be a binary mask. Skipping contour creation.'
                    print(mess)

            elif display_selection[c] == display_type[2]:     # Binary mask out of a non-binary image
                # Checking the provided mask is not binary
                input_mask = scaled_img_arr[c]
                if len(np.unique(input_mask)) != 2:
                    # Create binary mask
                    q_val = np.percentile(input_mask[np.nonzero(input_mask)], int(quantile_values['binary_val'] * 100))
                    img_max = np.iinfo(input_mask.dtype).max
                    print(f"Image is not binary but binary mask was requested.",
                          f"\nCreating binary from quantile ({quantile_values['binary_val']}) value = {q_val}.")

                    scaled_img_arr[c] = np.where(input_mask >= q_val, img_max, 0)

        # Color code channels upon color choice
        if output_format != 'aivia.tif':
            rgb_arr_list = []
            for c in range(len(channels)):
                rgb_arr_list.append(single_channel_to_RGB(scaled_img_arr[c], color_selection[c]))

            rgb_arr = np.stack(rgb_arr_list, axis=0)        # such as dim 0 = R, G or B, then dim 1 = channels

            # Get max projection over channel dimension
            final_arr = np.amax(rgb_arr, axis=0)   # Final format is YXC, C not being the channels but the RGB result

        else:
            final_arr = scaled_img_arr

            # Format Aivia metadata

            # Modify dimensions TODO

        # Name of output file
        output_file_p = output_file_base + '_' + output_img_name + output_format

        # Save gallery
        if output_format == 'png' or output_format == 'jpg':
            save_with_pil(final_arr, output_format, output_file_p)

        elif output_format == 'aivia.tif':
            final_out_meta = create_aivia_tif_xml_metadata(out_meta)
            imwrite(output_file_p, final_arr, metadata=None, ome_metadata=final_out_meta, bigtiff=True)

        print('--- {} processed ({}/{}).'.format(input_file, file_index + 1, len(indiv_path_list)))

        # Evaluate time for the processing of one table
        if len(indiv_path_list[:]) > 10 and file_index == 0:
            show_estimated_time(t1, len(indiv_path_list[:]))

        img_count += 1

    # Main LOOP END -------------------------------------------------------------------------------------------

    final_mess = '{} images were saved here:\n{}'.format(img_count, output_folder)

    final_mess += main_err_mess  # Adding potential errors reported

    # Message box to confirm table processing
    print(final_mess)
    Mbox('Process completed', final_mess, 0)

    # Open folder with results
    os.startfile(output_folder)


def single_channel_to_RGB(ch_data, rgb_colors):
    rgb_image = np.stack((np.round(ch_data * (rgb_colors[0] / 255)),
                          np.round(ch_data * (rgb_colors[1] / 255)),
                          np.round(ch_data * (rgb_colors[2] / 255))
                          ), axis=-1).astype(ch_data.dtype)
    return rgb_image


def find_corresponding_image_name(table_file_name):
    found_name_re = re.search(r'(^.+.aivia.tif).+', table_file_name)
    if found_name_re:
        found_name = found_name_re.groups()[0]
    else:
        found_name = '_'.join(table_file_name.split('_')[:-1])
    return found_name + '.aivia.tif'


def save_with_pil(rgb_data, img_extension, output_path):
    if not img_extension in ['png', 'jpg', 'tif']:
        sys.exit('Error trying to save an image format not supported by PIL')

    # Convert 16-bit to 8-bit RGB
    if not rgb_data.dtype is np.dtype('uint8'):
        rgb_data_8b = img_as_ubyte(rgb_data)
        print('16-bit image converted to 8-bit for output')
    else:
        rgb_data_8b = rgb_data

    # Convert the numpy array to a PIL Image
    image = Image.fromarray(rgb_data_8b, mode='RGB')

    # Save the image as a PNG file
    image.save(output_path)


def find_outer_contours(list_of_contours):
    # Initialize a list to store the outer contours
    outer_contours = []
    contour_count = 0

    # Iterate through each contour
    for contour in list_of_contours:
        is_outer_contour = True

        # Check if the current contour is enclosed by any previously identified outer contours
        for outer_contour in outer_contours:
            enclosed_x = (np.min(outer_contour[:, 1]) < np.min(contour[:, 1])) and \
                         (np.max(outer_contour[:, 1]) > np.max(contour[:, 1]))
            enclosed_y = (np.min(outer_contour[:, 0]) < np.min(contour[:, 0])) and \
                         (np.max(outer_contour[:, 0]) > np.max(contour[:, 0]))

            if enclosed_x and enclosed_y:
                is_outer_contour = False
                break

        # If the contour is not enclosed by any outer contours, consider it as an outer contour
        if is_outer_contour:
            outer_contours.append(contour)
            contour_count += 1

    return outer_contours, contour_count


# Function to get XY resolution from standard tif or Aivia.tif
def read_aivia_tif_metadata(img_path):
    meta = {'PixelSizeX': 1}
    img_data = TiffFile(img_path)

    try:
        xml_data = img_data.ome_metadata
        try:
            # Reading XML info from Aivia 13.x
            parser = minidom.parseString(xml_data)
            tag = parser.getElementsByTagName('Image')[0].getElementsByTagName('Pixels')[0]
            if tag.hasAttribute('PhysicalSizeX'):
                meta['PixelSizeX'] = float(tag.attributes['PhysicalSizeX'].value)
            if tag.hasAttribute('PhysicalSizeZ'):
                meta['PixelSizeZ'] = float(tag.attributes['PhysicalSizeZ'].value)

            meta['Dimensions'] = list(map(int, [tag.attributes['SizeX'].value, tag.attributes['SizeY'].value,
                                                tag.attributes['SizeZ'].value, tag.attributes['SizeT'].value,
                                                tag.attributes['SizeC'].value]))

            meta['BitDepth'] = tag.attributes['Type'].value

            tags = tag.getElementsByTagName('Channel')
            meta['ChannelNames'] = [tags[t].attributes['Name'].value for t in range(len(tags))]
            meta['ChannelColors'] = [tags[t].attributes['Color'].value for t in range(len(tags))]

        except BaseException as e:
            print(e, '\nCould not read XML data in the "OME Description" tif tag using Aivia 13.x nomenclature.')

            try:
                # Reading XML info from Aivia 12.x  # TODO: missing Z calib
                parser = minidom.parseString(xml_data)
                tag = parser.getElementsByTagName('Image')[0]
                if tag.hasAttribute('PixelSizeX'):
                    meta['PixelSizeX'] = float(tag.attributes['PixelSizeX'].value)

                tags = parser.getElementsByTagName('ChannelInfo')
                meta['ChannelNames'] = [tags[t].attributes['Name'].value for t in range(len(tags))]

                tag = parser.getElementsByTagName('Pixels')[0]
                meta['Dimensions'] = list(map(int, [tag.attributes['SizeX'].value, tag.attributes['SizeY'].value,
                                                    tag.attributes['SizeZ'].value, tag.attributes['SizeT'].value,
                                                    tag.attributes['SizeC'].value]))

                meta['BitDepth'] = tag.attributes['PixelType'].value

            except BaseException as e:
                print(e, '\nCould not read XML data in the "OME Description" tif tag using Aivia 12.x nomenclature.')

    except BaseException as e:
        print(e, '\n"OME Description" tif tag was not found, could not retrieve metadata.')

    return meta


def convert_rgb_to_byte(rgb_list):
    b = rgb_list[0] << 16 | rgb_list[1] << 8 | rgb_list[2]

    return b


def convert_byte_to_rgb(byte_val):
    r = (byte_val >> 16) & 255
    g = (byte_val >> 8) & 255
    b = byte_val & 255

    return [r, g, b]


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


# Function to create the XML metadata that can be pushed to the ImageDescription or ome_metadata tif tags
def create_aivia_tif_xml_metadata(meta_dict):
    # Expected metadata dictionary:
    # ['Dimensions'] = list of XYZTC, ['PixelSizeX'], ['PixelSizeZ'], ['TimeStep'] in seconds, ['BitDepth'] = 'Uint16'
    # ['ChannelNames'] = list, ['ChannelColors'] = list of excitation wavelengths,

    # Init of values which are hard coded in the xml result. See line 14234 in tifffile.py
    dimorder = 'XYZTC'
    ifd = '0'
    samples = '1'
    res_unit = 'um'  # XYZ unit
    t_res_unit = "s"  # Time unit
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

    def add_channel(c, chname, color, emwv, exvw, wvunit):
        attributes = (
            f' Name="{chname}"'
            f' Color="{color}"'
            f' EmissionWavelength="{emwv}"'
            f' EmissionWavelengthUnit="{wvunit}"'
            f' ExcitationWavelength="{exvw}"'
            f' ExcitationWavelengthUnit="{wvunit}"'
        )
        return (
            f'<Channel ID="Channel:{c}"'
            f' SamplesPerPixel="{samples}"'
            f'{attributes}>'
            '</Channel>'
        )

    def add_image(index, dtype, channels_str, planecount, xy_resolution, z_resolution, resolution_unit,
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
            f'<Image ID="Image:{index}" Name="Image {index}">'
            f'<Pixels ID="Pixels:{index}"'
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
    ch_names = meta_dict['ChannelNames']
    ch_exwv = meta_dict['ChannelColors']
    ch_emwv = ch_exwv + 40  # Arbitrary addition
    ch_colors = [convert_rgb_to_byte(wavelength_to_RGB(w)) for w in ch_emwv]
    xy_res = meta_dict['PixelSizeX']
    z_res = meta_dict['PixelSizeZ']
    t_res = meta_dict['TimeStep']

    # Define string for dimension sizes
    sizes = ''.join(
        f' Size{ax}="{size}"' for ax, size in zip(dimorder, dimsizes)
    )

    # Define string for channels
    ch_count = int(dimsizes[4])
    ch_str = ''.join(
        [add_channel(c, ch_names[c], ch_colors[c], ch_emwv[c], ch_exwv[c], wv_unit) for c in range(ch_count)])

    # Define larger string for images
    img_count = 1
    plane_count = int(dimsizes[2]) * int(dimsizes[3]) * ch_count
    images = ''.join([add_image(i, meta_dict['BitDepth'], ch_str, plane_count, xy_res, z_res, res_unit, t_res,
                                t_res_unit) for i in range(img_count)])

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


def calculate_relation_stats(df_i, df_ii, id_header, meas_prefix, obj_ii_type, measurements):
    global relationships_with_stats, relationship_measurements_stats_todrop

    df_to_add = pd.DataFrame()

    if set(df_ii.columns) & set(measurements):
        for obj_i_name in df_i.iloc[:, 0]:
            obj_i_id = int(obj_i_name.split(' ')[-1])  # Expecting a space before number

            # Filter rows for object II matching object I ID
            df_single_obj = df_ii[df_ii[id_header] == obj_i_id]

            # Filter columns with given measurements
            df_single_obj_filtered = df_single_obj.filter(measurements)

            # Rename columns with prefix of object II
            df_single_obj_values = df_single_obj_filtered.rename(columns=lambda x: meas_prefix + x)

            # Calculate statistics only for some object II (see definition before code)
            if obj_ii_type in relationships_with_stats:

                # No of objects II
                df_obj_ii_count = pd.DataFrame({meas_prefix + 'Count': [df_single_obj_values.shape[0]]})

                # Calculate total values
                df_obj_ii_sum = df_single_obj_values.sum(axis=0).to_frame().transpose()

                # Rename columns with prefix of object II
                df_obj_ii_sum = df_obj_ii_sum.rename(columns=lambda x: 'Total_' + x)

                # Calculate average values
                df_obj_ii_mean = df_single_obj_values.mean(axis=0).to_frame().transpose()

                # Rename columns with prefix of object II
                df_obj_ii_mean = df_obj_ii_mean.rename(columns=lambda x: 'Average_' + x)

                # Constitute full line for one object I
                df_single_obj_to_add = pd.concat([df_obj_ii_count, df_obj_ii_sum, df_obj_ii_mean], axis=1)

                # Drop some columns if they make no sense
                for k_to_drop in relationship_measurements_stats_todrop.keys():
                    col_name = relationship_measurements_stats_todrop[k_to_drop] + '_' + meas_prefix + k_to_drop
                    if col_name in df_single_obj_to_add.keys():
                        df_single_obj_to_add.drop([col_name], axis=1, inplace=True)

            else:
                df_single_obj_to_add = df_single_obj_values  # if no statistics needed

            # Concatenate with df
            df_single_obj_to_add = df_single_obj_to_add.replace('nan', '')  # Replace NaN with empty strings
            df_to_add = pd.concat([df_to_add, df_single_obj_to_add], axis=0, ignore_index=True)

        # Concatenate with main object I df
        df_i = pd.concat([df_i, df_to_add], axis=1)

    return df_i


def split_dendrite_set_and_segments(df):
    is_segment = df[df.columns[0]].str.match(r'^.*\sSegment')

    dendrite_set_df = df[~is_segment]
    dendrite_seg_df = df[is_segment]

    return dendrite_set_df, dendrite_seg_df


def get_split_name(txt: str):
    # Check if previous object set name is present in txt
    # prev_obj_name = '' if it is for the first measurement tab or if there is only one object set with no child objects

    if txt.startswith('Std. Dev') or '.' not in txt:
        obj_name = ''
        meas_name = txt

    else:  # Presence of an object set name expected
        obj_name = txt.split('.')[0]
        meas_name = '.'.join(txt.split('.')[1:])

        # Check if text doesn't end with '...'
        if txt.endswith('...'):
            txt = txt[:-3]
            if '.' not in txt:
                obj_name = ''
            else:
                obj_name = txt.split('.')[0]
            meas_name = '--incomplete--'
            print('{}: name can\'t be retrieved from this text.'.format(txt))

    return meas_name, obj_name


# Expecting the two first dimensions to be YX, a third dimension can be channels
def add_text_at_top(input_array, raw_text, is_white):
    # Fixed parameters
    font = 'calibri'
    font_min_size = 8

    if input_array.ndim > 2:  # YXC
        ite = input_array.shape[2]  # Number of iterations if multiple channels
        input_array_3d = input_array
    else:
        ite = 1
        # Transform input array as 3 dimensions to ease code for all situations
        input_array_3d = np.array([input_array]).reshape((input_array.shape[1], input_array.shape[0], 1))

    # defining size of text area (lower right half quadrant)
    [height, width] = input_array_3d.shape[0:2]
    size_x = width
    size_y = height // 4
    start_w = 0
    start_h = 0

    # Create font
    font_size = height // 10 if height // 10 > font_min_size else font_min_size
    pil_font = ImageFont.truetype(font + ".ttf", size=font_size, encoding="unic")
    text_l, text_t, text_r, text_b = pil_font.getbbox(raw_text)
    text_width = text_r - text_l
    text_height = text_b - text_t

    # Use min or max intensity as writing intensity
    print_min_val = 0
    # print_max_val = input_array_3d.max() + 10 if input_array_3d.max() + 10 < np.iinfo(input_array_3d.dtype).max \
    #     else np.iinfo(input_array_3d.dtype).max
    print_max_val = np.iinfo(input_array_3d.dtype).max
    txt_intensity = print_max_val if is_white else print_min_val
    bkg_intensity = print_min_val if is_white else print_max_val

    # create a blank canvas with extra space between lines
    canvas = Image.new('L', (size_x, size_y), color=bkg_intensity)

    # draw the text onto the canvas
    draw = ImageDraw.Draw(canvas)
    r_shift = round(size_x / 15) if size_x > 30 else 2
    offset = (size_x - (text_width + r_shift), r_shift)  # Top right corner
    draw.text(offset, raw_text, font=pil_font, fill=txt_intensity)

    # Convert the canvas into an array
    text_img_canvas = np.asarray(canvas)

    # Use min intensity to create some background to text
    # text_img_canvas = np.where(text_img_canvas == 0, (txt_intensity - bkg_intensity) // 4 + bkg_intensity, text_img_canvas)

    # Create empty image to put text
    text_img = np.zeros_like(input_array_3d[:, :, 0])
    text_img += bkg_intensity

    # Put text array in text image
    text_img[start_h:start_h + size_y, start_w:start_w + size_x] = text_img_canvas

    # Print onto input image
    output_array = np.zeros_like(input_array_3d)
    for i in range(ite):
        if is_white:
            output_array[:, :, i] = np.maximum(input_array_3d[:, :, i], text_img)
        else:
            output_array[:, :, i] = np.minimum(input_array_3d[:, :, i], text_img)

    return output_array


# Expecting the two first dimensions to be YX, a third dimension can be channels
def add_text_at_bottom(input_array, raw_text, is_white):
    # Fixed parameters
    font = 'calibri'
    font_min_size = 8

    if input_array.ndim > 2:  # YXC
        ite = input_array.shape[2]  # Number of iterations if multiple channels
        input_array_3d = input_array
    else:
        ite = 1
        # Transform input array as 3 dimensions to ease code for all situations
        input_array_3d = np.array([input_array]).reshape((input_array.shape[1], input_array.shape[0], 1))

    # defining size of text area (lower right half quadrant)
    [height, width] = input_array_3d.shape[0:2]
    size_x = width
    size_y = height // 4
    start_w = 0
    start_h = height - size_y

    # Create font
    font_size = height // 10 if height // 10 > font_min_size else font_min_size
    pil_font = ImageFont.truetype(font + ".ttf", size=font_size, encoding="unic")
    text_l, text_t, text_r, text_b = pil_font.getbbox(raw_text)
    text_width = text_r - text_l
    text_height = text_b - text_t

    # Use min or max intensity as writing intensity
    print_min_val = 0
    # print_max_val = input_array_3d.max() + 10 if input_array_3d.max() + 10 < np.iinfo(input_array_3d.dtype).max \
    #     else np.iinfo(input_array_3d.dtype).max
    print_max_val = np.iinfo(input_array_3d.dtype).max
    txt_intensity = print_max_val if is_white else print_min_val
    bkg_intensity = print_min_val if is_white else print_max_val

    # create a blank canvas with extra space between lines
    canvas = Image.new('L', (size_x, size_y), color=bkg_intensity)

    # draw the text onto the canvas
    draw = ImageDraw.Draw(canvas)
    r_shift = round(size_x / 15) if size_x > 30 else 2
    offset = (size_x - (text_width + r_shift), size_y - (text_height + r_shift))  # Bottom right corner
    draw.text(offset, raw_text, font=pil_font, fill=txt_intensity)

    # Convert the canvas into an array
    text_img_canvas = np.asarray(canvas)

    # Use min intensity to create some background to text
    # text_img_canvas = np.where(text_img_canvas == 0, (txt_intensity - bkg_intensity) // 4 + bkg_intensity, text_img_canvas)

    # Create empty image to put text
    text_img = np.zeros_like(input_array_3d[:, :, 0])
    text_img += bkg_intensity

    # Put text array in text image
    text_img[start_h:start_h + size_y, start_w:start_w + size_x] = text_img_canvas

    # Print onto input image
    output_array = np.zeros_like(input_array_3d)
    for i in range(ite):
        if is_white:
            output_array[:, :, i] = np.maximum(input_array_3d[:, :, i], text_img)
        else:
            output_array[:, :, i] = np.minimum(input_array_3d[:, :, i], text_img)

    return output_array


def pick_file(default_d=''):
    print('Starting wxPython app')
    app = wx.App()

    # Create open file dialog
    openFileDialog = wx.FileDialog(None, "Select an image to process", ".\\", default_d,
                                   "Aivia files (*.aivia.tif)|*.aivia.tif", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

    openFileDialog.ShowModal()
    filename = openFileDialog.GetPath()
    print("Selected table(s): ", filename)
    openFileDialog.Destroy()
    return filename


def remove_double_empty_rows(df):
    for r in range(df.shape[0] - 2, -1, -1):
        dbl_rows = df.iloc[r:r + 2, :]
        if (dbl_rows == '').all().all():
            df.drop(r + 1, inplace=True)

    return df


def num_sort_by_folder(file_paths, level):
    # Level = 0 means sort folders themselves, level = 1 means sort thanks to the parent folder

    if level == 0:
        indiv_folders = [Path(fo).name for fo in file_paths]
    else:
        # Collect all job folder names
        indiv_folders = [Path(fo).parents[level - 1].name for fo in file_paths]

    # Add zeros in front of number
    indiv_folders = [re.sub(r'\d+', str(re.search(r'\d+', z).group(0)).rjust(6, '0'), z) for z in indiv_folders]

    # Sort them with number
    sorted_folders_index = sorted(range(len(indiv_folders)), key=lambda tmp: indiv_folders[tmp])

    # Redefine the list
    tmp_list = file_paths
    sorted_path_list = [tmp_list[ind] for ind in sorted_folders_index]

    return sorted_path_list


# Detects folders such as A1, A2, [...], Z99
def is_multiwell(folder_name):
    ans = False
    pattern = re.compile(r'^[a-zA-Z]\d{1,2}$')
    match = pattern.match(folder_name)

    if not match is None:
        ans = True

    return ans


def show_estimated_time(t1, nb_of_tables):
    t2 = datetime.now()
    duration = round((t2 - t1).total_seconds())
    if duration == 0:
        duration = 1
    mess = 'Estimated time for one table: {} seconds.\n\nEstimated time for {} tables: {} minutes.\n\n' \
           'Extra time is expected for the processing of the data.' \
           ''.format(duration, nb_of_tables, round(duration * nb_of_tables / 60))

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(Mbox, 'Estimated reading time', mess, 1)
        ans = future.result()

    if ans == 2:
        sys.exit('Process terminated by user')


def Mbox(title, text, style):
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)


if __name__ == '__main__':
    params = {}
    run(params)

# Changelog:
# v1.00: - Code from ProcessMultipleExcelTables_FromAivia / CreateGalleries
# v1.10: - Updating MagicGui from 0.5.1 to 0.9.1 with new container functionality to better control UI appearance
