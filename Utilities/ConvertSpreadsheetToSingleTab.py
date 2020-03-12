import os
import pandas as pd


def aivia_spreadsheet_to_table(aivia_excel_file):
    """
    Convert a multi-tab spreadsheet exported from Aivia into a single tab.
    
    WARNING: This currently works only under the following conditions:
        - The file was exported from Aivia as an Excel file (not CSV)
        - There is no time dimension
        - The default row/column ordering was not changed at export.
    
    The converted file will be saved with the same name as the original but with
    "..._formatted" appended to the end.
        
    Requirements
    ------------
    pandas
    openpyxl
    xlrd

    (openpyxl and xlrd are Pandas requirements, but are not always
    installed with it. Install them explicitly if you receive errors.)
    
    Parameters
    ----------
    aivia_excel_file : string
        Path to the Excel file exported from Aivia.
    
    Returns
    -------
    DataFrame  
        Data from the spreadsheet converted to a Pandas DataFrame.
        
    """
    xl_file = os.path.abspath(aivia_excel_file)
    output_basename = '{}_formatted.xlsx'.format(os.path.basename(xl_file).split('.')[0])
    output_file = os.path.join(os.path.dirname(xl_file), output_basename)
    
    df_raw = pd.read_excel(xl_file, sheet_name=None)
    df_clean = pd.DataFrame()
    df_temp = pd.DataFrame()

    for k in df_raw.keys():
        # Don't need the summary tab if included
        if k == 'Summary':
            pass
        # Create a blank dataframe with appropriate columns
        elif k != 'Summary' and df_clean.empty is True:
            df_clean = df_raw[k]
            # Determines what type of Aivia objects (i.e. Mesh, Slice of Cell, etc.)
            object_type = str(df_raw[k].iloc[0][0])
            object_type = ' '.join([an for an in object_type.split() if an.isalpha()])
            df_clean.columns = [object_type, k]
        # Fill the dataframe
        else:
            df_temp = df_raw[k]
            df_temp.columns = [object_type, k]
            df_clean = pd.merge(df_clean, df_temp, on=object_type)

    df_clean.to_excel(output_file)
    return df_clean
