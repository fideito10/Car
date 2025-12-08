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
            "../credentials/service-account-key.json",
            "credentials/service_account.json",
            "../credentials/service_account.json", 
            "credentials/car-digital-441319-1a4e4b5c11c2.json",
            "../credentials/car-digital-441319-1a4e4b5c11c2.json"
        ]
        
        for cred_path in possible_paths:
            if os.path.exists(cred_path):
                with open(cred_path) as f:
                    return json.load(f)
        
        raise FileNotFoundError("No se encontró archivo de credenciales")
        
    except Exception as e:
        st.error(f"❌ Error cargando credenciales: {e}")
        return None

# Importaciones opcionales
try:
    from sheets.formularios_google_sheets import FormulariosGoogleSheets
except ImportError:
    FormulariosGoogleSheets = None

try:
    from .auth_manager import AuthManager
except ImportError:
    try:
        from auth_manager import AuthManager
    except ImportError:
        AuthManager = None

import gspread
from google.oauth2.service_account import Credentials

# Variables globales
creds_info = None
creds = None

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
        
        # Seleccionar la hoja de trabajo - MEJORADO
        if worksheet_name:
            worksheet = sh.worksheet(worksheet_name)
        else:
            worksheets = sh.worksheets()
            worksheet = None
            
            # Buscar por ID específico
            target_id = 982269766
            for ws in worksheets:
                if ws.id == target_id:
                    worksheet = ws
                    break
            
            # Si no encuentra por ID, usar la primera
            if worksheet is None:
                # st.warning(f"⚠️ No se encontró worksheet con ID {target_id}, usando la primera hoja")
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
        data_rows = all_data[1:]
        
        # Crear lista de diccionarios
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
    """
    result = read_google_sheet_with_headers(sheet_id, worksheet_name)
    
    if result['success']:
        df = pd.DataFrame(result['data'])
        return df
    else:
        return None

def mostrar_resumen_datos(df):
    """
    Muestra resumen estadístico de los datos con tarjetas métricas
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
    
    # Tarjetas métricas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📋 Lesiones Totales", total_lesionados)
    with col2:
        st.metric("🔄 En Recuperación", en_recuperacion)
    with col3:
        st.metric("✅ Recuperados", recuperados)
    with col4:
        st.metric("⚠️ Casos Graves", casos_graves)

