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

def get_google_credentials():
    """
    Obtiene las credenciales de Google de forma segura
    """
    try:
        # Verificar si st.secrets está disponible y tiene datos de Google
        if hasattr(st, 'secrets') and hasattr(st.secrets, '_file_paths') and st.secrets._file_paths:
            # Solo verificar si el archivo secrets existe
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
    except Exception:
        # Si hay cualquier error con secrets, continuar con archivos locales
        pass
    
    # Si estamos local o no hay secrets, leemos el archivo
    try:
        # Buscar el archivo de credenciales en varias ubicaciones
        possible_paths = [
            "credentials/service_account.json",
            "../credentials/service_account.json", 
            "C:/Users/dell/Desktop/Car/credentials/service_account.json"
        ]
        
        for cred_path in possible_paths:
            if os.path.exists(cred_path):
                with open(cred_path) as f:
                    return json.load(f)
        
        # Si no encuentra ningún archivo
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

# ...existing code...
    
    
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
    columna_fecha = obtener_columna_fecha(df_hist)
    columna_peso = 'Peso (kg): [Número con decimales 88,5]'
    if columna_fecha and columna_peso in df_hist.columns:
        # Convertir columna de fecha a datetime y eliminar filas sin fecha válida
        df_hist[columna_fecha] = pd.to_datetime(df_hist[columna_fecha], errors='coerce')
        df_hist = df_hist.dropna(subset=[columna_fecha])
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
            text=[f"{peso:.1f} kg" for peso in df_hist_ordenado[columna_peso]],
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