import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tkinter as tk
from skimage import io
from skimage.measure import regionprops

"""
Plots a horizontal or vertical line through the middle of a labeled image from Aivia,
then extracts images and measurements from the labels only touching those lines.

Instructions
------------
1. Load a tiled mosaic or series of images as individual time points in Aivia.
2. Create an object set.
3. Export the object set as a 16 bit labeled mask.
4. Run this script.
5. Select the 16 bit labeled mask that was exported from Aivia as the Input File.
6. Browse to choose a directory to contain the ouput.
7. Select a vertical or horizontal orientation of the line.
8. Apply the processing.


Results are output as plots showing before/after the label filtering along
with a single Excel file containing some measures for all of the objects.

In the resulting Excel file, the "Image Index" column describes from which image in
the series the measures came from. The "Object Index" column corresponds to the labels
assigned to each object in Aivia.

Requirements
------------
numpy
pandas
matplotlib
scikit-image

"""


class InspectLineIntersections:
    """
    Plots a horizontal or vertical line through the middle of a labeled image from Aivia,
    then extracts images and measurements from the labels only touching those lines.

    Must be used with an image where the dimensions are:
    (Y, X, T)
    and the T channel represents frames from within a mosaic instead of physical time points.
    """
    def __init__(self, master):
        self.master = master

        self.title = 'Inspect Labels Touching Lines'

        self.input_image_label = tk.Label(master, text='Input Image')
        self.input_image_label.grid(row=0, column=0, sticky=tk.W)

        self.input_image = tk.StringVar()
        self.input_image_path = tk.Entry(master, textvariable=self.input_image)
        self.input_image_path.grid(row=0, column=1, columnspan=7, sticky=tk.W+tk.E)

        self.input_image_button = tk.Button(master, text='Browse',
                                            command=self.get_input_image)
        self.input_image_button.grid(row=0, column=7, sticky=tk.E)

        self.output_dir_label = tk.Label(master, text='Output Directory')
        self.output_dir_label.grid(row=1, column=0, sticky=tk.W)

        self.output_dir = tk.StringVar()
        self.output_dir_path = tk.Entry(master, textvariable=self.output_dir)
        self.output_dir_path.grid(row=1, column=1, columnspan=7, sticky=tk.W+tk.E)

        self.output_dir_button = tk.Button(master, text='Browse',
                                           command=self.get_output_dir)
        self.output_dir_button.grid(row=1, column=7, sticky=tk.E)

        self.line_orientation_label = tk.Label(master, text='Line Orientation')
        self.line_orientation_label.grid(row=2, column=0, sticky=tk.W)

        self.orientation = tk.IntVar()
        self.vertical_line_option = tk.Radiobutton(master, text='Vertical',
                                                   variable=self.orientation, value=1)
        self.vertical_line_option.grid(row=2, column=1, stick=tk.W)
        self.vertical_line_option.select()
        self.horizontal_line_option = tk.Radiobutton(master, text='Horizontal',
                                                     variable=self.orientation, value=2)
        self.horizontal_line_option.grid(row=2, column=2, stick=tk.W)

        self.process_button = tk.Button(master, text='Batch Process', command=self.process_frames)
        self.process_button.grid(row=2, column=7, sticky=tk.E)

    def get_input_image(self):
        """
        Browse for the input image.
        """
        ifp = tk.filedialog.askopenfilename(title='Select labels from Aivia',
                                            filetype=(('TIF', '*.tif'), ('All files', '*')))
        self.input_image_path.delete(0, 'end')
        self.input_image_path.insert(0, ifp)

    def get_output_dir(self):
        """
        Browse for the output directory.
        """
        ofd = tk.filedialog.askdirectory(title='Select an output directory') + '/'
        self.output_dir_path.delete(0, 'end')
        self.output_dir_path.insert(0, ofd)

    def process_frames(self):
        """
        Perform line inspection processing on multiple frames within one Aivia image.
        """
        masks = io.imread(os.path.abspath(self.input_image.get()))
        
        measures = ['Image Index',  # Linear position in the mosaic
                    'Object Index', # Object label from Aivia
                    'Length',       # Longitudinal length of the major axis
                    'Breadth',      # Cross-sectional lenght of the major axis
                    'Aspect Ratio', # Length / Breadth
                    'Circularity',  # (4*pi*area) / (perimeter^2)
                    ]
        
        all_measures = pd.DataFrame(columns=measures)
        
        for f in range(0, masks.shape[2]):
    
            frame = masks[:, :, f]
            frame_labels = np.zeros(shape=frame.shape, dtype=frame.dtype)
            
            if self.orientation.get() == 1:     # Vertical case
                line_idx = int(masks.shape[1]/2)
                line_arr = frame[:, line_idx]
            else:                               # Horizontal case
                line_idx = int(masks.shape[0]/2)
                line_arr = frame[line_idx, :]

            values_on_line = np.unique(line_arr)

            for v in values_on_line:
                if v==0:
                    pass
                else:
                    frame_labels = frame_labels + np.where(frame==v, v, 0)

            frame_labels = frame_labels.astype(frame.dtype)
            measurements = regionprops(frame_labels)

            fig, ax = plt.subplots(1, 2)
            fig.set_size_inches(8, 6)
            cmap = plt.cm.Set1
            cmap.set_under(color='black')
            ax[0].imshow(frame, cmap=cmap, vmin=0.1)
            ax[0].set_title('Labels from Aivia')
            ax[1].imshow(frame_labels, cmap=cmap, vmin=0.1)
            ax[1].set_title('Labels Touching Line')
            if self.orientation.get() == 1:
                ax[0].axvline(line_idx, color='w')
                ax[1].axvline(line_idx, color='w')
            else:
                ax[0].axhline(line_idx, color='w')
                ax[1].axhline(line_idx, color='w')
            plt.savefig(os.path.join(self.output_dir.get(), f"Image Index {f:03}.png"))
            plt.close()

            for prop in measurements:
                if prop.minor_axis_length == 0:
                    aspect_ratio = 1.0
                else:
                    aspect_ratio = prop.major_axis_length / prop.minor_axis_length
                frame_measures = {'Image Index': int(f),
                                  'Object Index': int(prop.label),
                                  'Length': prop.major_axis_length,
                                  'Breadth': prop.minor_axis_length,
                                  'Aspect Ratio': aspect_ratio,
                                  'Circularity': (4 * np.pi * prop.area) / (prop.perimeter**2)
                                  }
                all_measures = all_measures.append(frame_measures, ignore_index=True)

        all_measures.to_excel(os.path.join(self.output_dir.get(), "Measures.xlsx"))


if __name__ == '__main__':
    root_ps = tk.Tk()
    root_ps.configure(bg='#232121')
    root_ps.option_add('*HighlightThickness', 0)
    root_ps.option_add('*Background', '#232121')
    root_ps.option_add('*Foreground', '#F1E7E3')
    root_ps.option_add('*Font', '{MS Sans Serif}')
    lineinspectionapp = InspectLineIntersections(root_ps)
    root_ps.mainloop()