def mostrar_filtros_jugador_categoria(df):
    """
    Muestra filtros por categoría y jugador con información detallada
    """
    st.markdown("### 🔍 Filtros por Categoría y Jugador")
    
    # Nombres de columnas
    col_categoria = 'Categoría'
    col_jugador = 'Nombre del Paciente'
    
    # Filtros en columnas
    col_filtro1, col_filtro2 = st.columns(2)
    
    with col_filtro1:
        # FILTRO IZQUIERDO - CATEGORÍAS
        if col_categoria in df.columns:
            categorias_disponibles = ['Todas'] + sorted(df[col_categoria].dropna().unique().tolist())
            categoria_seleccionada = st.selectbox(
                "🏈 Seleccionar División",
                categorias_disponibles,
                key="area_medica_filtro_categoria"
            )
        else:
            categoria_seleccionada = 'Todas'
    
    with col_filtro2:
        # FILTRO DERECHO - JUGADORES (FILTRADOS POR CATEGORÍA)
        if col_jugador in df.columns:
            # AQUÍ ESTÁ LA MAGIA: Si hay categoría seleccionada, filtra los jugadores
            if categoria_seleccionada != 'Todas':
                jugadores_filtrados = df[df[col_categoria] == categoria_seleccionada][col_jugador].dropna().unique()
            else:
                jugadores_filtrados = df[col_jugador].dropna().unique()
            
            jugadores_disponibles = ['Todos'] + sorted(jugadores_filtrados.tolist())
            jugador_seleccionado = st.selectbox(
                "👤 Seleccionar Jugador",
                jugadores_disponibles,
                key="area_medica_filtro_jugador"
            )
        else:
            jugador_seleccionado = 'Todos'
    
    # Aplicar filtros al DataFrame
    df_filtrado = df.copy()
    
    # Aplicar filtro de categoría
    if categoria_seleccionada != 'Todas' and col_categoria in df.columns:
        df_filtrado = df_filtrado[df_filtrado[col_categoria] == categoria_seleccionada]
    
    # Aplicar filtro de jugador específico
    if jugador_seleccionado != 'Todos' and col_jugador in df.columns:
        df_filtrado = df_filtrado[df_filtrado[col_jugador] == jugador_seleccionado]
    
    # Mostrar información de filtros aplicados
    info_filtros = []
    if categoria_seleccionada != 'Todas':
        info_filtros.append(f"**División:** {categoria_seleccionada}")
    if jugador_seleccionado != 'Todos':
        info_filtros.append(f"**Jugador:** {jugador_seleccionado}")
    
    if info_filtros:
        st.info(f"🔍 **Filtros activos:** {' | '.join(info_filtros)}")
    
    # Mostrar resultados filtrados
    if not df_filtrado.empty:
        st.success(f"✅ **{len(df_filtrado)} registro(s) encontrado(s)**")
        
        # Si es un jugador específico, mostrar información detallada
        if jugador_seleccionado != 'Todos':
            st.markdown(f"#### 👤 Historial Médico de {jugador_seleccionado}")
            
            # Mostrar resumen del jugador
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📋 Total Lesiones", len(df_filtrado))
            with col2:
                if 'Severidad de la lesión' in df_filtrado.columns:
                    graves = len(df_filtrado[df_filtrado['Severidad de la lesión'].str.contains('Grave', case=False, na=False)])
                    st.metric("⚠️ Lesiones Graves", graves)
                else:
                    st.metric("⚠️ Lesiones Graves", "N/A")
            with col3:
                if 'Fecha' in df_filtrado.columns:
                    try:
                        fechas = pd.to_datetime(df_filtrado['Fecha'], errors='coerce').dropna()
                        if not fechas.empty:
                            ultima_lesion = fechas.max().strftime('%d/%m/%Y')
                            st.metric("📅 Última Lesión", ultima_lesion)
                        else:
                            st.metric("📅 Última Lesión", "N/A")
                    except:
                        st.metric("📅 Última Lesión", "N/A")
        
        # Mostrar tabla de datos
        st.dataframe(df_filtrado, use_container_width=True, height=400)
        
        # Botón para descargar datos filtrados
        if len(df_filtrado) > 0:
            csv = df_filtrado.to_csv(index=False)
            st.download_button(
                label="📥 Descargar datos filtrados",
                data=csv,
                file_name=f"lesiones_filtradas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    else:
        st.warning("⚠️ No se encontraron registros con los filtros seleccionados")
    
    # Devolver el DataFrame filtrado para uso en otras funciones
    return df_filtrado

def test_google_connection():
    """
    Prueba la conexión con Google Sheets y muestra información de diagnóstico
    """
    st.sidebar.markdown("### 🧪 Test de Conexión")
    
    if st.sidebar.button("🔗 Probar Conexión"):
        with st.sidebar.spinner("Probando conexión..."):
            # Test básico de credenciales
            creds = get_google_credentials()
            if creds is None:
                st.sidebar.error("❌ No se encontraron credenciales")
                return
            
            st.sidebar.success("✅ Credenciales cargadas")
            
            # Test de conexión al sheet
            result = read_google_sheet_with_headers()
            
            if result['success']:
                st.sidebar.success(f"✅ Conexión exitosa")
                st.sidebar.info(f"📊 {result['total_rows']} filas, {len(result['columns'])} columnas")
                
                with st.sidebar.expander("Ver detalles"):
                    st.write("**Información del Sheet:**")
                    st.write(f"- Título: {result.get('sheet_title', 'N/A')}")
                    st.write(f"- Hoja: {result.get('worksheet_title', 'N/A')}")
                    st.write(f"- Mensaje: {result['message']}")
                    
                    st.write("**Columnas encontradas:**")
                    for i, col in enumerate(result['columns']):
                        st.write(f"{i+1}. `{col}`")
            else:
                st.sidebar.error(f"❌ Error: {result['message']}")

def mostrar_graficos_interactivos(df):
    """
    Muestra gráficos interactivos con filtros
    """
    st.markdown("### 📊 Análisis de Lesiones")
    
    # Nombres de columnas
    col_categoria = 'Categoría'
    col_severidad = 'Severidad de la lesión'
    
    # Limpiar datos
    if col_severidad in df.columns:
        df[col_severidad] = df[col_severidad].str.strip()
    
    # Gráficos
    if col_categoria in df.columns and not df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Lesiones por División")
            categorias_counts = df[col_categoria].value_counts()
            
            fig = px.bar(
                x=categorias_counts.index,
                y=categorias_counts.values,
                color_discrete_sequence=['#1e40af', '#2563eb', '#3b82f6']
            )
            
            fig.update_layout(
                showlegend=False,
                xaxis_title="División",
                yaxis_title="Cantidad",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if col_severidad in df.columns:
                st.markdown("#### 🎯 Distribución por Severidad")
                severidad_counts = df[col_severidad].value_counts()
                
                fig_pie = px.pie(
                    values=severidad_counts.values,
                    names=severidad_counts.index,
                    color_discrete_sequence=['#22c55e', '#eab308', '#ef4444', '#dc2626']
                )
                
                fig_pie.update_layout(height=400)
                st.plotly_chart(fig_pie, use_container_width=True)


def append_google_sheet_row(sheet_id, worksheet_name, row_data, credentials_dict):
    """Agrega una fila a una hoja de Google Sheets"""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(credentials_dict, scopes=scopes)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(sheet_id)
    ws = sh.worksheet(worksheet_name)
    ws.append_row(row_data, value_input_option="USER_ENTERED")
    return True


# Agregar después de la función mostrar_graficos_interactivos:

def mostrar_timeline_lesiones(df):
    """
    Muestra timeline de lesiones por fecha
    """
    if 'Fecha' in df.columns and not df.empty:
        st.markdown("#### 📅 Timeline de Lesiones")
        
        # Convertir fechas
        df_timeline = df.copy()
        df_timeline['Fecha'] = pd.to_datetime(df_timeline['Fecha'], errors='coerce')
        df_timeline = df_timeline.dropna(subset=['Fecha'])
        
        if not df_timeline.empty:
            # Agrupar por fecha
            lesiones_por_fecha = df_timeline.groupby(df_timeline['Fecha'].dt.date).size().reset_index()
            lesiones_por_fecha.columns = ['Fecha', 'Cantidad']
            
            fig = px.line(
                lesiones_por_fecha, 
                x='Fecha', 
                y='Cantidad',
                title="Evolución Temporal de Lesiones",
                markers=True
            )
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

def mostrar_estadisticas_avanzadas(df):
    """
    Estadísticas avanzadas y alertas
    """
    if not df.empty:
        st.markdown("#### 🚨 Alertas y Estadísticas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Jugadores con más lesiones
            if 'Nombre del Paciente' in df.columns:
                jugadores_frecuentes = df['Nombre del Paciente'].value_counts().head(5)
                
                if len(jugadores_frecuentes) > 0:
                    st.warning("⚠️ **Jugadores con más lesiones:**")
                    for jugador, cantidad in jugadores_frecuentes.items():
                        if cantidad > 2:  # Alerta si tiene más de 2 lesiones
                            st.write(f"🔴 {jugador}: {cantidad} lesiones")
                        else:
                            st.write(f"🟡 {jugador}: {cantidad} lesiones")
        
        with col2:
            # Divisiones más afectadas
            if 'Categoría' in df.columns:
                divisiones_afectadas = df['Categoría'].value_counts()
                
                st.info("📊 **Divisiones más afectadas:**")
                for division, cantidad in divisiones_afectadas.items():
                    porcentaje = (cantidad / len(df)) * 100
                    st.write(f"🏈 {division}: {cantidad} ({porcentaje:.1f}%)")


def mostrar_dashboard_tendencias_lesiones(df):
    """
    Dashboard completo para análisis de tendencias de lesiones
    Objetivo: Identificar partes del cuerpo y tipos de lesiones más frecuentes
    """
    st.markdown("---")
    st.markdown("""
    <div style="background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%); padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
        <h2 style="color: white; text-align: center; margin: 0;">🔬 Análisis de Tendencias de Lesiones</h2>
        <p style="color: rgba(255,255,255,0.9); text-align: center; margin: 0.5rem 0 0 0;">Identificación de patrones y zonas críticas</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ============================================
    # SECCIÓN 1: FILTROS AVANZADOS
    # ============================================
    st.markdown("### 🎯 Filtros de Análisis")
    
    col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
    
    with col_filtro1:
        # Filtro de Fechas
        if 'Fecha' in df.columns:
            df['Fecha_parsed'] = pd.to_datetime(df['Fecha'], errors='coerce')
            fechas_validas = df['Fecha_parsed'].dropna()
            
            if not fechas_validas.empty:
                fecha_min = fechas_validas.min().date()
                fecha_max = fechas_validas.max().date()
                
                rango_fechas = st.date_input(
                    "📅 Rango de Fechas",
                    value=(fecha_min, fecha_max),
                    min_value=fecha_min,
                    max_value=fecha_max,
                    key="tendencias_fecha"
                )
            else:
                rango_fechas = None
        else:
            rango_fechas = None
            st.warning("⚠️ No hay columna de fechas")
    
    with col_filtro2:
        # Filtro de Categoría
        if 'Categoría' in df.columns:
            categorias = ['Todas'] + sorted(df['Categoría'].dropna().unique().tolist())
            cat_seleccionada = st.selectbox(
                "🏈 División",
                categorias,
                key="tendencias_categoria"
            )
        else:
            cat_seleccionada = 'Todas'
    
    with col_filtro3:
        # Filtro de Parte del Cuerpo (NUEVA FUNCIONALIDAD)
        # Buscar posibles columnas que contengan partes del cuerpo
        posibles_columnas_parte = [col for col in df.columns if 'parte' in col.lower() or 'cuerpo' in col.lower() or 'zona' in col.lower()]
        
        if posibles_columnas_parte:
            col_parte = posibles_columnas_parte[0]
            partes = ['Todas'] + sorted(df[col_parte].dropna().unique().tolist())
            parte_seleccionada = st.selectbox(
                "🎯 Parte del Cuerpo",
                partes,
                key="tendencias_parte"
            )
        else:
            parte_seleccionada = 'Todas'
            st.info("💡 Agrega columna 'Parte Afectada' en el Sheet")
    
    # ============================================
    # APLICAR FILTROS
    # ============================================
    df_analisis = df.copy()
    
    # Filtro de fechas
    if rango_fechas and len(rango_fechas) == 2:
        fecha_inicio, fecha_fin = rango_fechas
        df_analisis = df_analisis[
            (df_analisis['Fecha_parsed'].dt.date >= fecha_inicio) & 
            (df_analisis['Fecha_parsed'].dt.date <= fecha_fin)
        ]
    
    # Filtro de categoría
    if cat_seleccionada != 'Todas' and 'Categoría' in df.columns:
        df_analisis = df_analisis[df_analisis['Categoría'] == cat_seleccionada]
    
    # Filtro de parte del cuerpo
    if parte_seleccionada != 'Todas' and posibles_columnas_parte:
        df_analisis = df_analisis[df_analisis[col_parte] == parte_seleccionada]
    
    # Mostrar info de filtros
    if not df_analisis.empty:
        st.success(f"✅ **{len(df_analisis)} lesiones** en el período seleccionado")
    else:
        st.warning("⚠️ No hay datos con los filtros seleccionados")
        return
    
    st.markdown("---")
    
    # ============================================
    # SECCIÓN 2: MÉTRICAS PRINCIPALES
    # ============================================
    st.markdown("### 📊 Resumen Ejecutivo")
    
    col_met1, col_met2, col_met3, col_met4 = st.columns(4)
    
    with col_met1:
        total_lesiones = len(df_analisis)
        st.metric(
            "📋 Total Lesiones",
            total_lesiones,
            delta=None
        )
    
    with col_met2:
        # Parte del cuerpo más afectada
        if posibles_columnas_parte and col_parte in df_analisis.columns:
            parte_mas_comun = df_analisis[col_parte].mode()
            if not parte_mas_comun.empty:
                parte_top = parte_mas_comun.iloc[0]
                cantidad_parte = len(df_analisis[df_analisis[col_parte] == parte_top])
                st.metric(
                    "🎯 Zona Crítica",
                    parte_top,
                    delta=f"{cantidad_parte} casos"
                )
            else:
                st.metric("🎯 Zona Crítica", "N/A")
        else:
            st.metric("🎯 Zona Crítica", "Sin datos")
    
    with col_met3:
        # Gravedad predominante
        if 'Severidad de la Lesión' in df_analisis.columns:
            severidad_top = df_analisis['Severidad de la Lesión'].mode()
            if not severidad_top.empty:
                st.metric(
                    "⚠️ Severidad Predominante",
                    severidad_top.iloc[0]
                )
            else:
                st.metric("⚠️ Severidad Predominante", "N/A")
        else:
            st.metric("⚠️ Severidad Predominante", "Sin datos")
    
    with col_met4:
        # Promedio lesiones por mes
        if 'Fecha_parsed' in df_analisis.columns:
            meses_unicos = df_analisis['Fecha_parsed'].dt.to_period('M').nunique()
            if meses_unicos > 0:
                promedio_mes = total_lesiones / meses_unicos
                st.metric(
                    "📈 Promedio Mensual",
                    f"{promedio_mes:.1f}",
                    delta=None
                )
            else:
                st.metric("📈 Promedio Mensual", "N/A")
        else:
            st.metric("📈 Promedio Mensual", "Sin datos")
    
    st.markdown("---")
    
    # ============================================
    # SECCIÓN 3: GRÁFICOS PRINCIPALES
    # ============================================
    st.markdown("### 📊 Análisis Visual de Tendencias")
    
    # FILA 1: TOP 5 LESIONES + EVOLUCIÓN TEMPORAL
    col_graf1, col_graf2 = st.columns([1, 1.5])
    
    with col_graf1:
        st.markdown("#### 🏆 Top 5 Partes del Cuerpo Más Afectadas")
        
        if posibles_columnas_parte and col_parte in df_analisis.columns:
            top_partes = df_analisis[col_parte].value_counts().head(5)
            
            if not top_partes.empty:
                fig_top = px.bar(
                    x=top_partes.values,
                    y=top_partes.index,
                    orientation='h',
                    color=top_partes.values,
                    color_continuous_scale='Reds',
                    labels={'x': 'Cantidad', 'y': 'Parte del Cuerpo'}
                )
                
                fig_top.update_layout(
                    height=400,
                    showlegend=False,
                    coloraxis_showscale=False
                )
                
                st.plotly_chart(fig_top, use_container_width=True)
                
                # Mostrar tabla de top 5
                st.markdown("**Detalle:**")
                for i, (parte, cantidad) in enumerate(top_partes.items(), 1):
                    porcentaje = (cantidad / total_lesiones) * 100
                    emoji = "🔴" if i == 1 else "🟠" if i == 2 else "🟡"
                    st.write(f"{emoji} **{i}. {parte}:** {cantidad} casos ({porcentaje:.1f}%)")
            else:
                st.info("No hay datos de partes del cuerpo")
        else:
            st.warning("⚠️ Agrega columna 'Parte Afectada' en Google Sheets para ver este análisis")
            st.info("""
            💡 **Sugerencia:** Crea una columna llamada:
            - `Parte Afectada` o
            - `Zona del Cuerpo` o
            - `Parte del Cuerpo`
            
            Con valores como: Rodilla, Tobillo, Isquiotibiales, etc.
            """)
    
    with col_graf2:
        st.markdown("#### 📈 Evolución Temporal de Lesiones")
        
        if 'Fecha_parsed' in df_analisis.columns:
            df_timeline = df_analisis.copy()
            df_timeline['Mes'] = df_timeline['Fecha_parsed'].dt.to_period('M').astype(str)
            
            lesiones_por_mes = df_timeline.groupby('Mes').size().reset_index(name='Cantidad')
            
            if not lesiones_por_mes.empty:
                fig_timeline = px.line(
                    lesiones_por_mes,
                    x='Mes',
                    y='Cantidad',
                    markers=True,
                    labels={'Mes': 'Período', 'Cantidad': 'Número de Lesiones'}
                )
                
                fig_timeline.update_traces(
                    line_color='#dc2626',
                    marker=dict(size=10, color='#ef4444'),
                    fill='tozeroy',
                    fillcolor='rgba(220, 38, 38, 0.1)'
                )
                
                fig_timeline.update_layout(
                    height=400,
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig_timeline, use_container_width=True)
                
                # Detectar picos
                if len(lesiones_por_mes) > 1:
                    max_mes = lesiones_por_mes.loc[lesiones_por_mes['Cantidad'].idxmax()]
                    st.warning(f"⚠️ **Pico detectado:** {max_mes['Mes']} con {max_mes['Cantidad']} lesiones")
            else:
                st.info("No hay suficientes datos temporales")
        else:
            st.info("No hay datos de fechas")
    
    st.markdown("---")
    
    # FILA 2: TIPOS DE LESIÓN + DISTRIBUCIÓN POR CATEGORÍA
    col_graf3, col_graf4 = st.columns(2)
    
    with col_graf3:
        st.markdown("#### 🏥 Tipos de Lesión Más Frecuentes")
        
        # Buscar columna de tipo de lesión
        posibles_columnas_tipo = [col for col in df.columns if 'tipo' in col.lower() or 'diagnóstico' in col.lower()]
        
        if posibles_columnas_tipo:
            col_tipo = posibles_columnas_tipo[0]
            tipos_lesion = df_analisis[col_tipo].value_counts().head(5)
            
            if not tipos_lesion.empty:
                fig_tipos = px.bar(
                    x=tipos_lesion.index,
                    y=tipos_lesion.values,
                    color=tipos_lesion.values,
                    color_continuous_scale='Oranges',
                    labels={'x': 'Tipo de Lesión', 'y': 'Cantidad'}
                )
                
                fig_tipos.update_layout(
                    height=400,
                    showlegend=False,
                    coloraxis_showscale=False
                )
                
                st.plotly_chart(fig_tipos, use_container_width=True)
            else:
                st.info("No hay datos de tipos de lesión")
        else:
            st.warning("⚠️ Agrega columna 'Tipo de Lesión' en Google Sheets")
            st.info("""
            💡 **Sugerencia:** Crea una columna llamada:
            - `Tipo de Lesión` o
            - `Diagnóstico`
            
            Con valores como: Esguince, Desgarro, Fractura, Contractura, etc.
            """)
    
    with col_graf4:
        st.markdown("#### 🏈 Distribución por Categoría")
        
        if 'Categoría' in df_analisis.columns:
            categorias_dist = df_analisis['Categoría'].value_counts()
            
            if not categorias_dist.empty:
                fig_cat = px.pie(
                    values=categorias_dist.values,
                    names=categorias_dist.index,
                    color_discrete_sequence=px.colors.sequential.Blues_r,
                    hole=0.4
                )
                
                fig_cat.update_traces(
                    textposition='inside',
                    textinfo='percent+label'
                )
                
                fig_cat.update_layout(height=400)
                
                st.plotly_chart(fig_cat, use_container_width=True)
            else:
                st.info("No hay datos de categorías")
        else:
            st.info("No hay datos de categorías")
    
    st.markdown("---")
    
    # ============================================
    # SECCIÓN 4: ALERTAS Y RECOMENDACIONES
    # ============================================
    st.markdown("### 🚨 Alertas y Recomendaciones")
    
    col_alert1, col_alert2 = st.columns(2)
    
    with col_alert1:
        st.markdown("#### ⚠️ Zonas de Alto Riesgo")
        
        if posibles_columnas_parte and col_parte in df_analisis.columns:
            partes_criticas = df_analisis[col_parte].value_counts().head(3)
            
            for i, (parte, cantidad) in enumerate(partes_criticas.items(), 1):
                porcentaje = (cantidad / total_lesiones) * 100
                
                if porcentaje > 30:
                    nivel = "🔴 CRÍTICO"
                    color = "error"
                elif porcentaje > 20:
                    nivel = "🟠 ALTO"
                    color = "warning"
                else:
                    nivel = "🟡 MODERADO"
                    color = "info"
                
                st.markdown(f"""
                **{i}. {parte}**  
                - {cantidad} casos ({porcentaje:.1f}%)  
                - Nivel: {nivel}
                """)
                
                if porcentaje > 25:
                    st.error(f"💡 **Recomendación:** Implementar trabajo preventivo específico para {parte}")
        else:
            st.info("Agrega datos de partes del cuerpo para ver alertas")
    
    with col_alert2:
        st.markdown("#### 📊 Tendencias Temporales")
        
        if 'Fecha_parsed' in df_analisis.columns and len(df_analisis) > 5:
            # Comparar último mes vs promedio
            df_analisis['Mes_Num'] = df_analisis['Fecha_parsed'].dt.to_period('M')
            lesiones_por_mes_num = df_analisis.groupby('Mes_Num').size()
            
            if len(lesiones_por_mes_num) >= 2:
                ultimo_mes = lesiones_por_mes_num.iloc[-1]
                promedio_historico = lesiones_por_mes_num.iloc[:-1].mean()
                
                diferencia_porcentual = ((ultimo_mes - promedio_historico) / promedio_historico) * 100
                
                st.metric(
                    "📈 Último Mes vs Promedio",
                    f"{ultimo_mes} lesiones",
                    delta=f"{diferencia_porcentual:+.1f}%"
                )
                
                if diferencia_porcentual > 50:
                    st.error(f"🚨 **ALERTA:** Incremento significativo del {diferencia_porcentual:.0f}% en lesiones")
                    st.warning("💡 **Acción requerida:** Revisar cargas de entrenamiento y protocolos de prevención")
                elif diferencia_porcentual > 20:
                    st.warning(f"⚠️ Aumento moderado del {diferencia_porcentual:.0f}% en lesiones")
                elif diferencia_porcentual < -20:
                    st.success(f"✅ Reducción del {abs(diferencia_porcentual):.0f}% en lesiones")
                else:
                    st.info("📊 Nivel de lesiones estable")
            else:
                st.info("Necesitas más datos históricos para análisis de tendencias")
        else:
            st.info("Agrega más datos para análisis de tendencias")
    
    st.markdown("---")
    
    # ============================================
    # SECCIÓN 5: TABLA DETALLADA
    # ============================================
    st.markdown("### 📋 Detalle de Lesiones")
    
    with st.expander("📊 Ver tabla completa de datos", expanded=False):
        st.dataframe(df_analisis, use_container_width=True, height=400)
        
        # Botón de descarga
        csv = df_analisis.to_csv(index=False)
        st.download_button(
            label="📥 Descargar análisis completo (CSV)",
            data=csv,
            file_name=f"analisis_tendencias_lesiones_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )


# ============================================
# MODIFICAR LA FUNCIÓN MAIN PARA INCLUIR EL NUEVO DASHBOARD
# ============================================

def main_streamlit():
    """
    INTERFAZ PRINCIPAL CON DASHBOARD DE TENDENCIAS
    """
    # Header
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 2rem; border-radius: 15px; margin-bottom: 2rem;">
        <h1 style="color: white; text-align: center; margin: 0;">🏥 Área Médica CAR</h1>
        <p style="color: rgba(255,255,255,0.9); text-align: center; margin: 0.5rem 0 0 0;">Sistema Integral de Gestión Médica</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Cargar datos
    with st.spinner("🔄 Cargando datos desde Google Sheets..."):
        try:
            df = create_dataframe_from_sheet()
            
            if df is not None and not df.empty:
                # ============================================
                # TABS PARA ORGANIZAR EL DASHBOARD
                # ============================================
                tab1, tab2 = st.tabs(["📊 Dashboard General", "🔬 Análisis de Tendencias"])
                
                with tab1:
                    # CÓDIGO EXISTENTE DEL DASHBOARD GENERAL
                    # (Todo el código que ya tenías)
                    
                    col_categoria = 'Categoría'
                    col_severidad = 'Severidad de la Lesión'
                    
                    st.markdown("### 🔍 Filtros")
                    col_filtro1, col_filtro2 = st.columns(2)
                    
                    with col_filtro1:
                        if col_categoria in df.columns:
                            categorias_disponibles = ['Todas'] + sorted(df[col_categoria].dropna().unique().tolist())
                            categoria_seleccionada = st.selectbox(
                                "🏈 Seleccionar División",
                                categorias_disponibles,
                                key="area_medica_filtro_categoria"
                            )
                        else:
                            categoria_seleccionada = 'Todas'
                    
                    with col_filtro2:
                        if col_severidad in df.columns:
                            gravedades_disponibles = ['Todas'] + sorted(df[col_severidad].dropna().unique().tolist())
                            gravedad_seleccionada = st.selectbox(
                                "⚠️ Seleccionar Gravedad",
                                gravedades_disponibles,
                                key="area_medica_filtro_gravedad"
                            )
                        else:
                            gravedad_seleccionada = 'Todas'
                    
                    df_filtrado = df.copy()
                    
                    if categoria_seleccionada != 'Todas' and col_categoria in df.columns:
                        df_filtrado = df_filtrado[df_filtrado[col_categoria] == categoria_seleccionada]
                    
                    if gravedad_seleccionada != 'Todas' and col_severidad in df.columns:
                        df_filtrado = df_filtrado[df_filtrado[col_severidad] == gravedad_seleccionada]
                    
                    info_filtros = []
                    if categoria_seleccionada != 'Todas':
                        info_filtros.append(f"**División:** {categoria_seleccionada}")
                    if gravedad_seleccionada != 'Todas':
                        info_filtros.append(f"**Gravedad:** {gravedad_seleccionada}")
                    
                    if info_filtros:
                        st.info(f"🔍 **Filtros activos:** {' | '.join(info_filtros)}")
                    
                    st.markdown("---")
                    
                    st.markdown("### 📊 Análisis de Lesiones")
                    col_grafico1, col_grafico2 = st.columns(2)
                    
                    with col_grafico1:
                        st.markdown("#### 📊 Lesiones por División")
                        if col_categoria in df_filtrado.columns and not df_filtrado.empty:
                            categorias_counts = df_filtrado[col_categoria].value_counts()
                            
                            fig_bar = px.bar(
                                x=categorias_counts.index,
                                y=categorias_counts.values,
                                color_discrete_sequence=['#1e40af', '#2563eb', '#3b82f6', '#60a5fa']
                            )
                            
                            fig_bar.update_layout(
                                showlegend=False,
                                xaxis_title="División",
                                yaxis_title="Cantidad",
                                height=400
                            )
                            
                            st.plotly_chart(fig_bar, use_container_width=True)
                        else:
                            st.info("No hay datos para mostrar")
                    
                    with col_grafico2:
                        st.markdown("#### 🎯 Jugadores por Gravedad")
                        if col_severidad in df_filtrado.columns and not df_filtrado.empty:
                            df_severidad = df_filtrado[df_filtrado[col_severidad].notna() & (df_filtrado[col_severidad] != '')]
                            
                            if not df_severidad.empty:
                                severidad_counts = df_severidad[col_severidad].value_counts()
                                
                                fig_pie = px.pie(
                                    values=severidad_counts.values,
                                    names=severidad_counts.index,
                                    color_discrete_sequence=['#22c55e', '#eab308', '#ef4444', '#dc2626'],
                                    hole=0.3
                                )
                                
                                fig_pie.update_traces(
                                    textposition='inside',
                                    textinfo='percent+label'
                                )
                                
                                fig_pie.update_layout(
                                    height=400,
                                    showlegend=True,
                                    legend=dict(
                                        orientation="v",
                                        yanchor="middle",
                                        y=0.5,
                                        xanchor="left",
                                        x=1.02
                                    )
                                )
                                
                                st.plotly_chart(fig_pie, use_container_width=True)
                            else:
                                if categoria_seleccionada != 'Todas':
                                    st.warning(f"⚠️ No hay datos de gravedad para **{categoria_seleccionada}**")
                                else:
                                    st.warning("⚠️ No hay datos de gravedad disponibles")
                        else:
                            st.info("No hay datos para mostrar")
                    
                    st.markdown("---")
                    
                    st.markdown("### 👥 Lesionados")
                    
                    if not df_filtrado.empty:
                        st.success(f"✅ **{len(df_filtrado)} lesionado(s) encontrado(s)**")
                        
                        col_met1, col_met2, col_met3, col_met4 = st.columns(4)
                        with col_met1:
                            st.metric("📋 Total Lesiones", len(df_filtrado))
                        with col_met2:
                            if col_severidad in df_filtrado.columns:
                                leves = len(df_filtrado[df_filtrado[col_severidad].str.contains('Leve', case=False, na=False)])
                                st.metric("🟢 Leves", leves)
                            else:
                                st.metric("🟢 Leves", "N/A")
                        with col_met3:
                            if col_severidad in df_filtrado.columns:
                                moderadas = len(df_filtrado[df_filtrado[col_severidad].str.contains('Moderada', case=False, na=False)])
                                st.metric("🟡 Moderadas", moderadas)
                            else:
                                st.metric("🟡 Moderadas", "N/A")
                        with col_met4:
                            if col_severidad in df_filtrado.columns:
                                graves = len(df_filtrado[df_filtrado[col_severidad].str.contains('Grave', case=False, na=False)])
                                st.metric("🔴 Graves", graves)
                            else:
                                st.metric("🔴 Graves", "N/A")
                        
                        st.dataframe(df_filtrado, use_container_width=True, height=400)
                        
                        csv = df_filtrado.to_csv(index=False)
                        st.download_button(
                            label="📥 Descargar datos filtrados",
                            data=csv,
                            file_name=f"lesiones_filtradas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.warning("⚠️ No se encontraron registros con los filtros seleccionados")
                
                # ============================================
                # TAB 2: NUEVO DASHBOARD DE TENDENCIAS
                # ============================================
                with tab2:
                    mostrar_dashboard_tendencias_lesiones(df)
                
            else:
                st.error("❌ No se pudieron cargar los datos")
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")



# Ejecutar solo si es llamado directamente
if __name__ == "__main__":
    main_streamlit()