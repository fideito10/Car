import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime
from google.oauth2.service_account import Credentials
from plotly.subplots import make_subplots
import gspread
import re
import json


# ✅ FUNCIÓN PARA IMPORTAR CUANDO SE NECESITE
def get_areamedica_functions():
    """Importa funciones de areamedica solo cuando se necesiten"""
    try:
        from areamedica import append_google_sheet_row, conectar_base_central
        return append_google_sheet_row, conectar_base_central
    except ImportError as e:
        st.warning(f"⚠️ No se pudo importar de areamedica: {e}")
        return None, None

def conectar_base_central():
    """
    Conecta a la Base Central de jugadores desde Google Sheets.
    Devuelve lista de jugadores con sus datos básicos.
    """
    try:
        from areamedica import read_google_sheet_with_headers
        
        result = read_google_sheet_with_headers(
            sheet_id='1LW8nlaIdJ_6bCnrqpMJW5X27Dhr78gRnhLHwKj6DV7E',
            worksheet_name=None
        )
        
        if not result or not result.get('success'):
            st.error(f"❌ Error conectando a Base Central: {result.get('error', 'Error desconocido')}")
            return []
        
        data = result.get('data', [])
        if not data:
            st.warning("⚠️ Base Central sin datos")
            return []
        
        # Procesar datos de jugadores
        jugadores = []
        for registro in data:
            nombre = (registro.get('Nombre', '').strip() + ' ' + registro.get('Apellido', '').strip()).strip()
            if not nombre or nombre == ' ':
                nombre = registro.get('Nombre y Apellido', '').strip()
            
            dni = str(registro.get('DNI', registro.get('dni', ''))).strip()
            
            jugador = {
                'nombre': nombre,
                'dni': dni,
                'categoria': registro.get('Categoria', registro.get('categoria', 'Sin Categoría')).strip(),
                'posicion': registro.get('Posicion', registro.get('posicion', '')).strip(),
                'telefono': registro.get('Teléfono', registro.get('telefono', '')).strip(),
                'email': registro.get('Email', registro.get('email', '')).strip(),
                'estado': registro.get('Estado', 'Activo').strip()
            }
            
            if jugador['nombre'] and jugador['dni']:
                jugadores.append(jugador)
        
        return jugadores
        
    except ImportError:
        st.error("❌ No se puede importar areamedica.py - Verifica la ruta")
        return []
    except Exception as e:
        st.error(f"❌ Error en conectar_base_central: {str(e)}")
        return []


