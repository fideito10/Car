import os
import pandas as pd

from src.modules.areanutricion import read_new_google_sheet_to_df
from src.modules.areafisica import cargar_hoja
from src.modules.areamedica import create_dataframe_from_sheet

def cargar_todas_las_areas():
    # --- Nutrición ---
    df_nutricion = read_new_google_sheet_to_df(
        sheet_id='12SqV7eAYpCwePD-TA1R1XOou-nGO3R6QUSHUnxa8tAI',
        target_gid=382913329
    )

    # --- Física ---
    df_fisica = cargar_hoja(
        sheet_id="180ikmYPmc1nxw5UZYFq9lDa0lGfLn_L-7Yb8CmwJAPM",
        nombre_hoja="Base Test"
    )

    # --- Médica ---
    df_medica = create_dataframe_from_sheet(
        sheet_id="1zGyW-M_VV7iyDKVB1TTd0EEP3QBjdoiBmSJN2tK-H7w",
        worksheet_name=None
    )

    return df_nutricion, df_fisica, df_medica

if __name__ == "__main__":
    df_nutricion, df_fisica, df_medica = cargar_todas_las_areas()
    print("Nutrición:", df_nutricion.shape if df_nutricion is not None else "No data")
    print("Física:", df_fisica.shape if df_fisica is not None else "No data")
    print("Médica:", df_medica.shape if df_medica is not None else "No data")