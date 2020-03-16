import os.path
import tkinter as tk
import numpy as np
from PIL import ImageTk, Image
from skimage.io import imread, imsave
from skimage.io import imread
from skimage.filters import sobel
from skimage.segmentation import watershed, mark_boundaries
from skimage.morphology import flood_fill
from skimage.util import img_as_ubyte

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
    image_location = params['inputImagePath']
    result_mask_location = params['resultMaskPath']
    result_object_location = params['resultObjectPath']
    tCount = int(params['TCount'])
    zCount = int(params['ZCount'])
    if not os.path.exists(image_location):
        print(f'Error: {image_location} does not exist')
        return;
        
    if zCount > 1 or tCount > 1:
        print('Currently this only supports 2D images with no time dimension.')
        return
    
    image_data = imread(image_location)
    mask_data = np.empty(shape=image_data.shape, dtype=np.uint8)
    
    mask_data = paint_superpixels(image_data)
    
    imsave(result_mask_location, mask_data)
    imsave(result_object_location, mask_data)

def paint_superpixels(image):
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
    root_ps = tk.Tk()
    root_ps.title('Superpixel Painter')
    painter_app = SuperpixelPainter(root_ps, image=image)
    root_ps.mainloop()
    return painter_app.mask[:, :, 0]


class SuperpixelPainter:
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
    def __init__(self, master, image):
        self.master = master

        self.input_image = image
        max_markers = int(0.01 * (self.input_image.shape[0] * self.input_image.shape[1]))

        user_instructions = 'Drag left mouse button to paint superpixels. Drag right mouse button to erase. ' \
                            'Middle click to fill a contour. Close the app when finished.'
        self.instructions = tk.Label(master, text=user_instructions)
        self.instructions.grid(row=0, column=1, sticky=tk.NW)

        self.markers = tk.Scale(master, label='Markers', orient=tk.VERTICAL, from_=10, to=max_markers, resolution=1)
        self.markers.set(300)
        self.markers.grid(row=1, column=0, sticky=tk.W)

        self.compactness = tk.Scale(master, label='Compactness', orient=tk.VERTICAL, from_=0.001, to=0.01,
                                    resolution=0.001)
        self.compactness.set(0.005)
        self.compactness.grid(row=2, column=0, sticky=tk.W)

        self.clear = tk.Button(master, text='Clear', command=self.clear_mask)
        self.clear.grid(row=3, column=0, sticky=tk.S)

        self.image_label = tk.Label(master)
        self.image_label.grid(row=1, column=1, rowspan=3)

        self.superpixels = watershed(sobel(self.input_image), markers=self.markers.get(), 
                                     compactness=self.compactness.get())
        self.boundaries = img_as_ubyte(mark_boundaries(self.input_image, self.superpixels))
        self.mask = np.zeros_like(self.boundaries)
        self.display_image = np.copy(self.boundaries)

        self.update_image()

        master.bind('<B1-Motion>', self.add_region)
        master.bind('<B3-Motion>', self.remove_region)
        master.bind('<ButtonRelease-1>', self.update_superpixels)
        master.bind('<Button-2>', self.flood_fill)

    def update_image(self):
        """
        Updates the app's displayed image.
        """
        self.display_tk = ImageTk.PhotoImage(Image.fromarray(self.display_image))
        self.image_label.configure(image=self.display_tk)
        self.image_label.image = self.display_tk

    def clear_mask(self):
        """
        Clears the mask and updates the app's displayed image.
        """
        self.mask = np.zeros_like(self.boundaries)
        self.display_image = np.copy(self.boundaries)
        self.update_image()

    def update_superpixels(self, event):
        """
        Recomputes superpixels with the user's selected parameters and displays the boundary image in the app.
        """
        if event.widget in [self.markers, self.compactness]:
            self.superpixels = watershed(sobel(self.input_image), markers=self.markers.get(), 
                                     compactness=self.compactness.get())
            self.boundaries = img_as_ubyte(mark_boundaries(self.input_image, self.superpixels))
            self.mask = np.zeros_like(self.boundaries)
            self.display_image = np.copy(self.boundaries)
            self.update_image()

    def add_region(self, event):
        """
        Adds superpixels to the segmentation by dragging the left mouse button.
        """
        if event.widget is self.image_label:
            chosen_region = self.superpixels[event.y, event.x]
            for i in range(3):
                self.mask[:, :, i] = np.where(self.superpixels == chosen_region, 255, self.mask[:, :, i])
                self.display_image[:, :, i] = np.where(self.mask[:, :, i] == 255, 255, self.display_image[:, :, i])
            self.update_image()

    def remove_region(self, event):
        """
        Removes superpixels from the segmentation by dragging the right mouse button.
        """
        if event.widget is self.image_label:
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
        if event.widget is self.image_label:
            for i in range(3):
                self.mask[:, :, i] = flood_fill(self.mask[:, :, i], seed_point=(event.y, event.x), new_value=255,
                                                tolerance=1)
                self.display_image[:, :, i] = np.where(self.mask[:, :, i] == 255, 255, self.display_image[:, :, i])
            self.update_image()
            

if __name__ == '__main__':
    params = {}
    params['inputImagePath'] = 'test.png'
    params['resultMaskPath'] = 'testResult.png'
    params['resultObjectPath'] = 'testResult.png'
    
    run(params)
