import streamlit as st
import json
import pandas as pd
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List
import gspread
from google.oauth2.service_account import Credentials
import os
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials



def get_google_credentials():
    # Si estamos en Streamlit Cloud, usamos st.secrets
    if "google" in st.secrets:
        return {
            "type": st.secrets["google"]["type"],
            "project_id": st.secrets["google"]["project_id"],
            "private_key_id": st.secrets["google"]["private_key_id"],
            "private_key": st.secrets["google"]["private_key"],
            "client_email": st.secrets["google"]["client_email"],
            "client_id": st.secrets["google"]["client_id"],
            "auth_uri": st.secrets["google"]["auth_uri"],
            "token_uri": st.secrets["google"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["google"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["google"]["client_x509_cert_url"],
            "universe_domain": st.secrets["google"].get("universe_domain", "googleapis.com"),
        }
    # Si estamos local, leemos el archivo
    else:
        cred_path = os.path.join("credentials", "service_account.json")
        with open(cred_path) as f:
            return json.load(f)
def cargar_hoja(sheet_id: str, nombre_hoja: str, rutas_credenciales=None) -> pd.DataFrame:
    """
    Carga una hoja de Google Sheets usando el sheet_id y el nombre de la pestaña.
    """
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    try:
        # Si estamos en Streamlit Cloud, usamos st.secrets
        if "google" in st.secrets:
            creds_info = get_google_credentials()
            credenciales = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
        else:
            if rutas_credenciales is None:
                rutas_credenciales = [
                    "../credentials/service_account.json",
                    "credentials/service_account.json",
                    "C:/Users/dell/Desktop/Car/credentials/service_account.json"
                ]
            credenciales_path = None
            for path in rutas_credenciales:
                if os.path.exists(path):
                    credenciales_path = path
                    break
            if not credenciales_path:
                print("❌ Archivo de credenciales no encontrado")
                return pd.DataFrame()
            credenciales = Credentials.from_service_account_file(credenciales_path, scopes=SCOPES)

        gc = gspread.authorize(credenciales)
        sh = gc.open_by_key(sheet_id)
        worksheet = sh.worksheet(nombre_hoja)
        all_data = worksheet.get_all_values()
        if not all_data:
            print("⚠️ La hoja está vacía")
            return pd.DataFrame()
        columns = all_data[0]
        data_rows = all_data[1:]
        df = pd.DataFrame(data_rows, columns=columns)
        return df

    except Exception as e:
        print(f"❌ Error al cargar la hoja: {e}")
        return pd.DataFrame()

    # Mueve la configuración visual fuera de SCOPES
    
# ...existing code...
    st.markdown("""
        <link href="https://fonts.googleapis.com/css?family=Montserrat:400,700&display=swap" rel="stylesheet">
        <style>
        html, body, [class*="css"] {
            font-family: 'Montserrat', Arial, sans-serif !important;
        }
        .titulo-area-fisica {
            background: #2E86C1;
            color: #fff;
            border-radius: 16px;
            padding: 32px 0 16px 0;
            text-align: center;
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 16px;
        }
        .subtitulo-area-fisica {
            text-align: center;
            color: #2E86C1;
            font-size: 1.2em;
            font-weight: 500;
        }
        </style>
        <div class='titulo-area-fisica'>
            🏋️ ÁREA FÍSICA
        </div>
        <div class='subtitulo-area-fisica'>
            Sistema de Análisis Físico - Club Argentino de Rugby
        </div>
        <hr style='border: 1px solid #2E86C1;'>
    """, unsafe_allow_html=True)
# ...existing code...

    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    credenciales = Credentials.from_service_account_file(
        credenciales_path,
        scopes=SCOPES
    )
    gc = gspread.authorize(credenciales)
    sh = gc.open_by_key(sheet_id)
    worksheet = sh.worksheet(nombre_hoja)
    all_data = worksheet.get_all_values()
    if not all_data:
        print("⚠️ La hoja está vacía")
        return pd.DataFrame()
    columns = all_data[0]
    data_rows = all_data[1:]
    df = pd.DataFrame(data_rows, columns=columns)
    return df


def resaltar_valores(s):
    # Reemplaza coma por punto y convierte a float
    s_float = pd.to_numeric(s.astype(str).str.replace(',', '.'), errors='coerce')
    is_high = s_float > s_float.quantile(0.75)
    is_low = s_float < s_float.quantile(0.25)
    return ['background-color: #b6fcd5' if h else 'background-color: #ffb6b6' if l else '' for h, l in zip(is_high, is_low)]


def physical_area():
    
    sheet_id = "180ikmYPmc1nxw5UZYFq9lDa0lGfLn_L-7Yb8CmwJAPM"
    nombre_hoja = "Base Test"
    df = cargar_hoja(sheet_id, nombre_hoja)
    if df.empty:
        st.error("No se pudo cargar la hoja 'Base Test'.")
        return

    categoria_col = "Categoría"
    jugador_col = "Nombre y Apellido"
    test_col = "Test"
    subtest_col = "Subtest"
    valor_col = "valor"
    fecha_col = "Marca temporal"
    posicion_col = "Posición del jugador"

    st.markdown("### 🔎 Filtros Interactivos")
    filtros = {}

    categorias = sorted(df[categoria_col].dropna().unique())
    filtros["categoria"] = st.selectbox("Selecciona la categoría", options=categorias)

    df_cat = df[df[categoria_col] == filtros["categoria"]]
    tests = sorted(df_cat[test_col].dropna().unique())
    filtros["test"] = st.selectbox("Selecciona el test físico", options=tests)

    df_test = df_cat[df_cat[test_col] == filtros["test"]]
    jugadores = sorted(df_test[jugador_col].dropna().unique())
    filtros["jugador"] = st.multiselect("Selecciona jugador/es", options=jugadores)

    df_jug = df_test[df_test[jugador_col].isin(filtros["jugador"])] if filtros["jugador"] else df_test
    subtests = sorted(df_jug[subtest_col].dropna().unique())
    filtros["subtest"] = st.selectbox("Selecciona el subtest", options=subtests)

    df_filtrado = df_jug[df_jug[subtest_col] == filtros["subtest"]]

    df_filtrado[valor_col] = df_filtrado[valor_col].astype(str).str.replace(',', '.')
    df_filtrado[valor_col] = pd.to_numeric(df_filtrado[valor_col], errors='coerce')
    # ----------------------------

    mostrar_tabla_estilizada(df_filtrado, valor_col, test_col, subtest_col)
    



def mostrar_tabla_estilizada(df, valor_col, test_col, subtest_col):
    # Aplica gradiente en columna "valor"
    styled_df = (
        df.style
        .background_gradient(subset=[valor_col], cmap='Blues')
        .set_properties(**{
            'text-align': 'center',
            'font-family': 'Montserrat, Arial',
            'font-size': '1em',
            'border-radius': '8px',
            'border': '1px solid #e1e1e1'
        })
        .set_table_styles([
            {'selector': 'th', 'props': [('font-size', '1.1em'), ('text-align', 'center'), ('background-color', '#eaf6fb'), ('color', '#2E86C1')]},
            {'selector': 'td', 'props': [('text-align', 'center'), ('font-family', 'Montserrat, Arial'), ('font-size', '1em')]},
            {'selector': 'table', 'props': [('border-radius', '8px'), ('border', '1px solid #e1e1e1'), ('background-color', '#fff')]}
        ])
    )

    st.markdown("### 📋 Datos filtrados y estilizados:")
    st.dataframe(styled_df, use_container_width=True)