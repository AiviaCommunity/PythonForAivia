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
from skimage.io import imread, imsave
from skimage.filters import sobel
from skimage.segmentation import watershed, mark_boundaries
from skimage.morphology import flood_fill
from skimage.util import img_as_ubyte
from skimage.transform import rescale, resize
import math
import time

import wx
import wx.lib.agw.floatspin as FS

"""
Compute watershed superpixels on an Aivia channel and create a mask from that painting.

Usability note! This plugin currently only works under certain conditions:
- Image is 2D only (no time)
- Image is smaller than the size of the screen

Improvements that would make this more usable are:
- Add ability to change color of painted mask
- Add ability to change color of superpixel boundaries
- Convert the Compactness slider to a log scale
- Scale image to screen size (need convert selected pixels by scaling factor)
 
Requirements
------------
numpy
scikit-image
PIL
wxPython

Parameters
----------
Input Image : Aivia channel
    Input channel to use for the transform.

Returns
-------
Aivia channel
    Binary mask as an image

Aivia objects
    Binary mask as an object
    
"""

# [INPUT Name:inputImagePath Type:string DisplayName:'Input Image']
# [OUTPUT Name:resultMaskPath Type:string DisplayName:'Mask Image']
# [OUTPUT Name:resultObjectPath Type:string DisplayName:'Mask Objects' Objects:2D MinSize:0.0 MaxSize:1000000000.0]
def run(params):
    print('reading')
    image_location = params['inputImagePath']
    result_mask_location = params['resultMaskPath']
    result_object_location = params['resultObjectPath']
    tCount = int(params['TCount'])
    zCount = int(params['ZCount'])
    print('read')
    if not os.path.exists(image_location):
        print(f'Error: {image_location} does not exist')
        return
        
    if zCount > 1 or tCount > 1:
        print('Currently this only supports 2D images with no time dimension.')
        return
    
    image_data = imread(image_location)
    mask_data = paint_superpixels(image_location)
    
    mask_data = resize(mask_data, image_data.shape, anti_aliasing=False)
    mask_data = img_as_ubyte(mask_data)
    
    imsave(result_mask_location, mask_data)
    imsave(result_object_location, mask_data)
    

def paint_superpixels(image_location):
    """
    Calls the Superpixel Painter window for the user to interactively segment using superpixels.

    Marker and compactness sliders adjust the watershed algorithm parameters.
    See documentation here:
    https://scikit-image.org/docs/dev/api/skimage.segmentation.html#skimage.segmentation.watershed

    Parameters
    ---------
    image : (N, M) array
        The image as a 2D array.

    Returns
    -------
    (N, M) array
        Binary mask based on the user's painting.
    """
    app = wx.App()    
    frame = MyFrame(image_location)
    app.MainLoop()

    return frame.mask[:, :, 0]
    

