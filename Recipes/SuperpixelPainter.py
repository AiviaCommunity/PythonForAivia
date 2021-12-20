import os.path
import numpy as np
from skimage.io import imread, imsave
from skimage.io import imread
from skimage.filters import sobel
from skimage.segmentation import watershed, mark_boundaries
from skimage.morphology import flood_fill
from skimage.util import img_as_ubyte
from skimage.transform import rescale, resize

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
numpy (comes with Aivia installer)
scikit-image (comes with Aivia installer)
PIL (installed with scikit-image)
wxPython (needs manual install)

For Aivia 10.x with embedded python, the guide to install non-standard packages (windows and macOS):

* Open terminal
* Change directory: cd "path/to/Aivia/Python/directory/" (For e.g. C:\Program Files\Leica Microsystems\Aivia 10.5.0\Python)
* Run: python -m pip install <name_of_the_module>

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
        return;
        
    if zCount > 1 or tCount > 1:
        print('Currently this only supports 2D images with no time dimension.')
        return
    
    
    image_data=imread(image_location)
    mask_data = paint_superpixels(image_location)
    
    
    mask_data = resize(mask_data, image_data.shape, anti_aliasing=False)
    mask_data=img_as_ubyte(mask_data)
    
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

    boundaries : (N, M, 3) array
        Image showing the boundaries of the superpixels superimposed with input_image.

    mask : (N, M, 3) array
        Image containing the user's selection.

    display_image : (N, M, 3) array
        Image showing composite of the input_image, superpixel boundaries, and the mask.

    """
        
    def __init__(self, image_location):
        super().__init__(parent=None, title='Superpixel Painter', size = wx.Size( 800,800 ))


       
        image_np=imread(image_location)
        frame_size = self.GetSize()
        frame_h = (frame_size[0]) *0.7
        frame_w = (frame_size[1]) *0.7
        image_np_sc = resize(image_np, (frame_h,frame_w), anti_aliasing=False)
        self.W = image_np_sc.shape[0]
        self.H = image_np_sc.shape[1]

        image = wx.Image(self.W, self.H)
        image.SetData(image_np.tobytes())
        wxBitmap = image.ConvertToBitmap()
        
        
        max_markers = int(0.01 * (self.W*self.H))
        self.marker_color = [1.00, 0.73, 0.03]
        
        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour("gray")

        
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        user_instructions = 'Click left mouse button to paint superpixels. Click right mouse button to erase. ' \
                            'Middle click to fill a contour. Close the app when finished.'
        self.instruction = wx.StaticText(self.panel, label=user_instructions)
        self.instruction.SetForegroundColour(wx.Colour(255,255,255))        
        self.mainSizer.Add(self.instruction, 0,wx.ALL | wx.CENTER, 5)
        
        self.imageCtrl = wx.StaticBitmap(self.panel, wx.ID_ANY, 
                                         wxBitmap)
                
        self.mainSizer.Add(self.imageCtrl, 0, wx.ALL, 5)        
        self.imageCtrl.SetBitmap(wxBitmap)       
        
        
        self.marker = wx.StaticText(self.panel, label='Marker')
        self.marker.SetForegroundColour(wx.Colour(255,255,255))
        self.mainSizer.Add(self.marker, 0, wx.ALL , 5)
        
        self.marker_sld = wx.Slider(self.panel, value = 1, minValue = 10, maxValue = max_markers,
        style = wx.SL_HORIZONTAL|wx.SL_LABELS)
        self.mainSizer.Add(self.marker_sld,1,flag = wx.EXPAND , border = 20)

        self.compactness = wx.StaticText(self.panel, label='Compactness')
        self.compactness.SetForegroundColour(wx.Colour(255,255,255))
        self.mainSizer.Add(self.compactness, 0, wx.ALL , 5)
        self.compactness_float=0.001


        self.compactness_sld = wx.Slider(self.panel, value = 1, minValue = 1, maxValue = 10,
        style = wx.SL_HORIZONTAL|wx.SL_LABELS)
        self.mainSizer.Add(self.compactness_sld,1,flag = wx.EXPAND , border = 20) 

        self.clear_button = wx.Button(self.panel, wx.ID_ANY, 'Clear', (10, 10))
        self.mainSizer.Add(self.clear_button, 0, wx.ALL , 5)
        
        self.input_image_np=image_np_sc
        self.superpixels = watershed(sobel(self.input_image_np), markers=self.marker_sld.GetValue(), 
                                     compactness=self.compactness_sld.GetValue()*self.compactness_float)
        self.boundaries = img_as_ubyte(mark_boundaries(self.input_image_np, self.superpixels, color=self.marker_color))
        self.mask = np.zeros_like(self.boundaries)
        self.display_image = np.copy(self.boundaries)

        self.update_image()
        
        self.clear_button.Bind(wx.EVT_LEFT_DOWN, self.clear_mask)
        self.imageCtrl.Bind(wx.EVT_LEFT_DOWN, self.add_region)
        self.imageCtrl.Bind(wx.EVT_RIGHT_DOWN, self.remove_region)
        self.imageCtrl.Bind(wx.EVT_MIDDLE_DOWN, self.flood_fill)
        self.compactness_sld.Bind(wx.EVT_SLIDER, self.update_superpixels)
        self.marker_sld.Bind(wx.EVT_SLIDER, self.update_superpixels)

        self.panel.SetSizer(self.mainSizer)
        
        self.Show()

    def wximage_to_numpy(self, image):

        arr = np.asarray(image.GetDataBuffer())
        image_np = np.copy(np.reshape(arr, (image.GetWidth(), image.GetHeight(),3)))
        return image_np
        
           

    def clear_mask(self, event):
        """
        Clears the mask and updates the app's displayed image.
        """
        self.mask = np.zeros_like(self.boundaries)
        self.display_image = np.copy(self.boundaries)
        self.update_image()

    def update_image(self):
        """
        Updates the app's displayed image.
        """
        
        wxBitmap= wx.Image(self.W,self.H, self.display_image)
        self.imageCtrl.SetBitmap(wx.Bitmap(wxBitmap))
        

    def update_superpixels(self, event):
        """
        Recomputes superpixels with the user's selected parameters and displays the boundary image in the app.
        """
        
        self.superpixels = watershed(sobel(self.input_image_np), markers=self.marker_sld.GetValue(), 
                                     compactness=self.compactness_sld.GetValue()*self.compactness_float)
        self.boundaries = img_as_ubyte(mark_boundaries(self.input_image_np, self.superpixels, color=self.marker_color))
        self.mask = np.zeros_like(self.boundaries)
        self.display_image = np.copy(self.boundaries)
        self.update_image()

    def add_region(self, event):
        """
        Adds superpixels to the segmentation by dragging the left mouse button.
        """
        
        chosen_region = self.superpixels[event.y, event.x]
        for i in range(3):
            self.mask[:, :, i] = np.where(self.superpixels == chosen_region, 255, self.mask[:, :, i])
            self.display_image[:, :, i] = np.where(self.mask[:, :, i] == 255, 255, self.display_image[:, :, i])
        self.update_image()
        
    def remove_region(self, event):
        """
        Removes superpixels from the segmentation by dragging the right mouse button.
        """
        
        chosen_region = self.superpixels[event.y, event.x]
        for i in range(3):
            self.mask[:, :, i] = np.where(self.superpixels == chosen_region, 0, self.mask[:, :, i])
            self.display_image[:, :, i] = np.where(self.mask[:, :, i] == 0, self.boundaries[:, :, i],
                                                       self.display_image[:, :, i])
        self.update_image()

    def flood_fill(self, event):
        """
        Fills a contour selected by the middle mouse button with the mask.
        """
        
        for i in range(3):
            self.mask[:, :, i] = flood_fill(self.mask[:, :, i], seed_point=(event.y, event.x), new_value=255,
                                                tolerance=1)
            self.display_image[:, :, i] = np.where(self.mask[:, :, i] == 255, 255, self.display_image[:, :, i])
        self.update_image()
        


    
            

if __name__ == '__main__':
    params = {}
    params['inputImagePath'] = '2D_PigSkin.tif'
    params['resultMaskPath'] = '2D_PigSkinMask.tif'
    params['resultObjectPath'] = '2D_PigSkinResult.tif'
    params['TCount']=1
    params['ZCount']=1
    run(params)