def guardar_datos_nutricion_en_google_sheets(row_data, sheet_id, worksheet_name):
    """
    Guarda una fila de datos de nutrición en Google Sheets.
    """
    try:
        # ✅ IMPORTACIÓN LAZY
        append_google_sheet_row, _ = get_areamedica_functions()
        
        if append_google_sheet_row is None:
            st.error("❌ No se pudo cargar la función de guardado")
            return False
        
        google_creds = get_google_credentials()
        if not google_creds:
            st.error("❌ No se pudieron obtener las credenciales de Google")
            return False
        
        # ✅ AGREGAR ESTE CÓDIGO QUE FALTA:
        result = append_google_sheet_row(
            sheet_id=sheet_id,
            worksheet_name=worksheet_name,
            row_data=row_data,
            credentials_dict=google_creds
        )
        
        # Manejo flexible del resultado (puede ser bool o dict)
        if isinstance(result, bool):
            if result:
                st.success("✅ Datos guardados en Google Sheets")
                return True
            else:
                st.error("❌ Error guardando datos: operación fallida")
                return False
        elif isinstance(result, dict):
            if result.get('success'):
                st.success("✅ Datos guardados en Google Sheets")
                return True
            else:
                error_msg = result.get('error', 'Error desconocido')
                st.error(f"❌ Error guardando datos: {error_msg}")
                return False
        else:
            st.error(f"❌ Respuesta inesperada: {result}")
            return False
            
    except Exception as e:
        st.error(f"❌ Error guardando en Google Sheets: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return False
       

    """
    Función principal - Lee categorías y jugadores de BASE CENTRAL
    """
    # Inicializar session_state
    if 'mostrar_formulario_nuevo' not in st.session_state:
        st.session_state['mostrar_formulario_nuevo'] = False
    if 'jugador_para_reporte' not in st.session_state:
        st.session_state['jugador_para_reporte'] = None
    
    st.markdown("""
    <div style="background: linear-gradient(90deg, #4CAF50 0%, #45a049 100%); 
                padding: 2rem; border-radius: 10px; margin-bottom: 2rem;">
        <h1 style="color: white; text-align: center; margin: 0;">
            🥗 ÁREA DE NUTRICIÓN
        </h1>
        <p style="color: white; text-align: center; margin: 0.5rem 0 0 0; font-size: 1.2rem;">
            Sistema de Análisis Nutricional - Club Argentino de Rugby
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # ✅ LLAMAR DIRECTAMENTE - NO IMPORTAR
    jugadores_base_central = conectar_base_central()  # Ya está definida arriba
    df_nutricion = read_new_google_sheet_to_df()
    
    if not jugadores_base_central:
        st.error("❌ No se pudieron cargar los jugadores de la Base Central")
        st.stop()
        
        
def get_google_credentials():
    """
    Obtiene las credenciales de Google de forma segura desde st.secrets o archivo local
    """
    try:
        # Primero intentar obtener desde st.secrets (para Streamlit Cloud)
        if hasattr(st, 'secrets') and "gcp_service_account" in st.secrets:
            return dict(st.secrets["gcp_service_account"])
    except Exception:
        pass
    
    # Si estamos local o no hay secrets, leer archivo
    try:
        possible_paths = [
            "credentials/service-account-key.json",  # 👈 AGREGADO
            "../credentials/service-account-key.json",  # 👈 AGREGADO
            "credentials/service_account.json",
            "../credentials/service_account.json", 
            "C:/Users/dell/Desktop/Car/credentials/service_account.json"
        ]
        
        for cred_path in possible_paths:
            if os.path.exists(cred_path):
                with open(cred_path) as f:
                    return json.load(f)
        
        raise FileNotFoundError("No se encontró archivo de credenciales")
        
    except Exception as e:
        st.error(f"❌ Error cargando credenciales: {e}")
        return None
        
def read_new_google_sheet_to_df(
    sheet_id='12SqV7eAYpCwePD-TA1R1XOou-nGO3R6QUSHUnxa8tAI',
    target_gid=382913329,
    credentials_paths=None
):
    """
    Lee un Google Sheet específico y devuelve un DataFrame de pandas.
    """
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    try:
        # Obtener credenciales usando la función mejorada
        creds_info = get_google_credentials()
        
        if creds_info is None:
            st.error("❌ No se pudieron cargar las credenciales de Google")
            return None
        
        # Crear credenciales desde la información obtenida
        credentials = Credentials.from_service_account_info(creds_info, scopes=SCOPES)

        gc = gspread.authorize(credentials)
        sh = gc.open_by_key(sheet_id)

        # Obtener la hoja de trabajo específica por GID
        worksheet = None
        for sheet in sh.worksheets():
            if str(sheet.id) == str(target_gid):
                worksheet = sheet
                break

        if worksheet is None:
            st.error(f"❌ No se encontró la hoja con GID: {target_gid}")
            return None

        # Leer todos los datos
        data = worksheet.get_all_records()

        if not data:
            st.warning("⚠️ La hoja está vacía")
            return pd.DataFrame()

        # Convertir a DataFrame
        df = pd.DataFrame(data)

        # Limpiar datos vacíos
        df = df.dropna(how='all')
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

        return df

    except gspread.exceptions.SpreadsheetNotFound:
        st.error("❌ Google Sheet no encontrado. Verifica el ID y permisos.")
        return None
    except gspread.exceptions.APIError as e:
        st.error(f"❌ Error de API: {e}. Verifica que hayas compartido el sheet con la cuenta de servicio.")
        return None
    except Exception as e:
        st.error(f"❌ Error al conectar con Google Sheets: {str(e)}")
        st.info("🔧 Verifica que:")
        st.info("• El archivo de credenciales sea válido")
        st.info("• El Sheet ID sea correcto")
        st.info("• La cuenta de servicio tenga permisos")
        return None


def enriquecer_datos_nutricion_con_base_central(df_nutricion, jugadores_base_central):
    """
    Enriquece los datos de nutrición con información de la Base Central.
    Completa DNI, Categoría, Posición si están vacíos.
    """
    if df_nutricion.empty or not jugadores_base_central:
        return df_nutricion
    
    df = df_nutricion.copy()
    
    # Crear diccionario para búsqueda rápida por nombre normalizado
    jugadores_dict = {}
    for j in jugadores_base_central:
        nombre_normalizado = j['nombre'].lower().strip()
        jugadores_dict[nombre_normalizado] = j
    
    # Procesar cada fila
    for idx, row in df.iterrows():
        nombre_jugador = str(row.get('Nombre y Apellido', '')).lower().strip()
        
        if nombre_jugador in jugadores_dict:
            datos_bc = jugadores_dict[nombre_jugador]
            
            # Rellenar DNI si existe la columna y está vacío
            if 'DNI' in df.columns:
                if pd.isna(df.at[idx, 'DNI']) or str(df.at[idx, 'DNI']).strip() == '':
                    df.at[idx, 'DNI'] = datos_bc['dni']
            else:
                # Si no existe la columna DNI, crearla
                if 'DNI' not in df.columns:
                    df['DNI'] = ''
                df.at[idx, 'DNI'] = datos_bc['dni']
            
            # Rellenar Categoría si existe la columna y está vacía
            if 'Categoría' in df.columns:
                if pd.isna(df.at[idx, 'Categoría']) or str(df.at[idx, 'Categoría']).strip() == '':
                    df.at[idx, 'Categoría'] = datos_bc['categoria']
            else:
                # Si no existe la columna Categoría, crearla
                if 'Categoría' not in df.columns:
                    df['Categoría'] = ''
                df.at[idx, 'Categoría'] = datos_bc['categoria']
            
            # Rellenar Posición si existe la columna y está vacía
            if 'Posición del jugador' in df.columns:
                if pd.isna(df.at[idx, 'Posición del jugador']) or str(df.at[idx, 'Posición del jugador']).strip() == '':
                    df.at[idx, 'Posición del jugador'] = datos_bc['posicion']
            else:
                # Si no existe la columna, crearla
                if 'Posición del jugador' not in df.columns:
                    df['Posición del jugador'] = ''
                df.at[idx, 'Posición del jugador'] = datos_bc['posicion']
    
    return df
    
 
def guardar_datos_nutricion_en_google_sheets(row_data, sheet_id, worksheet_name):
    """
    Guarda una fila de datos de nutrición en Google Sheets.
    """
    try:
        from areamedica import append_google_sheet_row
        
        google_creds = get_google_credentials()
        if not google_creds:
            st.error("❌ No se pudieron obtener las credenciales de Google")
            return False
        
        result = append_google_sheet_row(
            sheet_id=sheet_id,
            worksheet_name=worksheet_name,
            row_data=row_data,
            credentials_dict=google_creds
        )
        
        # Manejo flexible del resultado (puede ser bool o dict)
        if isinstance(result, bool):
            # Si retorna booleano directamente
            if result:
                st.success("✅ Datos guardados en Google Sheets")
                return True
            else:
                st.error("❌ Error guardando datos: operación fallida")
                return False
        elif isinstance(result, dict):
            # Si retorna diccionario
            if result.get('success'):
                st.success("✅ Datos guardados en Google Sheets")
                return True
            else:
                error_msg = result.get('error', 'Error desconocido')
                st.error(f"❌ Error guardando datos: {error_msg}")
                return False
        else:
            st.error(f"❌ Respuesta inesperada: {result}")
            return False
            
    except Exception as e:
        st.error(f"❌ Error guardando en Google Sheets: {str(e)}")
        return False
 




def crear_formulario_nutricion_nuevo_jugador(jugadores_base_central, jugador_preseleccionado=None):
    """
    Crea un formulario para registrar un nuevo jugador en nutrición.
    Respeta los datos de la Base Central y no permite modificarlos.
    """
    st.markdown("### 📝 Registrar Nuevo Reporte de Nutrición")
    
    # Crear lista de nombres de la base central
    nombres_disponibles = sorted([j['nombre'] for j in jugadores_base_central])
    
    # Determinar el índice del jugador preseleccionado
    indice_default = 0
    if jugador_preseleccionado and jugador_preseleccionado in nombres_disponibles:
        indice_default = nombres_disponibles.index(jugador_preseleccionado)
    
    with st.form("formulario_nuevo_jugador_nutricion"):
        col1, col2 = st.columns(2)
        
        with col1:
            nombre_seleccionado = st.selectbox(
                "👤 Nombre y Apellido *",
                options=nombres_disponibles,
                index=indice_default,
                key="select_nombre_nutricion"
            )
            
            # Obtener datos del jugador seleccionado
            datos_jugador_seleccionado = None
            if nombre_seleccionado:
                for j in jugadores_base_central:
                    if j['nombre'] == nombre_seleccionado:
                        datos_jugador_seleccionado = j
                        break
            
            # Pre-llenar DNI (DESHABILITADO - VIENE DE BASE CENTRAL)
            dni = st.text_input(
                "🆔 DNI * (Base Central)",
                value=datos_jugador_seleccionado['dni'] if datos_jugador_seleccionado else '',
                disabled=True,
                key="dni_input"
            )
            
            # Pre-llenar Categoría (DESHABILITADO - VIENE DE BASE CENTRAL)
            categoria = st.text_input(
                "📂 Categoría * (Base Central)",
                value=datos_jugador_seleccionado['categoria'] if datos_jugador_seleccionado else '',
                disabled=True,
                key="categoria_input"
            )
        
        with col2:
            # Pre-llenar Posición (DESHABILITADO - VIENE DE BASE CENTRAL)
            posicion = st.text_input(
                "🏈 Posición (Base Central)",
                value=datos_jugador_seleccionado['posicion'] if datos_jugador_seleccionado else '',
                disabled=True,
                key="posicion_input"
            )
            
            # Pre-llenar Teléfono (DESHABILITADO - VIENE DE BASE CENTRAL)
            telefono = st.text_input(
                "📞 Teléfono (Base Central)",
                value=datos_jugador_seleccionado['telefono'] if datos_jugador_seleccionado else '',
                disabled=True,
                key="telefono_input"
            )
            
            # Pre-llenar Email (DESHABILITADO - VIENE DE BASE CENTRAL)
            email = st.text_input(
                "📧 Email (Base Central)",
                value=datos_jugador_seleccionado['email'] if datos_jugador_seleccionado else '',
                disabled=True,
                key="email_input"
            )
        
            st.markdown("---")
        st.markdown("**📊 Información de Nutrición (Campos Editables)**")
        
        objetivo = st.selectbox(
            "🎯 Objetivo Nutricional *",
            options=[
                'Seleccionar...',
                'Mantenimiento de peso corporal',
                'Aumento de Masa Muscular',
                'Disminución de Masa Adiposa'
            ],
            key="objetivo_input"
        )
        
        st.markdown("**📏 Mediciones Antropométricas Básicas**")
        col_med1, col_med2, col_med3 = st.columns(3)
        
        with col_med1:
            peso = st.number_input("Peso (kg) *", min_value=0.0, step=0.1, format="%.1f", key="peso_input")
            talla = st.number_input("Talla (cm) *", min_value=0.0, step=0.1, format="%.1f", key="talla_input")
            talla_sentado = st.number_input("Talla sentado (cm)", min_value=0.0, step=0.1, format="%.1f", key="talla_sentado_input")
        
        with col_med2:
            imc = st.number_input("IMC", min_value=0.0, step=0.1, format="%.1f", key="imc_input")
            pct_ma = st.number_input("% MA (Masa Adiposa)", min_value=0.0, max_value=100.0, step=0.1, format="%.1f", key="pct_ma_input")
            z_adiposo = st.number_input("Z Adiposo", min_value=-10.0, max_value=10.0, step=0.01, format="%.2f", key="z_adiposo_input")
        
        with col_med3:
            seis_pliegues = st.number_input("6 Pliegues (mm)", min_value=0.0, step=0.1, format="%.1f", key="seis_pliegues_input")
            kg_mm = st.number_input("Cuantos kilos de Masa Muscular *", min_value=0.0, step=0.1, format="%.1f", key="kg_mm_input")
            pct_mm = st.number_input("% MM (% Masa Muscular)", min_value=0.0, max_value=100.0, step=0.1, format="%.1f", key="pct_mm_input")
            
        st.markdown("**🦴 Masa Ósea e Índices**")
        col_osea1, col_osea2, col_osea3 = st.columns(3)
        
        with col_osea1:
            z_mm = st.number_input("Z MM (Índice Masa Muscular)", min_value=-10.0, max_value=10.0, step=0.01, format="%.2f", key="z_mm_input")
        
        with col_osea2:
            kg_mo = st.number_input("kg de MO (Masa Ósea)", min_value=0.0, step=0.1, format="%.1f", key="kg_mo_input")
        
        with col_osea3:
            imo = st.number_input("IMO (Índice Masa Ósea)", min_value=0.0, step=0.01, format="%.2f", key="imo_input")
        
        st.markdown("---")
        st.markdown("**📝 Observaciones**")
        observaciones = st.text_area("Observaciones adicionales", key="observaciones_input")
        
        submit = st.form_submit_button("💾 Guardar Registros", type="primary")
        
        if submit:
            # Validaciones
            if not nombre_seleccionado:
                st.error("❌ Selecciona un jugador")
                return False
            if not datos_jugador_seleccionado:
                st.error("❌ No se encontraron datos del jugador en la Base Central")
                return False
            if objetivo == 'Seleccionar...':
                st.error("❌ Selecciona un objetivo nutricional")
                return False
            
            # Validar que hay al menos una medición
  # Validar que hay al menos una medición
            if peso <= 0 and talla <= 0 and imc <= 0 and kg_mm <= 0:
                st.warning("⚠️ Agrega al menos una medición")
                return False
            
            # Crear fila de datos - RESPETANDO EXACTAMENTE EL ORDEN DEL GOOGLE SHEETS
            marca_temporal = datetime.now().strftime("%d/%m/%Y %H:%M")
            
                    
            row_data = [
                marca_temporal,                                    # 0: Marca temporal
                nombre_seleccionado,                               # 1: Nombre y Apellido
                datos_jugador_seleccionado['dni'],                 # 2: Dni
                datos_jugador_seleccionado['categoria'],           # 3: Categoría
                datos_jugador_seleccionado['posicion'],            # 4: Posición del jugador
                peso if peso > 0 else '',                          # 5: Peso (kg)
                talla if talla > 0 else '',                        # 6: Talla (cm)
                talla_sentado if talla_sentado > 0 else '',        # 7: Talla sentado (cm)
                kg_mm if kg_mm > 0 else '',                        # 8: Cuantos kilos de Masa Muscular
                imc if imc > 0 else '',                            # 9: IMC
                pct_ma if pct_ma > 0 else '',                      # 10: % MA
                z_adiposo if z_adiposo != 0 else '',              # 11: Z Adiposo
                seis_pliegues if seis_pliegues > 0 else '',       # 12: 6 Pliegues
                kg_mm if kg_mm > 0 else '',                        # 13: kg MM
                pct_mm if pct_mm > 0 else '',                      # 14: % MM
                z_mm if z_mm != 0 else '',                         # 15: Z MM
                kg_mo if kg_mo > 0 else '',                        # 16: kg de MO
                imo if imo > 0 else '',                            # 17: IMO
                objetivo,                                          # 18: Objetivo
                observaciones                                      # 19: Observaciones (NUEVO)
            ]
            # Guardar en Google Sheets de Nutrición
            if guardar_datos_nutricion_en_google_sheets(
                row_data=row_data,
                sheet_id='12SqV7eAYpCwePD-TA1R1XOou-nGO3R6QUSHUnxa8tAI',
                worksheet_name='Respuestas de formulario 1'
            ):
                st.session_state['mostrar_formulario_nuevo'] = False
                st.session_state['jugador_para_reporte'] = None
                st.rerun()
            
            return True
        


def hacer_merge_nutricion_con_base_central(df_nutricion, jugadores_base_central):
    """
    Hace un MERGE entre los datos de Nutrición y Base Central.
    Asegura que todos los datos de Base Central estén en Nutrición.
    
    Args:
        df_nutricion (pd.DataFrame): Datos del Sheet de Nutrición
        jugadores_base_central (list): Datos de la Base Central
    
    Returns:
        pd.DataFrame: DataFrame enriquecido con MERGE completo
    """
    if df_nutricion.empty:
        st.warning("⚠️ No hay datos en el sheet de nutrición")
        return df_nutricion
    
    # Crear DataFrame desde Base Central
    df_bc = pd.DataFrame(jugadores_base_central)
    
    # Normalizar nombres para el merge
    df_nutricion['nombre_normalizado'] = df_nutricion['Nombre y Apellido'].str.lower().str.strip()
    df_bc['nombre_normalizado'] = df_bc['nombre'].str.lower().str.strip()
    
    # Hacer MERGE (LEFT JOIN - mantener todos los registros de nutrición)
    df_merged = df_nutricion.merge(
        df_bc[['nombre_normalizado', 'dni', 'categoria', 'posicion', 'email', 'telefono', 'estado']],
        on='nombre_normalizado',
        how='left',
        suffixes=('_nutricion', '_bc')
    )
    
    # Priorizar datos de Base Central sobre Nutrición (porque es la fuente de verdad)
    for col in ['dni', 'categoria', 'posicion', 'email', 'telefono']:
        col_bc = f'{col}_bc'
        if col_bc in df_merged.columns:
            # Si existe dato en BC, usar ese. Si no, usar el de nutrición
            df_merged[col] = df_merged[col_bc].fillna(df_merged[col])
            df_merged.drop(col_bc, axis=1, inplace=True)
    
    # Eliminar columna auxiliar
    df_merged.drop('nombre_normalizado', axis=1, inplace=True)
    
    return df_merged



def read_new_google_sheet_to_df(
    sheet_id='12SqV7eAYpCwePD-TA1R1XOou-nGO3R6QUSHUnxa8tAI',
    target_gid=382913329,
    credentials_paths=None
):
    """
    Lee un Google Sheet específico y devuelve un DataFrame de pandas.
    """
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    try:
        # Obtener credenciales usando la función mejorada
        creds_info = get_google_credentials()
        
        if creds_info is None:
            st.error("❌ No se pudieron cargar las credenciales de Google")
            return None
        
        # Crear credenciales desde la información obtenida
        credentials = Credentials.from_service_account_info(creds_info, scopes=SCOPES)

        gc = gspread.authorize(credentials)
        sh = gc.open_by_key(sheet_id)

        # Obtener la hoja de trabajo específica por GID
        worksheet = None
        for sheet in sh.worksheets():
            if str(sheet.id) == str(target_gid):
                worksheet = sheet
                break

        if worksheet is None:
            st.error(f"❌ No se encontró la hoja con GID: {target_gid}")
            return None

        # Leer todos los datos
        data = worksheet.get_all_records()

        if not data:
            st.warning("⚠️ La hoja está vacía")
            return pd.DataFrame()

        # Convertir a DataFrame
        df = pd.DataFrame(data)

        # Limpiar datos vacíos
        df = df.dropna(how='all')
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

        return df

    except gspread.exceptions.SpreadsheetNotFound:
        st.error("❌ Google Sheet no encontrado. Verifica el ID y permisos.")
        return None
    except gspread.exceptions.APIError as e:
        st.error(f"❌ Error de API: {e}. Verifica que hayas compartido el sheet con la cuenta de servicio.")
        return None
    except Exception as e:
        st.error(f"❌ Error al conectar con Google Sheets: {str(e)}")
        st.info("🔧 Verifica que:")
        st.info("• El archivo de credenciales sea válido")
        st.info("• El Sheet ID sea correcto")
        st.info("• La cuenta de servicio tenga permisos")
        return None



      
def crear_selector_jugadores(df, categorias_seleccionadas):
    """
    Crea un selector múltiple para elegir jugadores específicos de las categorías seleccionadas.
    
    Args:
        df (pd.DataFrame): DataFrame con los datos.
        categorias_seleccionadas (list): Lista de categorías seleccionadas.
    
    Returns:
        list: Lista de jugadores seleccionados
    """
    if df is None or df.empty:
        st.error("❌ Error: DataFrame vacío o no existe")
        return []
    
    if not categorias_seleccionadas:
        st.info("ℹ️ Selecciona primero una categoría para elegir jugadores")
        return []
    
    # Filtrar jugadores por categorías seleccionadas
    df_filtrado = df[df['Categoría'].isin(categorias_seleccionadas)]
    
    if df_filtrado.empty:
        st.warning("⚠️ No hay jugadores en las categorías seleccionadas")
        return []
    
    st.subheader("👥 Seleccionar Jugadores")

    # Obtener lista de jugadores disponibles
    columna_jugador = 'Nombre y Apellido'
    if columna_jugador not in df.columns:
        st.error(f"❌ No se encontró la columna '{columna_jugador}'")
        return []
    
    jugadores_disponibles = sorted(df_filtrado[columna_jugador].unique())
    jugadores_disponibles = [j for j in jugadores_disponibles if str(j).strip() and str(j) != 'nan']
    
    # Opciones para seleccionar todos o ninguno
    col1, col2 = st.columns(2)
    with col1:
        seleccionar_todos = st.button("✅ Seleccionar todos", key="sel_todos_jug")
    with col2:
        limpiar_seleccion = st.button("❌ Limpiar Selección", key="limpiar_jug")
    
    # Selector múltiple principal
    if seleccionar_todos:
        jugadores_seleccionados = st.multiselect(
            f"Elige los jugadores a analizar ({len(jugadores_disponibles)} disponibles):",
            options=jugadores_disponibles,
            default=jugadores_disponibles,
            help="Selecciona jugadores específicos para análisis detallado"
        )
    elif limpiar_seleccion:
        jugadores_seleccionados = st.multiselect(
            f"Elige los jugadores a analizar ({len(jugadores_disponibles)} disponibles):",
            options=jugadores_disponibles,
            default=[],
            help="Selecciona jugadores específicos para análisis detallado"
        )
    else:
        jugadores_seleccionados = st.multiselect(
            f"Elige los jugadores a analizar ({len(jugadores_disponibles)} disponibles):",
            options=jugadores_disponibles,
            default=[],
            help="Selecciona jugadores específicos para análisis detallado"
        )
    
    return jugadores_seleccionados

def crear_selector_categorias(df):
    """
    Crea un selector múltiple para elegir categorías.
    """
    if df is None or df.empty:
        st.error("❌ Error: DataFrame vacío o no existe")
        return []
    
    if 'Categoría' not in df.columns:
        st.error("❌ No se encontró la columna 'Categoría'")
        return []
    
    categorias_disponibles = sorted(df['Categoría'].unique())
    categorias_disponibles = [c for c in categorias_disponibles if str(c).strip() and str(c) != 'nan']
    
    st.subheader("🏷️ Seleccionar Categorías")
    
    # Opciones para seleccionar todos o ninguno
    col1, col2 = st.columns(2)
    with col1:
        seleccionar_todos = st.button("✅ Seleccionar todas", key="sel_todas_cat")
    with col2:
        limpiar_seleccion = st.button("❌ Limpiar Selección", key="limpiar_cat")
    
    # Selector múltiple principal
    if seleccionar_todos:
        categorias_seleccionadas = st.multiselect(
            f"Elige las categorías a analizar ({len(categorias_disponibles)} disponibles):",
            options=categorias_disponibles,
            default=categorias_disponibles,
            help="Selecciona las categorías para análisis"
        )
    elif limpiar_seleccion:
        categorias_seleccionadas = st.multiselect(
            f"Elige las categorías a analizar ({len(categorias_disponibles)} disponibles):",
            options=categorias_disponibles,
            default=[],
            help="Selecciona las categorías para análisis"
        )
    else:
        categorias_seleccionadas = st.multiselect(
            f"Elige las categorías a analizar ({len(categorias_disponibles)} disponibles):",
            options=categorias_disponibles,
            default=[],
            help="Selecciona las categorías para análisis"
        )
    
    return categorias_seleccionadas

def contar_jugadores_por_categoria_filtrado(df, categorias_seleccionadas):
    """
    Cuenta jugadores por categoría filtrado por las categorías seleccionadas.
    """
    if df is None or df.empty:
        return None
    
    if not categorias_seleccionadas:
        return None
    
    df_filtrado = df[df['Categoría'].isin(categorias_seleccionadas)]
    conteo = df_filtrado['Categoría'].value_counts()
    
    return conteo

def crear_grafico_categorias_con_objetivos(df_filtrado, conteo_categorias, columna_objetivo):
    """
    Crea un gráfico de barras apiladas con objetivos nutricionales por categoría.
    """
    if df_filtrado is None or df_filtrado.empty or columna_objetivo is None:
        return go.Figure()
    
    # Crear tabla cruzada para el gráfico
    tabla_cruzada = pd.crosstab(df_filtrado['Categoría'], df_filtrado[columna_objetivo])
    
    # Colores para cada objetivo
    colores_objetivos = {
        'Mantenimineto de peso corporal': "#0B8F10",  # <- agrega esta línea con el typo
        'Mantenimiento de peso corporal': "#0B8F10",  # <- puedes dejar la correcta también
        'Aumento de Masa Muscular': "#BDA20D",
        'Disminución de Masa Adiposa': '#FF6B6B'
    }
    
    fig = go.Figure()
    
    # Agregar una barra por cada objetivo
    for objetivo in tabla_cruzada.columns:
        color = colores_objetivos.get(objetivo, '#9E9E9E')
        fig.add_trace(go.Bar(
            name=objetivo,
            x=tabla_cruzada.index,
            y=tabla_cruzada[objetivo],
            marker_color=color,
            text=tabla_cruzada[objetivo],
            textposition='auto'
        ))
    
    fig.update_layout(
        title="Distribución de Objetivos Nutricionales por Categoría",
        xaxis_title="Categoría",
        yaxis_title="Número de Jugadores",
        barmode='stack',
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig


def filtrar_ultimo_registro_por_jugador(df):
    """
    Filtra el DataFrame para mantener solo el último registro de cada jugador único.
    Usa 'Nombre y Apellido' y 'DNI' como identificadores únicos.
    
    Args:
        df (pd.DataFrame): DataFrame con todos los registros
    
    Returns:
        pd.DataFrame: DataFrame filtrado con solo los últimos registros
    """
    if df is None or df.empty:
        return df
    
    # Verificar que existan las columnas necesarias
    columna_nombre = 'Nombre y Apellido'
    columna_dni = None
    
    # Buscar columna de DNI (puede tener diferentes nombres)
    posibles_dni = ['DNI', 'dni', 'Dni', 'documento', 'Documento']
    for col in df.columns:
        if col in posibles_dni or 'dni' in col.lower() or 'documento' in col.lower():
            columna_dni = col
            break
    
    if columna_nombre not in df.columns:
        st.warning(f"⚠️ No se encontró la columna '{columna_nombre}' para filtrar registros únicos")
        return df
    
    # Buscar columna de fecha para ordenar por la más reciente
    columna_fecha = None
    posibles_fechas = ['Fecha', 'fecha', 'timestamp', 'Timestamp', 'created_at', 'date']
    for col in df.columns:
        if any(palabra in col.lower() for palabra in ['fecha', 'date', 'time']):
            columna_fecha = col
            break
    
    # Si hay columna de fecha, ordenar por ella (más reciente primero)
    if columna_fecha is not None:
        try:
            # Intentar convertir a datetime si no lo está ya
            if not pd.api.types.is_datetime64_any_dtype(df[columna_fecha]):
                df[columna_fecha] = pd.to_datetime(df[columna_fecha], errors='coerce')
            
            # Ordenar por fecha descendente (más reciente primero)
            df = df.sort_values(by=columna_fecha, ascending=False)
        except Exception as e:
            st.warning(f"⚠️ No se pudo ordenar por fecha: {str(e)}")
    
    # Filtrar duplicados
    if columna_dni is not None:
        # Usar nombre Y DNI para identificar jugadores únicos
        df_filtrado = df.drop_duplicates(subset=[columna_nombre, columna_dni], keep='first')
        identificador = f"{columna_nombre} + {columna_dni}"
    else:
        # Solo usar nombre si no hay DNI
        df_filtrado = df.drop_duplicates(subset=[columna_nombre], keep='first')
        identificador = columna_nombre
        st.warning("⚠️ No se encontró columna de DNI, filtrando solo por nombre")
    
    registros_originales = len(df)
    registros_filtrados = len(df_filtrado)
    registros_duplicados = registros_originales - registros_filtrados
    
    
   
    
    return df_filtrado




def crear_grafico_categorias(conteo_categorias):
    """
    Crea un gráfico de barras simple por categoría (función fallback).
    """
    if conteo_categorias is None or conteo_categorias.empty:
        return go.Figure()
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=conteo_categorias.index,
        y=conteo_categorias.values,
        marker_color='#4CAF50',
        text=conteo_categorias.values,
        textposition='auto'
    ))
    
    fig.update_layout(
        title="Jugadores por Categoría",
        xaxis_title="Categoría",
        yaxis_title="Número de Jugadores",
        height=400
    )
    
    return fig

def crear_grafico_categorias_con_objetivos(df_filtrado, conteo_categorias, columna_objetivo):
    """
    Crea un gráfico de barras apiladas con objetivos nutricionales por categoría,
    mostrando los nombres de los jugadores en el tooltip.
    """
    if df_filtrado is None or df_filtrado.empty or columna_objetivo is None:
        return go.Figure()
    
    # Colores para cada objetivo
    colores_objetivos = {
        'Mantenimiento de peso corporal': "#0B8F10",
        'Aumento de Masa Muscular': "#BDA20D",
        'Disminución de Masa Adiposa': '#FF6B6B'
    }
    
    categorias = sorted(df_filtrado['Categoría'].unique())
    objetivos = df_filtrado[columna_objetivo].unique()
    
    fig = go.Figure()
    
    for objetivo in objetivos:
        y = []
        text = []
        for categoria in categorias:
            jugadores = df_filtrado[
                (df_filtrado['Categoría'] == categoria) &
                (df_filtrado[columna_objetivo] == objetivo)
            ]['Nombre y Apellido'].tolist()
            y.append(len(jugadores))
            # Tooltip: lista de nombres separados por salto de línea
            text.append("<br>".join(jugadores) if jugadores else "")
        
        color = colores_objetivos.get(objetivo, '#9E9E9E')
        fig.add_trace(go.Bar(
            name=objetivo,
            x=categorias,
            y=y,
            marker_color=color,
            text=y,  # Número de jugadores como texto en la barra
            customdata=text,  # Nombres de jugadores para el tooltip
            hovertemplate=(
                "<b>%{x}</b><br>" +
                objetivo + ": %{y} jugadores<br>" +
                "Jugadores:<br>%{customdata}<extra></extra>"
            )
        ))
    
    fig.update_layout(
        title="Distribución de Objetivos Nutricionales por Categoría",
        xaxis_title="Categoría",
        yaxis_title="Número de Jugadores",
        barmode='stack',
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig


def obtener_columna_fecha(df):
    posibles_fechas = ['Marca temporal']
    for col in df.columns:
        if col in posibles_fechas or any(palabra in col.lower() for palabra in ['fecha', 'date', 'time', 'marca']):
            return col
    return None

def grafico_evolucion_peso(df_hist):
    """
    Genera gráfico de evolución del peso con conversión explícita a float.
    """
    columna_fecha = obtener_columna_fecha(df_hist)
    
    # ✅ BUSCAR COLUMNA DE PESO DE FORMA FLEXIBLE
    columna_peso = None
    posibles_nombres_peso = [
        'Peso (kg): [Número con decimales 88,5]',
        'Peso (kg)',
        'peso',
        'Peso'
    ]
    
    for nombre in posibles_nombres_peso:
        if nombre in df_hist.columns:
            columna_peso = nombre
            break
    
    # Si no encuentra, buscar por contenido
    if columna_peso is None:
        for col in df_hist.columns:
            if 'peso' in col.lower() and 'kg' in col.lower():
                columna_peso = col
                break
    
    if columna_fecha and columna_peso and columna_peso in df_hist.columns:
        # Convertir columna de fecha a datetime y eliminar filas sin fecha válida
        df_hist[columna_fecha] = pd.to_datetime(df_hist[columna_fecha], errors='coerce')
        df_hist = df_hist.dropna(subset=[columna_fecha])
        
        # ✅ CONVERTIR PESO A FLOAT EXPLÍCITAMENTE
        df_hist[columna_peso] = pd.to_numeric(df_hist[columna_peso], errors='coerce')
        df_hist = df_hist.dropna(subset=[columna_peso])  # Eliminar pesos inválidos
        
        # Validar que hay datos después de la limpieza
        if df_hist.empty:
            return None
        
        # Ordenar de más vieja a más nueva
        df_hist_ordenado = df_hist.sort_values(columna_fecha, ascending=True)
        fechas_formateadas = df_hist_ordenado[columna_fecha].dt.strftime('%b %Y')
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_hist_ordenado[columna_fecha],
            y=df_hist_ordenado[columna_peso],
            mode='lines+markers+text',
            line=dict(
                shape='spline',
                color='#f2c94c',
                width=3
            ),
            marker=dict(
                color='#f2c94c',
                size=10,
                line=dict(color='white', width=2)
            ),
            # ✅ CONVERSIÓN EXPLÍCITA A FLOAT
            text=[f"{float(peso):.1f} kg" for peso in df_hist_ordenado[columna_peso]],
            textposition="top center",
            hovertemplate=(
                "<b>Peso:</b> %{y:.1f} kg<br>" +
                "<b>Fecha:</b> %{customdata}<extra></extra>"
            ),
            customdata=fechas_formateadas
        ))
        
        fig.update_layout(
            title=dict(
                text="Evolución del Peso (kg)",
                x=0.5,
                xanchor='center',
                font=dict(color='white', size=22, family='Arial')
            ),
            plot_bgcolor='#1a1a1a',
            paper_bgcolor='#1a1a1a',
            xaxis=dict(
                title=dict(
                    text="Fecha",
                    font=dict(color='white', size=16)
                ),
                tickfont=dict(color='white', size=14),
                gridcolor='rgba(255,255,255,0.1)',
                showline=False,
                zeroline=False
            ),
            yaxis=dict(
                title=dict(
                    text="Peso (kg)",
                    font=dict(color='white', size=16)
                ),
                tickfont=dict(color='white', size=14),
                gridcolor='rgba(255,255,255,0.1)',
                showline=False,
                zeroline=False
            ),
            font=dict(color='white'),
            margin=dict(l=40, r=40, t=60, b=40),
            height=350,
            showlegend=False
        )
        return fig
    else:
        return None
    
def grafico_torta_antropometria(df_hist):
    """
    Devuelve un gráfico de torta con la composición corporal de la última antropometría.
    Muestra solo el peso en kg en el centro del gráfico.
    """
    if df_hist is None or df_hist.empty:
        return None

    date_col = obtener_columna_fecha(df_hist)
    df_copy = df_hist.copy()

    if date_col:
        df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors='coerce')
        df_copy = df_copy.dropna(subset=[date_col])

    try:
        if date_col and not df_copy.empty:
            ultimo = df_copy.sort_values(by=date_col).iloc[-1]
        else:
            ultimo = df_hist.dropna(how='all').iloc[-1]
    except Exception as e:
        st.warning(f"⚠️ No se pudo determinar la última antropometría: {e}")
        return None

    def norm(col_name):
        return re.sub(r'[^a-z0-9]', '', str(col_name).lower())

    col_masa_muscular = None
    col_kg_mm = None
    col_masa_osea = None
    col_kg_mo = None
    col_kg_ma = None
    col_pct_ma = None
    col_peso = None

    for c in df_hist.columns:
        n = norm(c)
        if ('masamuscular' in n) or ('cuantoskilos' in n) or ('kgmm' in n):
            if 'masa' in n and 'muscular' in n:
                col_masa_muscular = c
            if 'kgmm' in n:
                col_kg_mm = c
        if ('masaosea' in n) or ('kgmo' in n) or ('kgdemo' in n) or ('mo' == n):
            col_kg_mo = c
            col_masa_osea = c
        if ('kgma' in n) or ('masaadip' in n) or ('masaadipos' in n):
            col_kg_ma = c
        if '%' in c or '%ma' in n or 'porcent' in n:
            if 'ma' in n or 'masa' in n:
                col_pct_ma = c
        if 'peso' in n and 'kg' in n:
            col_peso = c

    col_muscular_final = col_kg_mm or col_masa_muscular
    col_osea_final = col_kg_mo or col_masa_osea
    col_adiposa_final = col_kg_ma

    def to_num(val):
        try:
            return float(pd.to_numeric(val, errors='coerce'))
        except:
            return None

    masa_muscular_kg = None
    masa_osea_kg = None
    masa_adiposa_kg = None
    peso_kg = None

    if col_muscular_final in ultimo.index:
        masa_muscular_kg = to_num(ultimo.get(col_muscular_final))
    if col_osea_final in ultimo.index:
        masa_osea_kg = to_num(ultimo.get(col_osea_final))
    if col_adiposa_final in ultimo.index:
        masa_adiposa_kg = to_num(ultimo.get(col_adiposa_final))
    if col_pct_ma in ultimo.index:
        pct_ma = to_num(ultimo.get(col_pct_ma))
    else:
        pct_ma = None
    if col_peso in ultimo.index:
        peso_kg = to_num(ultimo.get(col_peso))

    if masa_adiposa_kg is None and pct_ma is not None and peso_kg is not None:
        masa_adiposa_kg = peso_kg * (pct_ma / 100.0)

    etiqueta_adiposa = 'Masa Adiposa'
    if pct_ma is not None:
        try:
            etiqueta_adiposa = f"Masa Adiposa ({pct_ma:.1f}%)"
        except:
            etiqueta_adiposa = f"Masa Adiposa ({pct_ma}%)"

    labels = []
    values = []

    if masa_osea_kg is not None and not pd.isna(masa_osea_kg) and masa_osea_kg > 0:
        labels.append('Masa Ósea')
        values.append(float(masa_osea_kg))
    if masa_muscular_kg is not None and not pd.isna(masa_muscular_kg) and masa_muscular_kg > 0:
        labels.append('Masa Muscular')
        values.append(float(masa_muscular_kg))
    if masa_adiposa_kg is not None and not pd.isna(masa_adiposa_kg) and masa_adiposa_kg > 0:
        labels.append(etiqueta_adiposa)
        values.append(float(masa_adiposa_kg))

    if not labels and peso_kg is not None and not pd.isna(peso_kg) and peso_kg > 0:
        labels = ['Peso Total']
        values = [float(peso_kg)]

    if labels and values and sum(values) > 0:
        base_color_map = {
            'Masa Ósea': "#7DA2AB",
            'Masa Muscular': "#C40404",
            'Masa Adiposa': "#F1E107",
            'Peso Total': "#A36309"
        }
        if etiqueta_adiposa != 'Masa Adiposa':
            base_color_map[etiqueta_adiposa] = base_color_map['Masa Adiposa']

        slice_colors = [base_color_map.get(l, '#9E9E9E') for l in labels]

        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            marker=dict(colors=slice_colors, line=dict(color='#1a1a1a', width=2)),
            textinfo='label+percent',
            textposition='inside',
            hovertemplate="%{label}: %{value:.1f} kg<br>%{percent}",
        )])

        fig.update_layout(
            title=dict(
                text="Composición corporal (última antropometría)",
                x=0.5,
                xanchor='center',
                font=dict(color='white', size=22, family='Arial')
            ),
            height=350,
            plot_bgcolor='#1a1a1a',
            paper_bgcolor='#1a1a1a',
            font=dict(color='white'),
            legend=dict(
                orientation="v",
                x=1.02,
                y=0.5,
                font=dict(color='white')
            ),
            margin=dict(l=20, r=140, t=60, b=20)
        )

        fig.update_traces(textfont=dict(color='white', size=12))

        # Mostrar SOLO el PESO (kg) en el centro del donut
        if peso_kg is not None and not pd.isna(peso_kg):
            fig.add_annotation(
                dict(
                    text=f"{peso_kg:.1f} kg<br>Peso",
                    x=0.5, y=0.5,
                    font=dict(size=18, color='white'),
                    showarrow=False,
                    align='center'
                )
            )
        return fig
    else:
        return None
    

def crear_tabla_seguimiento_semanal(df_categoria):
    """
    Crea una tabla de seguimiento nutricional semanal con semáforo.
    Ordena por Estado (Rojo → Amarillo → Verde).
    5 columnas: Jugador, Puesto, Objetivo, Estado, Acción Sugerida
    """
    if df_categoria is None or df_categoria.empty:
        return None
    
    # Función interna para determinar estado
    def determinar_estado(row):
        """Lógica mejorada para determinar el estado del semáforo"""
        objetivo = str(row.get('Objetivo', '')).lower().strip()
        
        try:
            pct_ma_val = row.get('% MA: [Número con decimales]', 0)
            pct_ma = float(pct_ma_val) if (pd.notna(pct_ma_val) and isinstance(pct_ma_val, (int, float))) else 0
            
            peso_val = row.get('Peso (kg): [Número con decimales 88,5]', 0)
            peso = float(peso_val) if (pd.notna(peso_val) and isinstance(peso_val, (int, float))) else 0
            
            kg_mm_val = row.get('Cuantos kilos de  Masa Muscular', 0)
            kg_mm = float(kg_mm_val) if (pd.notna(kg_mm_val) and isinstance(kg_mm_val, (int, float))) else 0
            
            imc_val = row.get('IMC: [Número con decimales]', 0)
            imc = float(imc_val) if (pd.notna(imc_val) and isinstance(imc_val, (int, float))) else 0
        except (ValueError, TypeError):
            pct_ma = 0
            peso = 0
            kg_mm = 0
            imc = 0
        
        # AUMENTO DE MASA MUSCULAR
        if 'aumento' in objetivo and 'muscular' in objetivo:
            # Criterios mejorados: considerar masa muscular y peso
            if kg_mm < 55 or peso < 80:
                return ('🔴 Riesgo', 'aumento')
            elif kg_mm < 65 or peso < 90:
                return ('🟡 Monitoreo', 'aumento')
            else:
                return ('🟢 En Meta', 'aumento')
        
        # DISMINUCIÓN DE MASA ADIPOSA
        elif 'disminución' in objetivo or 'reducción' in objetivo or 'adiposa' in objetivo:
            if pct_ma > 22:
                return ('🔴 Riesgo', 'disminución')
            elif pct_ma > 18:
                return ('🟡 Monitoreo', 'disminución')
            else:
                return ('🟢 En Meta', 'disminución')
        
        # MANTENIMIENTO
        else:
            # Usar IMC para mantenimiento
            if imc < 18.5 or imc > 27:
                return ('🔴 Riesgo', 'mantenimiento')
            elif imc < 20 or imc > 25:
                return ('🟡 Monitoreo', 'mantenimiento')
            else:
                return ('🟢 En Meta', 'mantenimiento')
    
    # Función para obtener acciones sugeridas
    def get_accion_sugerida(estado_emoji, objetivo_tipo):
        """Retorna la acción sugerida según el estado y objetivo"""
        acciones = {
            ('🔴 Riesgo', 'aumento'): "Aumentar ingesta proteica +25g/día. Revisar plan alimentario. Reunión nutricional urgente.",
            ('🔴 Riesgo', 'disminución'): "Revisar déficit calórico. Aumentar actividad. Auditoría dietética inmediata.",
            ('🔴 Riesgo', 'mantenimiento'): "IMC fuera de rango. Ajustar plan alimentario. Consulta nutricional.",
            ('🟡 Monitoreo', 'aumento'): "Progreso moderado. Incrementar carbohidratos post-entreno +50g.",
            ('🟡 Monitoreo', 'disminución'): "En progreso hacia meta. Mantener protocolo. Revisar en 7 días.",
            ('🟡 Monitoreo', 'mantenimiento'): "Estable con variaciones menores. Continuar monitoreo semanal.",
            ('🟢 En Meta', 'aumento'): "Excelente progreso. Mantener plan actual. Seguimiento en 10 días.",
            ('🟢 En Meta', 'disminución'): "Meta alcanzada exitosamente. Iniciar fase de mantenimiento.",
            ('🟢 En Meta', 'mantenimiento'): "Estable y en rango óptimo. Continuar protocolo actual."
        }
        
        return acciones.get((estado_emoji, objetivo_tipo), "Mantener seguimiento semanal")
    
    # Copiar DataFrame
    df_tabla = df_categoria.copy()
    
    # Aplicar función de estado
    df_tabla[['estado_emoji', 'objetivo_tipo']] = df_tabla.apply(
        lambda row: pd.Series(determinar_estado(row)), 
        axis=1
    )
    
    # CONSTRUIR TABLA DE SALIDA CON 5 COLUMNAS EXACTAS
    df_tabla_salida = pd.DataFrame()
    
    # Columna 1: Jugador
    df_tabla_salida['Jugador'] = df_tabla['Nombre y Apellido']
    
    # Columna 2: Puesto
    df_tabla_salida['Puesto'] = df_tabla['Posición del jugador'].fillna('N/A')
    
    # Columna 3: Objetivo Nutricional
    df_tabla_salida['Objetivo Nutricional'] = df_tabla['Objetivo'].fillna('N/A')
    
    # Columna 4: Estado (Semáforo)
    df_tabla_salida['Estado'] = df_tabla['estado_emoji']
    
    # Columna 5: Acción Sugerida
    df_tabla_salida['Acción Sugerida'] = df_tabla.apply(
        lambda row: get_accion_sugerida(row['estado_emoji'], row['objetivo_tipo']),
        axis=1
    )
    
    # ORDENAR: 🔴 Riesgo → 🟡 Monitoreo → 🟢 En Meta
    orden_estado = {'🔴 Riesgo': 0, '🟡 Monitoreo': 1, '🟢 En Meta': 2}
    df_tabla_salida['sort_order'] = df_tabla_salida['Estado'].map(orden_estado).fillna(999)
    df_tabla_salida = df_tabla_salida.sort_values('sort_order').drop('sort_order', axis=1)
    
    # Reset índice
    df_tabla_salida = df_tabla_salida.reset_index(drop=True)
    
    return df_tabla_salida

      
def mostrar_analisis_nutricion():
    """
    Función principal para mostrar el análisis de nutrición en Streamlit.
    """
    # Header principal con estilo similar al área médica
    st.markdown("""
    <div style="background: linear-gradient(90deg, #4CAF50 0%, #45a049 100%); 
                padding: 2rem; border-radius: 10px; margin-bottom: 2rem;">
        <h1 style="color: white; text-align: center; margin: 0;">
            🥗 ÁREA DE NUTRICIÓN
        </h1>
        <p style="color: white; text-align: center; margin: 0.5rem 0 0 0; font-size: 1.2rem;">
            Sistema de Análisis Nutricional - Club Argentino de Rugby
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Cargar datos con indicador de progreso
    with st.spinner("📊 Cargando datos nutricionales desde Google Sheets..."):
        df_original = read_new_google_sheet_to_df()
    
    if df_original is None:
        st.error("❌ No se pudieron cargar los datos nutricionales")
        st.info("🔧 Verifica que las credenciales estén configuradas correctamente")
        st.stop()
    
    # Verificar que hay datos
    if df_original.empty:
        st.warning("⚠️ No hay datos nutricionales disponibles")
        st.info("📝 Asegúrate de que el Google Sheet contenga datos")
        st.stop()
    
    # FILTRAR PARA OBTENER SOLO EL ÚLTIMO REGISTRO DE CADA JUGADOR
    df = filtrar_ultimo_registro_por_jugador(df_original)
    
    
    
    # Crear dos columnas para los selectores
    col_izq, col_der = st.columns(2)
    
    # Columna izquierda: Selector de categorías
    with col_izq:
        categorias_seleccionadas = crear_selector_categorias(df)
    
    # Columna derecha: Selector de jugadores
    with col_der:
        jugadores_seleccionados = crear_selector_jugadores(df, categorias_seleccionadas)
    
    # Mostrar análisis solo si hay categorías seleccionadas
    if categorias_seleccionadas:
        st.markdown("---")
        
        # Contar jugadores por categoría filtrado
        conteo_categorias = contar_jugadores_por_categoria_filtrado(df, categorias_seleccionadas)
        
    
        if conteo_categorias is not None:
            # Filtrar DataFrame por categorías seleccionadas
            df_filtrado = df[df['Categoría'].isin(categorias_seleccionadas)]
            
            # Buscar la columna de objetivos
            columna_objetivo = None
            posibles_nombres = ['objetivo', 'Objetivo', 'OBJETIVO', 'Objetivos', 'objetivos']
            for nombre in posibles_nombres:
                if nombre in df.columns:
                    columna_objetivo = nombre
                    break
            # Si no encuentra, buscar columnas que contengan "objetivo"
            if columna_objetivo is None:
                for col in df.columns:
                    if 'objetivo' in col.lower():
                        columna_objetivo = col
                        break

            # Normalizar valores de objetivo nutricional
            if columna_objetivo is not None:
                reemplazos_objetivos = {
                    'Mantenimieto de peso corporal': 'Mantenimiento de peso corporal'
                    # Puedes agregar más reemplazos si aparecen otros errores de tipeo
                }
                df_filtrado[columna_objetivo] = df_filtrado[columna_objetivo].replace(reemplazos_objetivos)
                df[columna_objetivo] = df[columna_objetivo].replace(reemplazos_objetivos)
                
                
                
            # NUEVA SECCIÓN: Detalle por Categoría con Objetivos Nutricionales
            st.subheader("🎯 Detalle por Categoría: Objetivos Nutricionales")
            
            if columna_objetivo is not None:
                # Crear tabla cruzada de categorías vs objetivos
                tabla_objetivos = pd.crosstab(
                    df_filtrado['Categoría'], 
                    df_filtrado[columna_objetivo], 
                    margins=True, 
                    margins_name="Total"
                )
                
                # Mostrar solo las tarjetas coloridas por objetivo
                st.write("**📋 Distribución de Objetivos por Categoría:**")
                
                # Colores para cada objetivo
                colores_objetivos = {
                    'Mantenimiento de peso corporal': '#4CAF50',
                    'Aumento de Masa Muscular': '#FFD700',
                    'Disminución de Masa Adiposa': '#FF6B6B'
                }

                # Mostrar métricas de totales por objetivo en tarjetas coloridas
                col_metricas1, col_metricas2, col_metricas3 = st.columns(3)
                
                if 'Total' in tabla_objetivos.index:
                    totales_objetivos = tabla_objetivos.loc['Total'][:-1]  # Excluir el total general
                    
                    metricas_cols = [col_metricas1, col_metricas2, col_metricas3]
                    col_idx = 0
                    
                    for objetivo, cantidad in totales_objetivos.items():
                        if cantidad > 0:  # Solo mostrar objetivos con jugadores
                            with metricas_cols[col_idx % 3]:
                                # Obtener color del objetivo
                                color = colores_objetivos.get(objetivo, "#9E9E9E")
                                
                                st.markdown(f"""
                                <div style="background-color: {color}; padding: 1rem; border-radius: 0.5rem; margin-bottom: 0.5rem;">
                                    <h3 style="color: white; margin: 0; font-size: 1.2rem;">
                                        {objetivo.replace(' de ', ' de<br>')}
                                    </h3>
                                    <h2 style="color: white; margin: 0.5rem 0 0 0; font-size: 2rem;">
                                        {int(cantidad)}
                                    </h2>
                                    <p style="color: white; margin: 0; font-size: 0.9rem;">
                                        jugadores
                                    </p>
                                </div>
                                """, unsafe_allow_html=True)
                            col_idx += 1
                    
            else:
                st.warning("⚠️ No se encontró la columna de objetivos nutricionales")
                st.info("📝 Columnas disponibles: " + ", ".join(df.columns.tolist()))
            
            # Métricas por categoría (sección original)
            st.subheader("📈 Detalle por Categoría")
            cols = st.columns(len(categorias_seleccionadas))
            for i, categoria in enumerate(categorias_seleccionadas):
                with cols[i]:
                    cantidad = conteo_categorias.get(categoria, 0)
                    st.metric(
                        label=categoria,
                        value=cantidad,
                        delta=f"{cantidad} jugadores"
                    )
            
            # Gráfico mejorado con objetivos nutricionales
            st.subheader("📊 Análisis Visual por Categorías")
            
            # Solo mostrar el gráfico de barras apiladas mejorado
            if columna_objetivo is not None:
                fig_barras_objetivos = crear_grafico_categorias_con_objetivos(df_filtrado, conteo_categorias, columna_objetivo)
                st.plotly_chart(fig_barras_objetivos, use_container_width=True)
            else:
                # Fallback al gráfico original si no hay columna de objetivos
                fig_barras = crear_grafico_categorias(conteo_categorias)
                st.plotly_chart(fig_barras, use_container_width=True)
            
           

            if jugadores_seleccionados:
                st.markdown("## 🔎 Análisis Individual")
                for jugador in jugadores_seleccionados:
                    st.markdown(f"### {jugador}")
                    col1, col2 = st.columns(2)
                    df_hist = df_original[df_original['Nombre y Apellido'] == jugador]

                    with col1:
                        st.markdown("**Evolución del peso**")
                        fig_peso = grafico_evolucion_peso(df_hist)
                        if fig_peso:
                            st.plotly_chart(fig_peso, use_container_width=True)
                        else:
                            st.info("No hay datos históricos de peso para este jugador.")

                    with col2:
                        st.markdown("**Composición corporal (última antropometría)**")
                        fig_torta = grafico_torta_antropometria(df_hist)
                        if fig_torta:
                            st.plotly_chart(fig_torta, use_container_width=True)
                        else:
                            st.info("No hay datos de composición corporal para este jugador.")

                st.markdown("### 🗂️ Últimas mediciones cargadas")
                # Filtrar solo los jugadores seleccionados
                if jugadores_seleccionados:
                    df_vista = df_original[df_original['Nombre y Apellido'].isin(jugadores_seleccionados)].copy()
                else:
                    df_vista = pd.DataFrame()  # Si no hay selección, muestra vacío

                col_fecha = obtener_columna_fecha(df_vista)
                if col_fecha and not df_vista.empty:
                    df_vista[col_fecha] = pd.to_datetime(df_vista[col_fecha], errors='coerce')
                    df_vista = df_vista.sort_values(by=col_fecha, ascending=False)

                columnas_ordenadas = [
                    "Marca temporal",
                    "Nombre y Apellido",
                    "Objetivo",
                    "Categoría",
                    "Posición del jugador",
                    "Peso (kg): [Número con decimales 88,5]",
                    "Talla (cm): [Número]",
                    "Talla sentado (cm): [Número]",
                    "Cuantos kilos de  Masa Muscular",
                    "IMC",
                    "% MA: [Número con decimales]",
                    "Z Adiposo: [Número con decimales]",
                    "6 Pliegues: [Número con decimales]",
                    " kg MM: [Número con decimales]",
                    "% MM: [Número con decimales]",
                    "Z MM: [Número con decimales]",
                    "kg de MO: [Número con decimales]",
                    "IMO: [Número con decimales]",
                    "Dni"
                ]

                columnas_mostrar = [c for c in columnas_ordenadas if c in df_vista.columns]
                if columnas_mostrar and not df_vista.empty:
                    df_vista = df_vista[columnas_mostrar]
                    # Aplica estilos: encabezado verde y filas alternas
                    styled_df = df_vista.style\
                        .set_properties(**{'background-color': '#F7F7F7', 'color': '#222'})\
                        .set_table_styles([
                            {'selector': 'th', 'props': [('background-color', '#4CAF50'), ('color', 'white'), ('font-size', '16px')]},
                            {'selector': 'td', 'props': [('font-size', '15px')]}
                        ])
                    st.dataframe(styled_df, use_container_width=True, height=400)
                else:
                    st.info("ℹ️ No hay columnas disponibles para mostrar en 'Últimas mediciones cargadas'")
                    
                    
                    
                    
                    
def mostrar_tabla_seguimiento_profesional(df_seguimiento):
    """
    Muestra la tabla de seguimiento de forma profesional con Streamlit.
    Incluye opción de exportar como CSV y Excel.
    """
    if df_seguimiento is None or df_seguimiento.empty:
        st.info("ℹ️ No hay datos suficientes para la tabla")
        return
    
    # Mostrar tabla con estilos nativos de Streamlit
    st.dataframe(
        df_seguimiento,
        use_container_width=True,
        column_config={
            "Jugador": st.column_config.TextColumn(
                "Jugador",
                width="medium"
            ),
            "Puesto": st.column_config.TextColumn(
                "Puesto",
                width="small"
            ),
            "Objetivo Nutricional": st.column_config.TextColumn(
                "Objetivo Nutricional",
                width="medium"
            ),
            "Estado": st.column_config.TextColumn(
                "Estado",
                width="small"
            ),
            "Acción Sugerida": st.column_config.TextColumn(
                "Acción Sugerida",
                width="large"
            )
        },
        hide_index=True
    )
    
    # Resumen de estados
    st.markdown("---")
    st.markdown("### 📊 Resumen por Estado")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        rojos = int(len(df_seguimiento[df_seguimiento['Estado'].str.contains('🔴', na=False)]))
        st.metric(
            "🔴 Riesgo",
            rojos,
            delta="Acción inmediata",
            help="Jugadores que requieren intervención urgente"
        )
    
    with col2:
        amarillos = int(len(df_seguimiento[df_seguimiento['Estado'].str.contains('🟡', na=False)]))
        st.metric(
            "🟡 Monitoreo",
            amarillos,
            delta="Seguimiento cercano",
            help="Jugadores en progreso"
        )
    
    with col3:
        verdes = int(len(df_seguimiento[df_seguimiento['Estado'].str.contains('🟢', na=False)]))
        st.metric(
            "🟢 En Meta",
            verdes,
            delta="Mantener protocolo",
            help="Jugadores en objetivo"
        )
    
    # Botones de descarga
    st.markdown("---")
    st.markdown("### 📥 Descargar Datos")
    
    col_csv, col_excel = st.columns(2)
    
    with col_csv:
        csv_data = df_seguimiento.to_csv(index=False)
        st.download_button(
            label="📥 Descargar CSV",
            data=csv_data,
            file_name=f"seguimiento_nutricion_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col_excel:
        # Crear Excel con pandas
        import io
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_seguimiento.to_excel(writer, sheet_name='Seguimiento', index=False)
        buffer.seek(0)
        
        st.download_button(
            label="📊 Descargar Excel",
            data=buffer.getvalue(),
            file_name=f"seguimiento_nutricion_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    # Información de estados
    st.markdown("---")
    st.markdown("### 📋 Leyenda de Estados")
    
    col_leg1, col_leg2, col_leg3 = st.columns(3)
    
    with col_leg1:
        st.info("**🔴 Riesgo**: Requiere acción inmediata del nutricionista")
    
    with col_leg2:
        st.warning("**🟡 Monitoreo**: Seguimiento cercano recomendado")
    
    with col_leg3:
        st.success("**🟢 En Meta**: Protocolo actual mantiene resultados")

        


def mostrar_analisis_nutricion():
    """
    Función principal - Lee categorías y jugadores de BASE CENTRAL
    """
    # Inicializar session_state
    if 'mostrar_formulario_nuevo' not in st.session_state:
        st.session_state['mostrar_formulario_nuevo'] = False
    if 'jugador_para_reporte' not in st.session_state:
        st.session_state['jugador_para_reporte'] = None
    
    st.markdown("""
    <div style="background: linear-gradient(90deg, #4CAF50 0%, #45a049 100%); 
                padding: 2rem; border-radius: 10px; margin-bottom: 2rem;">
        <h1 style="color: white; text-align: center; margin: 0;">
            🥗 ÁREA DE NUTRICIÓN
        </h1>
        <p style="color: white; text-align: center; margin: 0.5rem 0 0 0; font-size: 1.2rem;">
            Sistema de Análisis Nutricional - Club Argentino de Rugby
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # CARGAR DATOS
    jugadores_base_central = conectar_base_central()
    df_nutricion = read_new_google_sheet_to_df()
    
    if not jugadores_base_central:
        st.error("❌ No se pudieron cargar los jugadores de la Base Central")
        st.stop()
    
    if df_nutricion is None:
        st.error("❌ No se pudieron cargar los datos de nutrición")
        st.stop()
    
    # ✅ AGREGAR AQUÍ: Hacer MERGE de Nutrición con Base Central
    if not df_nutricion.empty:
        df_nutricion = hacer_merge_nutricion_con_base_central(df_nutricion, jugadores_base_central)
        # ❌ ELIMINA ESTA LÍNEA:
        # st.success(f"✅ Base central integrada: {len(jugadores_base_central)} jugadores disponibles | Registros: {len(df_nutricion)}")
    else:
        st.warning("⚠️ No hay datos en nutrición aún")
    
    # ============================================================
    # CREAR TABS PRINCIPALES
    # ============================================================
    tab_individual, tab_equipo = st.tabs(["👤 Análisis Individual", "👥 Análisis de Equipo"])
    

    
    # ============================================================
    # TAB 1: ANÁLISIS INDIVIDUAL
    # ============================================================
    with tab_individual:
        st.markdown("## 👤 Análisis Individual por Jugador")
        
        # Filtros - LEEN DE BASE CENTRAL
        col_izq, col_der = st.columns(2)
        
        with col_izq:
            # Obtener categorías DIRECTAMENTE de Base Central
            categorias_bc = sorted(set([j['categoria'] for j in jugadores_base_central if j['categoria']]))
            categorias_individual = st.multiselect(
                "🏷️ Seleccionar Categorías",
                options=categorias_bc,
                default=[],
                key="cat_individual"
            )
        
        with col_der:
            # Filtrar jugadores por categorías seleccionadas (BASE CENTRAL)
            if categorias_individual:
                jugadores_filtrados = sorted([
                    j['nombre'] for j in jugadores_base_central 
                    if j['categoria'] in categorias_individual
                ])
            else:
                jugadores_filtrados = sorted([j['nombre'] for j in jugadores_base_central])
            
            jugadores_individual = st.multiselect(
                f"👥 Seleccionar Jugadores ({len(jugadores_filtrados)} disponibles)",
                options=jugadores_filtrados,
                default=[],
                key="jug_individual"
            )
        
        st.markdown("---")
        
        # Botón nuevo reporte
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 3])
        with col_btn1:
            # El botón solo se habilita si hay jugadores seleccionados
            boton_habilitado = len(jugadores_individual) > 0
            if st.button(
                "➕ Nuevo Reporte", 
                key="btn_nuevo_nutricion", 
                use_container_width=True,
                disabled=not boton_habilitado
            ):
                # Guardar el jugador seleccionado en session_state
                st.session_state['jugador_para_reporte'] = jugadores_individual[0]
                st.session_state['mostrar_formulario_nuevo'] = True
        
        if st.session_state.get('mostrar_formulario_nuevo', False):
            crear_formulario_nutricion_nuevo_jugador(
                jugadores_base_central,
                jugador_preseleccionado=st.session_state.get('jugador_para_reporte')
            )
            st.stop()

        
        st.markdown("---")
        
        # Mostrar análisis
        if jugadores_individual:
            for jugador in jugadores_individual:
                st.markdown(f"### 📊 {jugador}")
                
                col1, col2 = st.columns(2)
                df_hist = df_nutricion[df_nutricion['Nombre y Apellido'] == jugador]

                with col1:
                    st.markdown("**Evolución del peso**")
                    fig_peso = grafico_evolucion_peso(df_hist)
                    if fig_peso:
                        st.plotly_chart(fig_peso, use_container_width=True)
                    else:
                        st.info("No hay datos históricos de peso para este jugador.")

                with col2:
                    st.markdown("**Composición corporal**")
                    fig_torta = grafico_torta_antropometria(df_hist)
                    if fig_torta:
                        st.plotly_chart(fig_torta, use_container_width=True)
                    else:
                        st.info("No hay datos de composición corporal para este jugador.")
                
                st.markdown("---")
            
            # Tabla histórico
            st.markdown("### 🗂️ Historial de Mediciones")
            df_vista = df_nutricion[df_nutricion['Nombre y Apellido'].isin(jugadores_individual)].copy()

            col_fecha = obtener_columna_fecha(df_vista)
            if col_fecha and not df_vista.empty:
                df_vista[col_fecha] = pd.to_datetime(df_vista[col_fecha], errors='coerce')
                df_vista = df_vista.sort_values(by=col_fecha, ascending=False)

            columnas_ordenadas = [
                "Marca temporal",
                "Nombre y Apellido",
                "Objetivo",
                "Categoría",
                "Posición del jugador",
                "Peso (kg): [Número con decimales 88,5]",
                "Talla (cm): [Número]",
                "IMC",
                "% MA: [Número con decimales]",
                "Cuantos kilos de  Masa Muscular"
            ]

            columnas_mostrar = [c for c in columnas_ordenadas if c in df_vista.columns]
            if columnas_mostrar and not df_vista.empty:
                df_vista = df_vista[columnas_mostrar]
                styled_df = df_vista.style\
                    .set_properties(**{'background-color': '#F7F7F7', 'color': '#222'})\
                    .set_table_styles([
                        {'selector': 'th', 'props': [('background-color', '#4CAF50'), ('color', 'white')]},
                        {'selector': 'td', 'props': [('font-size', '14px')]}
                    ])
                st.dataframe(styled_df, use_container_width=True)
            else:
                st.info("ℹ️ No hay datos para mostrar")
        else:
            st.info("ℹ️ Selecciona jugadores para ver el análisis individual")

        # ============================================================
    # TAB 2: ANÁLISIS DE EQUIPO
    # ============================================================
    with tab_equipo:
            st.markdown("## 👥 Análisis de Equipo por Categoría")
            st.markdown("**Información accesible para Entrenadores y Nutricionistas**")
            
            st.markdown("---")
            
            # 1️⃣ SELECTOR DE CATEGORÍAS - BIEN DESTACADO
            st.markdown("### Paso 1: ")
            categorias_equipo = crear_selector_categorias(df_nutricion)
            
            if not categorias_equipo:
                st.info("ℹ️ Selecciona una o más categorías para ver el análisis")
                st.stop()
            
            # 2️⃣ FILTRAR DATOS POR CATEGORÍAS
            df_categoria = df_nutricion[df_nutricion['Categoría'].isin(categorias_equipo)].copy()
            
            if df_categoria.empty:
                st.warning("⚠️ No hay jugadores en las categorías seleccionadas")
                st.stop()
            
            # Filtrar último registro por jugador (sin duplicados)
            df_categoria = filtrar_ultimo_registro_por_jugador(df_categoria)
            
            
            
            st.markdown("---")
            
            # 2️⃣ LEYENDA DE ESTADOS - EXPLICACIÓN DE COLORES
            st.markdown("### 📋 Paso 2: Leyenda de Estados")
            st.markdown("**Entiende qué significa cada color del semáforo:**")
            
            col_leg1, col_leg2, col_leg3 = st.columns(3)
            
            with col_leg1:
                st.error("🔴 **RIESGO**")
                st.markdown("""
                Requiere **acción inmediata** del nutricionista.
                
                Intervención urgente necesaria.
                """)
            
            with col_leg2:
                st.warning("🟡 **MONITOREO**")
                st.markdown("""
                Seguimiento **cercano** recomendado.
                
                En progreso hacia el objetivo.
                """)
            
            with col_leg3:
                st.success("🟢 **EN META**")
                st.markdown("""
                Protocolo actual **mantiene resultados**.
                
                Continuar con el plan vigente.
                """)
            
            st.markdown("---")
            
            # 3️⃣ RESUMEN DE ESTADOS - MÉTRICAS PRINCIPALES
            st.markdown("### 📊 Paso 3: Resumen por Estado")
            
            # Crear tabla de seguimiento para obtener datos
            df_seguimiento = crear_tabla_seguimiento_semanal(df_categoria)
            
            if df_seguimiento is not None and not df_seguimiento.empty:
                # Calcular totales - Convertir explícitamente a int
                rojos = int(len(df_seguimiento[df_seguimiento['Estado'].str.contains('🔴', na=False)]))
                amarillos = int(len(df_seguimiento[df_seguimiento['Estado'].str.contains('🟡', na=False)]))
                verdes = int(len(df_seguimiento[df_seguimiento['Estado'].str.contains('🟢', na=False)]))
                total = int(len(df_seguimiento))
                
                # Validar que total > 0 para evitar división por cero
                if total == 0:
                    st.warning("⚠️ No hay datos para calcular porcentajes")
                else:
                    # Mostrar métricas con estilos
                    col_met1, col_met2, col_met3, col_met4 = st.columns(4)
                    
                    with col_met1:
                        porcentaje_rojo = float((rojos / total * 100)) if total > 0 else 0.0
                        st.metric(
                            "🔴 Riesgo",
                            rojos,
                            f"{porcentaje_rojo:.1f}%",
                            help="Acción inmediata requerida"
                        )
                    
                    with col_met2:
                        # ✅ AGREGAR float() AQUÍ
                        porcentaje_amarillo = float((amarillos / total * 100)) if total > 0 else 0.0
                        st.metric(
                            "🟡 Monitoreo",
                            amarillos,
                            f"{porcentaje_amarillo:.1f}%",
                            help="Seguimiento cercano"
                        )
                    
                    with col_met3:
                        # ✅ AGREGAR float() AQUÍ
                        porcentaje_verde = float((verdes / total * 100)) if total > 0 else 0.0
                        st.metric(
                            "🟢 En Meta",
                            verdes,
                            f"{porcentaje_verde:.1f}%",
                            help="Mantener protocolo"
                        )
                    
                    with col_met4:
                        st.metric(
                            "📋 Total",
                            total,
                            "Jugadores",
                            help="Total de registros"
                        )
                
                # Gráfico de progreso visual
                st.markdown("**Distribución visual:**")
                
                datos_estados = {
                    '🔴 Riesgo': rojos,
                    '🟡 Monitoreo': amarillos,
                    '🟢 En Meta': verdes
                }
                
                fig_resumen = go.Figure(data=[
                    go.Bar(
                        x=list(datos_estados.keys()),
                        y=list(datos_estados.values()),
                        marker_color=['#FF6B6B', '#FFC107', '#4CAF50'],
                        text=list(datos_estados.values()),
                        textposition='auto'
                    )
                ])
                
                fig_resumen.update_layout(
                    height=300,
                    showlegend=False,
                    yaxis_title="Cantidad de Jugadores",
                    xaxis_title="Estado",
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                
                st.plotly_chart(fig_resumen, use_container_width=True)
                
                st.markdown("---")
                
                # 4️⃣ TABLA DE SEGUIMIENTO SEMANAL
                st.markdown("### 📋 Paso 4: Tabla de Seguimiento Semanal")
                st.markdown("**Datos detallados ordenados por prioridad (Rojo → Amarillo → Verde)**")
                
                # Mostrar tabla profesional
                mostrar_tabla_seguimiento_profesional(df_seguimiento)
                
            else:
                st.info("ℹ️ No hay datos suficientes para la tabla")