class MyFrame(wx.Frame):

    """
    An app that the user can use to manually paint their object by dragging their mouse
    across watershed superpixels.

    Attributes
    ----------
    input_image : str
        String representing path to the image to segment.
    
    superpixels : (N, M) array
        Label image containing computed superpixels.

    with_boundaries : (N, M, 3) array
        Image showing the boundaries of the superpixels superimposed with input_image.

    mask : (N, M, 3) array
        Image containing the user's selection.

    image_mask_bound : (N, M, 3) array
        Image showing composite of the input_image, superpixel boundaries, and the mask.

    """
        
    def __init__(self, image_location):
        super().__init__(parent=None, title='Superpixel Painter', size=wx.Size(900, 900))

        # Defined parameters
        self.refreshing_time = 0.1      # refreshing time when painting, in seconds
        self.refreshing_time_no_click = 0.01        # refreshing time when no click, in seconds
        self.zoom_factor = 2              # zoom factor for each step = for each scroll wheel step
        self.anti_aliasing = True

        image_np = imread(image_location)
        frame_size = self.GetSize()

        # Desired image size = 70% of frame size
        self.frame_w = int(frame_size[0] * 0.7)
        self.frame_h = int(frame_size[1] * 0.7)
        x_ratio = self.frame_w / image_np.shape[1]
        y_ratio = self.frame_h / image_np.shape[0]
        resize_factor = y_ratio if image_np.shape[0] > image_np.shape[1] else x_ratio
        self.image_w = image_np.shape[1]
        self.image_h = image_np.shape[0]

        # Correcting final frame size depending on image ratio
        self.frame_w = int(self.image_w * resize_factor)
        self.frame_h = int(self.image_h * resize_factor)

        # Initial resize of image to fit frame
        image_np_sc = resize(image_np, (self.frame_h, self.frame_w), anti_aliasing=self.anti_aliasing)

        # Init size values
        self.image_part_w = self.image_w       # Current image region viewed (in case of zooming)
        self.image_part_h = self.image_h
        self.start_X = 0
        self.end_X = self.image_part_w
        self.start_Y = 0
        self.end_Y = self.image_part_h

        # Init resized image in frame to fit available space
        image = wx.Image(self.frame_w, self.frame_h)
        image.SetData(image_np_sc.tobytes())
        wxBitmap = image.ConvertToBitmap()

        # Init superpixel boundaries
        max_markers = int(0.01 * (self.image_w * self.image_h))
        self.marker_color = [1.00, 0.73, 0.03]
        
        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour("gray")

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        user_instructions = 'Click left mouse button to paint superpixels. Click right mouse button to erase. ' \
                            'Middle click to fill a contour. Close the app when finished.'
        self.instruction = wx.StaticText(self.panel, label=user_instructions)
        self.instruction.SetForegroundColour(wx.Colour(255, 255, 255))
        self.mainSizer.Add(self.instruction, 0, wx.ALL | wx.CENTER, 5)

        self.imageCtrl = wx.StaticBitmap(self.panel, wx.ID_ANY, wxBitmap)
                
        self.mainSizer.Add(self.imageCtrl, 0, wx.ALL, 5)

        # Button to toggle the display of the mask + superpixel boundaries
        self.toggle_button = wx.ToggleButton(self.panel, wx.ID_ANY, 'Toggle display of superpixels', (50, 10))
        self.toggle_button.SetValue(True)
        self.mainSizer.Add(self.toggle_button, 0, wx.ALL, 5)

        # Sliders to control parameters
        self.marker = wx.StaticText(self.panel, label='Marker (change will reset drawn mask)')
        self.marker.SetForegroundColour(wx.Colour(255, 255, 255))
        self.mainSizer.Add(self.marker, 0, wx.ALL, 5)
        
        self.marker_sld = wx.Slider(self.panel, value=1, minValue=10, maxValue=max_markers,
                                    style=wx.SL_HORIZONTAL|wx.SL_LABELS)
        self.mainSizer.Add(self.marker_sld, 1, flag=wx.EXPAND, border=20)

        self.compactness = wx.StaticText(self.panel, label='Compactness (change will reset drawn mask)')
        self.compactness.SetForegroundColour(wx.Colour(255, 255, 255))
        self.mainSizer.Add(self.compactness, 0, wx.ALL, 5)
        self.compactness_float = 0.001

        self.compactness_sld = wx.Slider(self.panel, value=1, minValue=1, maxValue=10,
                                         style=wx.SL_HORIZONTAL|wx.SL_LABELS)
        self.mainSizer.Add(self.compactness_sld, 1, flag=wx.EXPAND, border=20)

        # Button to reset the mask
        self.clear_button = wx.Button(self.panel, wx.ID_ANY, 'Clear', (10, 10))
        self.mainSizer.Add(self.clear_button, 0, wx.ALL, 5)

        # Init image np data
        self.input_image_np_bkup = np.copy(image_np)     # Backup when zooming in and out

        # init zoom values. Max number of zoom steps defined thanks to the size of the image,
        # with arbitrary shift to avoid zooming in too much
        self.zoom_step = 1
        min_image_size = 10
        min_zoom_step = math.ceil(math.log(min_image_size) / math.log(self.zoom_factor))
        self.zoom_step_max = math.floor(math.log(min(self.image_w, self.image_h)) / math.log(self.zoom_factor)) - min_zoom_step
        print(f'Max zoom steps = {self.zoom_step_max}')

        # Computation of boundaries
        self.superpixels = watershed(sobel(image_np), markers=self.marker_sld.GetValue(),
                                     compactness=self.compactness_sld.GetValue()*self.compactness_float)
        self.with_boundaries = img_as_ubyte(mark_boundaries(image_np, self.superpixels, color=self.marker_color))

        # Init RGB images
        self.mask = np.zeros_like(self.with_boundaries)
        self.image_mask_bound = np.copy(self.with_boundaries)    # Existing image
        self.visible_image_part = np.copy(self.with_boundaries)  # View can be zoomed in and not covering the full image

        self.update_image()

        # Event binding to actions
        self.toggle_button.Bind(wx.EVT_TOGGLEBUTTON, self.toggle_mask_display)
        self.clear_button.Bind(wx.EVT_BUTTON, self.clear_mask)
        self.imageCtrl.Bind(wx.EVT_LEFT_DOWN, self.add_region)
        self.imageCtrl.Bind(wx.EVT_RIGHT_DOWN, self.remove_region)
        self.imageCtrl.Bind(wx.EVT_MIDDLE_DOWN, self.flood_fill)
        self.imageCtrl.Bind(wx.EVT_MOTION, self.is_click_down)      # For painting mode
        self.imageCtrl.Bind(wx.EVT_MOUSEWHEEL, self.zoom_in_or_out)            # Zoom in or out
        self.compactness_sld.Bind(wx.EVT_SLIDER, self.update_superpixels)
        self.marker_sld.Bind(wx.EVT_SLIDER, self.update_superpixels)

        self.panel.SetSizer(self.mainSizer)
        
        self.Show()

    def wximage_to_numpy(self, image):

        arr = np.asarray(image.GetDataBuffer())
        image_np = np.copy(np.reshape(arr, (image.GetWidth(), image.GetHeight(), 3)))
        return image_np

    def update_image(self):
        """
        Updates the app's displayed image.
        """
        # Resize image
        cropped_view = self.image_mask_bound[self.start_Y:self.end_Y, self.start_X:self.end_X, :]
        resized_view = np.empty((self.frame_h, self.frame_w, 3), dtype=self.input_image_np_bkup.dtype)
        for c in range(3):
            resized_view[:, :, c] = resize(cropped_view[:, :, c], (self.frame_h, self.frame_w),
                                           anti_aliasing=self.anti_aliasing, preserve_range=True)
        self.visible_image_part = resized_view

        wxBitmap = wx.Image(self.frame_w, self.frame_h, self.visible_image_part)
        self.imageCtrl.SetBitmap(wx.Bitmap(wxBitmap))

    def update_superpixels(self, event):
        """
        Recomputes superpixels with the user's selected parameters and displays the boundary image in the app.
        """
        self.superpixels = watershed(sobel(self.input_image_np_bkup), markers=self.marker_sld.GetValue(),
                                     compactness=self.compactness_sld.GetValue()*self.compactness_float)
        self.with_boundaries = img_as_ubyte(mark_boundaries(self.input_image_np_bkup, self.superpixels, color=self.marker_color))
        self.mask = np.zeros_like(self.with_boundaries)
        self.image_mask_bound = np.copy(self.with_boundaries)
        self.update_image()

        self.toggle_button.SetValue(True)

    def toggle_mask_display(self, event):
        """
        Toggles display of superpixel boundaries and drawn mask.
        """
        if self.toggle_button.Value:
            # Redraw selected regions
            for i in range(3):
                self.image_mask_bound[:, :, i] = np.where(self.mask[:, :, i] == 0, self.with_boundaries[:, :, i],
                                                          self.image_mask_bound[:, :, i])
                self.image_mask_bound[:, :, i] = np.where(self.mask[:, :, i] == 255, 255, self.image_mask_bound[:, :, i])

            self.update_image()

        else:
            # Reconstitute RGB image from input
            rgb_dims = np.insert(self.input_image_np_bkup.shape, 2, 3)
            input_image_np_rgb = np.empty(rgb_dims, dtype=self.input_image_np_bkup.dtype)
            for i in range(3):
                input_image_np_rgb[:, :, i] = self.input_image_np_bkup

            self.image_mask_bound = img_as_ubyte(input_image_np_rgb)

            self.update_image()

    def add_region(self, event):
        """
        Adds superpixels to the segmentation by clicking on the left mouse button.
        """
        # Get coordinates from event
        coord_X, coord_Y = self.relative_event_coord(event)

        chosen_region = self.superpixels[coord_Y, coord_X]
        for i in range(3):
            self.mask[:, :, i] = np.where(self.superpixels == chosen_region, 255, self.mask[:, :, i])
            self.image_mask_bound[:, :, i] = np.where(self.mask[:, :, i] == 255, 255, self.image_mask_bound[:, :, i])

        self.update_image()

    def is_click_down(self, event):
        """
        For painting mode
        """
        ms = wx.GetMouseState()
        time.sleep(self.refreshing_time_no_click)
        if ms.leftIsDown:
            self.add_region(event)
            time.sleep(self.refreshing_time)
        elif ms.rightIsDown:
            self.remove_region(event)
            time.sleep(self.refreshing_time)

    def remove_region(self, event):
        """
        Removes superpixels from the segmentation by dragging the right mouse button.
        """
        # Get coordinates from event
        coord_X, coord_Y = self.relative_event_coord(event)

        chosen_region = self.superpixels[coord_Y, coord_X]
        for i in range(3):
            self.mask[:, :, i] = np.where(self.superpixels == chosen_region, 0, self.mask[:, :, i])
            self.image_mask_bound[:, :, i] = np.where(self.mask[:, :, i] == 0, self.with_boundaries[:, :, i],
                                                      self.image_mask_bound[:, :, i])

        self.update_image()

    def flood_fill(self, event):
        """
        Fills a contour selected by the middle mouse button with the mask.
        """
        for i in range(3):
            self.mask[:, :, i] = flood_fill(self.mask[:, :, i], seed_point=(event.y, event.x), new_value=255,
                                            tolerance=1)
            self.image_mask_bound[:, :, i] = np.where(self.mask[:, :, i] == 255, 255, self.image_mask_bound[:, :, i])

        self.update_image()

    def clear_mask(self, event):
        """
        Clears the mask and updates the app's displayed image.
        """
        self.mask = np.zeros_like(self.with_boundaries)
        self.image_mask_bound = np.copy(self.with_boundaries)
        self.update_image()

    def zoom_in_or_out(self, event):
        """
        Zooming in thanks to position of cursor
        """
        wheel_direction = event.GetWheelRotation()

        zooming_allowed = False
        if wheel_direction > 0:             # Zoom in
            if self.zoom_step < self.zoom_step_max:
                zooming_allowed = True
                self.zoom_step += 1
        else:                               # Zoom out
            if self.zoom_step > 1:
                zooming_allowed = True
                self.zoom_step -= 1

        if zooming_allowed:
            # Get coordinates from event
            coord_X, coord_Y = self.relative_event_coord(event)

            # New image size
            if self.zoom_step > 1:
                self.image_part_w = round(self.image_w / (self.zoom_factor * (self.zoom_step - 1)))
                self.image_part_h = round(self.image_h / (self.zoom_factor * (self.zoom_step - 1)))
            else:
                self.image_part_w = self.image_w        # full image
                self.image_part_h = self.image_h

            # Adjust coordinates of cursor if too close to border
            adjusted_cursor_X = self.adjust_coordinates(coord_X, self.image_part_w, self.image_w)
            adjusted_cursor_Y = self.adjust_coordinates(coord_Y, self.image_part_h, self.image_h)

            # Adjust displayed image
            self.start_X = int(adjusted_cursor_X - (self.image_part_w / 2))
            self.end_X = self.start_X + self.image_part_w + 1
            self.start_Y = int(adjusted_cursor_Y - (self.image_part_h / 2))
            self.end_Y = self.start_Y + self.image_part_h + 1

            self.update_image()

        time.sleep(self.refreshing_time_no_click)

    def relative_event_coord(self, event):
        """
        Transforms XY coordinates of event on image in relative coordinates depending on current zoomed in view.
        Should not change coordinates if no zoom.
        """
        # Relative positions of mouse cursor in displayed frame (image part)
        relative_pos_X = event.x / self.frame_w
        relative_pos_Y = event.y / self.frame_h

        # Converted to pixel values in the visible part (if zoomed in)
        coord_X_in_view = int(self.image_part_w * relative_pos_X)
        coord_Y_in_view = int(self.image_part_h * relative_pos_Y)

        # Calculate real coordinates in full image
        real_coord_X = self.start_X + coord_X_in_view
        real_coord_Y = self.start_Y + coord_Y_in_view

        return real_coord_X, real_coord_Y

    def adjust_coordinates(self, coord, size, max_coord):
        """
        To readjust coordinates relative to the edge of the image, given the size of the bounding box edge (= size)
        """
        new_coord = coord
        if (coord - (size / 2)) < 0:
            new_coord = size / 2
        elif (coord + (size / 2)) > max_coord:
            new_coord = max_coord - (size / 2) + 1
        return new_coord


if __name__ == '__main__':
    params = {}
    params['inputImagePath'] = r'../test_8b_rect.tif'
    params['resultMaskPath'] = r'../test_8b_res.tif'
    params['resultObjectPath'] = r'../test_8b_objres.tif'
    params['TCount'] = 1
    params['ZCount'] = 1
    run(params)

# CHANGELOG:
# v1.01: - Bug fixed with wxPython.Image.SetData (ValueError: Invalid data buffer size.) >> was not using rescaled img.
# v1.02: - Adding left-/right-button dragging binding on top of click to select/deselect multiple superpixels in one go.
# v1.03: - Adding button to toggle the display of the boundaries and mask
# v1.04: - Add ability to zoom in/out with scroll of the mouse
# v1.05: - Resizing from the original image if image is downscaled to match window size
