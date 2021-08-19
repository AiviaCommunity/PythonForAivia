import os.path
import shlex
import subprocess
import imagecodecs
import numpy as np
from tifffile import imread, imwrite
from skimage import transform, img_as_uint, img_as_ubyte
import tkinter as tk

aivia_version = 'Aivia 10.0.0'

"""
Scales the input channel up or down (isotropic factor). Option for interpolation is in the code.
Works only for 2D/3D (not timelapses) and for single channels.
IMPORTANT: This scripts works for Aivia 10 or more.

Documentation
-------------
https://scikit-image.org/docs/stable/api/skimage.transform.html#skimage.transform.rescale

Requirements
------------
numpy (comes with Aivia installer)
scikit-image (comes with Aivia installer)
tkinter (comes with Aivia installer, but in 10.0.0, needs manual install with 'pip install tk')
imagecodecs (comes with Aivia installer)
tifffile (comes with Aivia installer)

Parameters
----------
Input channel:
    Input channel to be scaled.

Returns
-------
New channel in original image:
    Returns an empty channel.

New image:
    Opens Aivia to display the new scaled image.

"""

default_scale_factor_XY = 2
default_scale_factor_Z = 1
interpolation_mode = 1  # 0: Nearest-neighbor, 1: Bi-linear , 2: Bi-quadratic, 3: Bi-cubic, 4: Bi-quartic, 5: Bi-quintic

# automatic parameters
aivia_path = 'C:\\Program Files\\Leica Microsystems\\' + aivia_version + '\\Aivia.exe'


# [INPUT Name:inputImagePath Type:string DisplayName:'Input Channel']
# [OUTPUT Name:resultPath Type:string DisplayName:'Duplicate of input']
def run(params):
    image_location = params['inputImagePath']
    result_location = params['resultPath']
    zCount = int(params['ZCount'])
    tCount = int(params['TCount'])
    if not os.path.exists(image_location):
        print(f"Error: {image_location} does not exist")
        return

    if not os.path.exists(aivia_path):
        print(f"Error: {aivia_path} does not exist")
        return

    image_data = imread(image_location)
    dims = image_data.shape
    print('-- Input dimensions (expected (Z), Y, X): ', np.asarray(dims), ' --')

    # Checking image is not 2D+t or 3D+t
    if len(dims) > 3 or (len(dims) == 3 and tCount > 1):
        print('Error: Cannot handle timelapses yet.')
        return

    output_data = np.empty_like(image_data)

    # ------------------- defining a class for the GUI ----------------------------
    class GUI:
        def __init__(self, master, def_scalef_xy, def_scalef_z, img_data, res_path, interpol):
            self.master = master
            self.pane = tk.Frame(master)

            master.title('Scale image')
            self.tmp_path = ''
            self.scale_order = interpol

            self.scale_direction = tk.StringVar()
            self.scale_dir_option1 = tk.Radiobutton(master, text='Upscale', variable=self.scale_direction, value='up')
            self.scale_dir_option1.grid(row=1, column=1, stick=tk.W)
            self.scale_dir_option2 = tk.Radiobutton(master, text='Downscale', variable=self.scale_direction,
                                                    value='down')
            self.scale_dir_option2.grid(row=1, column=2, stick=tk.W)
            self.scale_dir_option2.select()

            self.scale_factor_xy_lbl = tk.Label(master, text='Scaling Factor XY: ')
            self.scale_factor_xy_lbl.grid(row=2, column=1, stick=tk.W)
            self.scale_factor_xy = tk.StringVar()
            self.scale_factor_xy.set(def_scalef_xy)
            self.scale_fact_option = tk.Entry(master, textvariable=self.scale_factor_xy, width=10)
            self.scale_fact_option.grid(row=2, column=2, stick=tk.W)

            self.scale_factor_z_lbl = tk.Label(master, text='Scaling Factor Z: ')
            self.scale_factor_z_lbl.grid(row=3, column=1, stick=tk.W)
            self.scale_factor_z = tk.StringVar()
            self.scale_factor_z.set(def_scalef_z)
            self.scale_fact_option = tk.Entry(master, textvariable=self.scale_factor_z, width=10)
            self.scale_fact_option.grid(row=3, column=2, stick=tk.W)

            self.process_lbl = tk.Label(master, text='')
            self.process_lbl.grid(row=4, column=1, stick=tk.W)
            self.process_button = tk.Button(master, text='Process', command=lambda: self.process_frames(img_data, res_path))
            self.process_button.grid(row=4, column=4, sticky=tk.E, pady=5)

        def process_frames(self, img_data, res_path):
            """
            Performs transform depending on input parameters
            """
            self.process_lbl['text'] = '... processing ...'
            self.pane.update_idletasks()

            scale_factor_xy = float(self.scale_factor_xy.get())
            scale_factor_z = float(self.scale_factor_z.get())
            if self.scale_direction.get() == 'down':
                scale_factor_xy = 1 / scale_factor_xy
                scale_factor_z = 1 / scale_factor_z

            # Defining axes for output metadata and scale factor variable
            final_scale = None
            if tCount == 1 and zCount > 1:         # 3D
                axes = 'YXZ'
                final_scale = (scale_factor_z, scale_factor_xy, scale_factor_xy)

            elif tCount == 1 and zCount == 1:      # 2D
                axes = 'YX'
                final_scale = scale_factor_xy

            scaled_img = transform.rescale(img_data, final_scale, self.scale_order)

            # Formatting result array
            if img_data.dtype is np.dtype('u2'):
                out_data = img_as_uint(scaled_img)
            else:
                out_data = img_as_ubyte(scaled_img)

            self.process_lbl['text'] = '... processed ...'
            self.pane.update_idletasks()

            self.tmp_path = res_path.replace('.tif', '-tmp.tif')
            imwrite(self.tmp_path, out_data, photometric='minisblack', metadata={'axes': axes})

            self.master.quit()

    # -------------------- run GUI ---------------------------
    root_ps = tk.Tk()
    root_ps.configure(bg='#232121')
    root_ps.option_add('*HighlightThickness', 0)
    root_ps.option_add('*Background', '#232121')
    root_ps.option_add('*Foreground', '#F1E7E3')
    root_ps.option_add('*Font', '{MS Sans Serif}')
    runTransform = GUI(root_ps, default_scale_factor_XY, default_scale_factor_Z, image_data, result_location,
                       interpolation_mode)
    root_ps.mainloop()

    # Dummy save
    # imwrite(result_location, output_data)

    # Run external program
    temp_location = runTransform.tmp_path
    cmdLine = 'start \"\" \"' + aivia_path + '\" \"' + temp_location + '\"'
    # cmdLine = 'start \"\" \"' + IJ_path + '\" \"' + temp_location + '\"'

    args = shlex.split(cmdLine)
    subprocess.run(args, shell=True)


if __name__ == '__main__':
    params = {'inputImagePath': 'D:\\python-tests\\3D-image.aivia.tif',
              'resultPath': 'D:\\python-tests\\scaled.tif',
              'TCount': 1,
              'ZCount': 51}

    run(params)

# CHANGELOG
# v1_00: - scaling in XYZ with same factor
# v1_10: - scaling in XY and Z are now independent
