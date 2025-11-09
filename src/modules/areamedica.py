"""
Interfaz de Formularios Médicos con Streamlit
Sistema completo de captura y visualización de datos médicos
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
import json
import sys
import os
import streamlit as st
import json
import os

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
            "credentials/car-digital-441319-1a4e4b5c11c2.json",
            "../credentials/car-digital-441319-1a4e4b5c11c2.json"
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


# Importaciones opcionales - continuar si no están disponibles
try:
    from sheets.formularios_google_sheets import FormulariosGoogleSheets
except ImportError:
    FormulariosGoogleSheets = None

try:
    from auth_manager import AuthManager
except ImportError:
    AuthManager = None

import gspread
from google.oauth2.service_account import Credentials
from google.oauth2.service_account import Credentials

# Inicializar variables globales - se cargarán cuando se necesiten
creds_info = None
creds = None

with st.sidebar:
        st.header("🔧 Configuración")

        # --- MENÚ DE NAVEGACIÓN PRINCIPAL ---
        st.markdown("### 🗂 Navegación")
        paginas = {
            "🏠 Dashboard Principal": "dashboard",
            "🏥 Área Médica": "areamedica",
            "🥗 Área Nutrición": "nutricion",
            "🏋️ Área Física": "fisica"
        }
        for nombre, clave in paginas.items():
            if st.button(nombre):
                st.session_state['pagina'] = clave
                st.experimental_rerun()

        st.markdown("---")
        # Configuración de Google Sheets
        st.subheader("📊 Google Sheets")


# ...existing code...

def read_google_sheet_with_headers(sheet_id=None, worksheet_name=None, credentials_path=None):
    """
    Lee un Google Sheet usando la primera fila como nombres de columnas
    """
    global creds_info, creds
    
    # Configuración por defecto
    if sheet_id is None:
        sheet_id = '1zGyW-M_VV7iyDKVB1TTd0EEP3QBjdoiBmSJN2tK-H7w'
    
    # Cargar credenciales solo cuando se necesiten
    if creds_info is None:
        creds_info = get_google_credentials()
        
    if creds_info is None:
        return {
            'success': False,
            'data': None,
            'columns': None,
            'message': 'No se pudieron cargar las credenciales de Google'
        }
    
    try:
        SCOPES = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Crear credenciales solo cuando se necesiten
        if creds is None:
            creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
        
        gc = gspread.authorize(creds)
        
      
        # Abrir el Google Sheet
        sh = gc.open_by_key(sheet_id)
        
        # Seleccionar la hoja de trabajo
        if worksheet_name:
            worksheet = sh.worksheet(worksheet_name)
        else:
            worksheets = sh.worksheets()
            worksheet = None
            for ws in worksheets:
                if ws.id == 982269766:
                    worksheet = ws
                    break
            if worksheet is None:
                worksheet = sh.get_worksheet(0)
        
        # Leer todos los datos
        all_data = worksheet.get_all_values()
        
        if not all_data:
            return {
                'success': False,
                'data': None,
                'columns': None,
                'message': 'La hoja está vacía'
            }
        
        # Primera fila como columnas
        columns = all_data[0]
        data_rows = all_data[1:]  # Resto de filas como datos
        
        # Crear lista de diccionarios (cada fila es un diccionario)
        structured_data = []
        for row in data_rows:
            row_data = {}
            for i, column in enumerate(columns):
                value = row[i] if i < len(row) else ''
                row_data[column] = value
            structured_data.append(row_data)
        
        return {
            'success': True,
            'data': structured_data,
            'columns': columns,
            'raw_data': data_rows,
            'total_rows': len(data_rows),
            'sheet_title': sh.title,
            'worksheet_title': worksheet.title,
            'message': f'Datos leídos exitosamente: {len(data_rows)} filas, {len(columns)} columnas'
        }
        
    except gspread.exceptions.SpreadsheetNotFound:
        return {
            'success': False,
            'data': None,
            'columns': None,
            'message': 'Google Sheet no encontrado. Verifica el ID y permisos.'
        }
        
    except gspread.exceptions.APIError as e:
        return {
            'success': False,
            'data': None,
            'columns': None,
            'message': f'Error de API: {e}. Verifica que hayas compartido el sheet con la cuenta de servicio.'
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'columns': None,
            'message': f'Error inesperado: {e}'
        }


def create_dataframe_from_sheet(sheet_id=None, worksheet_name=None):
    """
    Crea un DataFrame de pandas desde el Google Sheet
    
    Returns:
        pandas.DataFrame o None si hay error
    """
    result = read_google_sheet_with_headers(sheet_id, worksheet_name)
    
    if result['success']:
        df = pd.DataFrame(result['data'])
        return df
    else:
        return None

# ==========================================
# INTERFAZ STREAMLIT
# ==========================================

def main_streamlit():
    """
    Interfaz principal de Streamlit para visualizar datos de Google Sheets
    """
    st.set_page_config(
        page_title="CAR - Sistema Digital",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded"  # <-- Sidebar visible por defecto
    )

    # CSS personalizado para el diseño profesional
    st.markdown("""
    <style>
    /* Ocultar elementos de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Estilo del contenedor principal */
    .main > div {
        padding-top: 0rem;
    }
    
    /* Header principal con gradiente azul */
    .header-container {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #60a5fa 100%);
        padding: 3rem 2rem;
        margin: -1rem -1rem 2rem -1rem;
        border-radius: 0 0 20px 20px;
        text-align: center;
        box-shadow: 0 8px 32px rgba(30, 58, 138, 0.3);
    }
    
    .header-title {
        color: white;
        font-size: 3rem;
        font-weight: 800;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .header-subtitle {
        color: #e0f2fe;
        font-size: 1.2rem;
        font-weight: 400;
        margin: 0.5rem 0 0 0;
        opacity: 0.95;
    }
    
    /* Estilo de las tarjetas métricas */
    .metric-container {
        background: linear-gradient(135deg, #1e40af 0%, #2563eb 100%);
        padding: 2rem 1.5rem;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 8px 25px rgba(37, 99, 235, 0.25);
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin: 0.5rem;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .metric-container:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 35px rgba(37, 99, 235, 0.4);
    }
    
    .metric-number {
        color: white;
        font-size: 3.5rem;
        font-weight: 800;
        margin: 0;
        line-height: 1;
    }
    
    .metric-label {
        color: #bfdbfe;
        font-size: 1.1rem;
        font-weight: 500;
        margin: 0.5rem 0 0 0;
    }
    
    /* Contenedor de métricas */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1rem;
        margin: 2rem 0;
    }
    
    /* Estilo para gráficos */
    .chart-container {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header principal con diseño profesional
    st.markdown("""
    <div class="header-container">
        <h1 class="header-title">⚡ Sistema digital CAR</h1>
        <p class="header-subtitle">Sistema Integral de Gestión Deportiva Profesional</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar con configuración
    with st.sidebar:
        st.header("🔧 Configuración")
        
        # Configuración de Google Sheets
        st.subheader("📊 Google Sheets")
        
        sheet_id = st.text_input(
            "ID del Google Sheet:",
            value="1zGyW-M_VV7iyDKVB1TTd0EEP3QBjdoiBmSJN2tK-H7w",
            help="ID del Google Sheet que contiene los datos médicos"
        )
        
        worksheet_name = st.text_input(
            "Nombre de la hoja (opcional):",
            value="",
            help="Deja vacío para usar la hoja principal"
        )
        
        st.markdown("---")
        
        # Estado del sistema
        st.subheader("📋 Estado del Sistema")
        
        # Verificar credenciales
        credenciales_encontradas = False
        rutas_credenciales = [
            "../credentials/service_account.json",
            "credentials/service_account.json",
            "C:/Users/dell/Desktop/Car/credentials/service_account.json"
        ]
        
        for ruta in rutas_credenciales:
            if os.path.exists(ruta):
                st.success(f"✅ Credenciales: {ruta}")
                credenciales_encontradas = True
                break
        
        if not credenciales_encontradas:
            st.error("❌ Credenciales no encontradas")
            st.info("💡 Asegúrate de tener el archivo service_account.json en la carpeta credentials")

    # CARGAR DATOS AUTOMÁTICAMENTE (sin botón)
    with st.spinner("🔄 Cargando datos desde Google Sheets..."):
        try:
            # Llamar a la función existente
            result = read_google_sheet_with_headers(sheet_id, worksheet_name or None)
            
            if result['success']:
                
                
                # Crear DataFrame
                df = pd.DataFrame(result['data'])
                
                # MOSTRAR DIRECTAMENTE EL RESUMEN (sin pestañas)
                mostrar_resumen_datos(df)
                
                # MOSTRAR GRÁFICOS INTERACTIVOS
                mostrar_graficos_interactivos(df)
            else:
                st.error(f"❌ Error al cargar datos: {result['message']}")
                
                # Mostrar información de ayuda
                with st.expander("💡 Solución de Problemas", expanded=True):
                    st.markdown("""
                    **Posibles soluciones:**
                    1. Verifica que el archivo `service_account.json` esté en la carpeta `credentials`
                    2. Asegúrate de que el Google Sheet sea accesible
                    3. Verifica que la cuenta de servicio tenga permisos de lectura
                    4. Confirma que el ID del Sheet sea correcto
                    """)
                
        except Exception as e:
            st.error(f"❌ Error inesperado: {str(e)}")

def mostrar_resumen_datos(df):
    """
    Muestra resumen estadístico de los datos con tarjetas métricas estilo profesional
    """
    
    # Calcular métricas
    total_lesionados = len(df)
    
    if 'Severidad de la lesión' in df.columns:
        en_recuperacion = len(df[df['Severidad de la lesión'].str.contains('Leve|Moderada', case=False, na=False)])
        recuperados = len(df[df['Severidad de la lesión'].str.contains('Leve \(1-7 días\)', case=False, na=False)])
        casos_graves = len(df[df['Severidad de la lesión'].str.contains('Grave|Muy grave', case=False, na=False)])
    else:
        en_recuperacion = 0
        recuperados = 0
        casos_graves = 0
    
    # Tarjetas métricas con diseño profesional
    st.markdown("""
    <div class="metrics-grid">
        <div class="metric-container">
            <div class="metric-number">{}</div>
            <div class="metric-label">Lesiones totales</div>
        </div>
        <div class="metric-container">
            <div class="metric-number">{}</div>
            <div class="metric-label">En Recuperación</div>
        </div>
        <div class="metric-container">
            <div class="metric-number">{}</div>
            <div class="metric-label">Recuperados</div>
        </div>
        <div class="metric-container">
            <div class="metric-number">{}</div>
            <div class="metric-label">Casos Graves</div>
        </div>
    </div>
    """.format(total_lesionados, en_recuperacion, recuperados, casos_graves), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Gráficos con diseño profesional
    if 'Severidad de la lesión' in df.columns:
        severidad_counts = df['Severidad de la lesión '].value_counts()
        
        # Contenedor para gráficos
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Distribución por Severidad")
            # Gráfico de barras con colores azules
            fig = px.bar(
                x=severidad_counts.index,
                y=severidad_counts.values,
                color_discrete_sequence=['#1e40af', '#2563eb', '#3b82f6', '#60a5fa']
            )
            
            fig.update_layout(
                showlegend=False,
                xaxis_title="Severidad de la Lesión",
                yaxis_title="Cantidad de Jugadores",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#374151')
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### 📈 Análisis Porcentual")
            # Gráfico de dona con colores azules
            fig_pie = px.pie(
                values=severidad_counts.values,
                names=severidad_counts.index,
                hole=0.4,
                color_discrete_sequence=['#1e40af', '#2563eb', '#3b82f6', '#60a5fa']
            )
            
            fig_pie.update_layout(
                showlegend=True,
                legend=dict(orientation="v", yanchor="middle", y=0.5),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#374151')
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)


def mostrar_graficos_interactivos(df):
    """
    Muestra gráficos interactivos con filtros - VERSIÓN CORREGIDA
    """
    st.markdown("---")
    st.markdown("### 📊 Informe de Lesiones por División")
    
    # NOMBRES CORRECTOS DE LAS COLUMNAS
    col_categoria = 'Categoría'  # ← CON TILDE
    col_severidad = 'Severidad de la lesión  '  # ← CON ESPACIOS EXTRA
    
    # Limpiar datos si es necesario
    if col_severidad in df.columns:
        df[col_severidad] = df[col_severidad].str.strip()  # Quitar espacios extra
    
    # Filtros interactivos
    col_filtro1, col_filtro2 = st.columns(2)
    
    with col_filtro1:
        # Filtro por División/Categorías
        if col_categoria in df.columns:
            categorias_disponibles = ['Todas'] + sorted(df[col_categoria].dropna().unique().tolist())
            categoria_seleccionada = st.selectbox(
                "🔍 Seleccionar División",
                categorias_disponibles,
                key="filtro_categoria"
            )
        else:
            categoria_seleccionada = 'Todas'
            st.info(f"⚠️ Columna '{col_categoria}' no encontrada")
    
    with col_filtro2:
        # Filtro por Estado/Severidad
        if col_severidad in df.columns:
            estados_disponibles = ['Todos'] + sorted(df[col_severidad].dropna().unique().tolist())
            estado_seleccionado = st.selectbox(
                "📋 Estado",
                estados_disponibles,
                key="filtro_estado"
            )
        else:
            estado_seleccionado = 'Todos'
            st.info(f"⚠️ Columna '{col_severidad}' no encontrada")
        
    # Filtrar DataFrame según selecciones
    df_filtrado = df.copy()
    
    if categoria_seleccionada != 'Todas' and col_categoria in df.columns:
        df_filtrado = df_filtrado[df_filtrado[col_categoria] == categoria_seleccionada]
    
    if estado_seleccionado != 'Todos' and col_severidad in df.columns:
        df_filtrado = df_filtrado[df_filtrado[col_severidad] == estado_seleccionado]
    
    # Gráficos lado a lado
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Lesiones por División")
        
        if col_categoria in df_filtrado.columns and not df_filtrado.empty:
            # Contar lesiones por categoría
            categorias_counts = df_filtrado['Categoría'].value_counts()
            
            # Gráfico de barras con colores azules oscuros (como en la imagen)
            fig_categorias = px.bar(
                x=categorias_counts.index,
                y=categorias_counts.values,
                color_discrete_sequence=['#1e3a8a', '#1e40af', '#2563eb', '#3b82f6']
            )
            
            fig_categorias.update_layout(
                showlegend=False,
                xaxis_title="División",
                yaxis_title="Cantidad de Lesiones",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#374151', size=12),
                height=400,
                margin=dict(t=20, b=20, l=20, r=20)
            )
            
            fig_categorias.update_traces(
                texttemplate='%{y}',
                textposition='outside'
            )
            
            st.plotly_chart(fig_categorias, use_container_width=True)
            
            # Mostrar estadísticas
            st.info(f"📈 Total de divisiones: {len(categorias_counts)} | Registros mostrados: {len(df_filtrado)}")
            
        else:
            st.warning("⚠️ No hay datos de categorías para mostrar")
    
    with col2:
        st.markdown("#### 🎯 Distribución por Severidad")
        
        if col_severidad in df_filtrado.columns and not df_filtrado.empty:
            # Contar por severidad
            severidad_counts = df_filtrado[col_severidad].value_counts()
            
            # Gráfico de torta con colores como en la imagen (verde, amarillo, rojo)
            colores_severidad = {
                'Leve (1-7 días)': '#22c55e',      # Verde
                'Moderada (1-4 semanas)': '#eab308', # Amarillo
                'Grave (1-3 meses)': "#df6767",     # Rojo
                'Muy grave (+3 meses)': '#dc2626'   # Rojo oscuro
            }
            
            # Crear lista de colores basada en los datos
            colores = [colores_severidad.get(sev, '#64748b') for sev in severidad_counts.index]
            
            fig_severidad = px.pie(
                values=severidad_counts.values,
                names=severidad_counts.index,
                color_discrete_sequence=colores
            )
            
            fig_severidad.update_layout(
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.05
                ),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#374151', size=12),
                height=400,
                margin=dict(t=20, b=20, l=20, r=80)
            )
            
            fig_severidad.update_traces(
                textposition='inside',
                textinfo='percent+label',
                textfont_size=12
            )
            
            st.plotly_chart(fig_severidad, use_container_width=True)
            
            # Mostrar estadísticas
            st.info(f"📊 Tipos de severidad: {len(severidad_counts)} | Total lesiones: {severidad_counts.sum()}")
            
        else:
            st.warning("⚠️ No hay datos de severidad para mostrar")
    
    # Tabla resumen de datos filtrados
    if not df_filtrado.empty:
        st.markdown("---")
        st.markdown("#### 📋 Vista Detallada de Datos Filtrados")
        
        # Información de filtros aplicados
        filtros_aplicados = []
        if categoria_seleccionada != 'Todas':
            filtros_aplicados.append(f"División: {categoria_seleccionada}")
        if estado_seleccionado != 'Todos':
            filtros_aplicados.append(f"Estado: {estado_seleccionado}")
        
        if filtros_aplicados:
            st.info(f"🔍 Filtros aplicados: {' | '.join(filtros_aplicados)}")
        
        # Mostrar tabla con scroll
        st.dataframe(
            df_filtrado,
            use_container_width=True,
            height=300
        )
        
        # Botón de descarga
        csv_data = df_filtrado.to_csv(index=False)
        st.download_button(
            label="📥 Descargar Datos Filtrados",
            data=csv_data,
            file_name=f"lesiones_filtradas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.warning("⚠️ No hay datos que coincidan con los filtros seleccionados")




    
   
# ==========================================
# EJECUTAR APLICACIÓN
# ==========================================

if __name__ == "__main__":
    # Si se ejecuta directamente, iniciar Streamlit
    main_streamlit()
