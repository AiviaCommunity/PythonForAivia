from seaborn import color_palette

def seaborn_to_aivia_coloring(desired_palette, output_dir):
    """
    Converts a named palette from seaborn or matplotlib into a LUT compatible with Aivia
    channels. This LUT file is written to the directory provided by the user.

    If the user is unsure what palettes are available, they can enter the sns.color_palettes()
    method into a Python console with an obviously incorrect argument, like:

    > sns.color_palettes('there is no way a palette can be named this')

    This will cause a ValueError which returns the list of possible palettes.
    
    To load the resulting file into Aivia, right-click a channel in Aivia 
    and navigate to "Advanced Coloring" > "Load Coloring" > then choose the output file.

    Requirements
    ------------
    seaborn

    Parameters
    ----------
    desired_palette : string
        Name of the palette that you want to convert.

    output_dir : string
        Path to the directory where you want the file to be written.
    """
    
    palettes = ['Accent', 'Accent_r', 'Blues', 'Blues_r', 'BrBG', 'BrBG_r', 'BuGn',
                'BuGn_r', 'BuPu', 'BuPu_r', 'CMRmap', 'CMRmap_r', 'Dark2', 'Dark2_r',
                'GnBu', 'GnBu_r', 'Greens', 'Greens_r', 'Greys', 'Greys_r', 'OrRd',
                'OrRd_r', 'Oranges', 'Oranges_r', 'PRGn', 'PRGn_r', 'Paired',
                'Paired_r', 'Pastel1', 'Pastel1_r', 'Pastel2', 'Pastel2_r', 'PiYG',
                'PiYG_r', 'PuBu', 'PuBuGn', 'PuBuGn_r', 'PuBu_r', 'PuOr', 'PuOr_r',
                'PuRd', 'PuRd_r', 'Purples', 'Purples_r', 'RdBu', 'RdBu_r', 'RdGy',
                'RdGy_r', 'RdPu', 'RdPu_r', 'RdYlBu', 'RdYlBu_r', 'RdYlGn', 'RdYlGn_r',
                'Reds', 'Reds_r', 'Set1', 'Set1_r', 'Set2', 'Set2_r', 'Set3', 'Set3_r',
                'Spectral', 'Spectral_r', 'Wistia', 'Wistia_r', 'YlGn', 'YlGnBu',
                'YlGnBu_r', 'YlGn_r', 'YlOrBr', 'YlOrBr_r', 'YlOrRd', 'YlOrRd_r',
                'afmhot', 'afmhot_r', 'autumn', 'autumn_r', 'binary', 'binary_r',
                'bone', 'bone_r', 'brg', 'brg_r', 'bwr', 'bwr_r', 'cividis',
                'cividis_r', 'cool', 'cool_r', 'coolwarm', 'coolwarm_r', 'copper',
                'copper_r', 'cubehelix', 'cubehelix_r', 'flag', 'flag_r', 'gist_earth',
                'gist_earth_r', 'gist_gray', 'gist_gray_r', 'gist_heat', 'gist_heat_r',
                'gist_ncar', 'gist_ncar_r', 'gist_rainbow', 'gist_rainbow_r',
                'gist_stern', 'gist_stern_r', 'gist_yarg', 'gist_yarg_r', 'gnuplot',
                'gnuplot2', 'gnuplot2_r', 'gnuplot_r', 'gray', 'gray_r', 'hot', 'hot_r',
                'hsv', 'hsv_r', 'icefire', 'icefire_r', 'inferno', 'inferno_r',
                # leave out 'jet', 'jet_r', b/c of snarky error
                'magma', 'magma_r', 'mako', 'mako_r', 'nipy_spectral',
                'nipy_spectral_r', 'ocean', 'ocean_r', 'pink', 'pink_r', 'plasma',
                'plasma_r', 'prism', 'prism_r', 'rainbow', 'rainbow_r', 'rocket',
                'rocket_r', 'seismic', 'seismic_r', 'spring', 'spring_r', 'summer',
                'summer_r', 'tab10', 'tab10_r', 'tab20', 'tab20_r', 'tab20b',
                'tab20b_r', 'tab20c', 'tab20c_r', 'terrain', 'terrain_r', 'twilight',
                'twilight_r', 'twilight_shifted', 'twilight_shifted_r', 'viridis',
                'viridis_r', 'vlag', 'vlag_r', 'winter', 'winter_r']

    if desired_palette not in palettes:
        print(f"{desired_palette} is not a possible option.")
        response = input(f"List possible options? Y/n")
        if reponse.lower() == 'y':
            for p in palettes:
                print(p)
        else:
            pass
    else:
        f = open(f"{output_dir}/{desired_palette} colors.txt", 'w+')
        f.write(f"\"{desired_palette} colors\"\n")
        for c, color in enumerate(color_palette(desired_palette, 128).as_hex()):
            if c*2 < 128:
                f.write(f"{int((c)*2):3d} {color.upper()[-6:]}\n")
            else:
                f.write(f"{int((c)*2)+1:3d} {color.upper()[-6:]}\n")
        f.close()