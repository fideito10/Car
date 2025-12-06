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

def cargar_hoja(sheet_id: str, nombre_hoja: str, rutas_credenciales=None) -> pd.DataFrame:
    """
    Carga una hoja de Google Sheets usando el sheet_id y el nombre de la pestaña.
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
            return pd.DataFrame()
        
        # Crear credenciales desde la información obtenida
        credenciales = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
        
        gc = gspread.authorize(credenciales)
        sh = gc.open_by_key(sheet_id)
        worksheet = sh.worksheet(nombre_hoja)
        all_data = worksheet.get_all_values()
        
        if not all_data:
            st.warning("⚠️ La hoja está vacía")
            return pd.DataFrame()
            
        columns = all_data[0]
        data_rows = all_data[1:]
        df = pd.DataFrame(data_rows, columns=columns)
        return df

    except gspread.exceptions.SpreadsheetNotFound:
        st.error("❌ Google Sheet no encontrado. Verifica el ID y permisos.")
        return pd.DataFrame()
        
    except gspread.exceptions.APIError as e:
        st.error(f"❌ Error de API: {e}. Verifica que hayas compartido el sheet con la cuenta de servicio.")
        return pd.DataFrame()
        
    except Exception as e:
        st.error(f"❌ Error al cargar la hoja: {e}")
        return pd.DataFrame()

def resaltar_valores(s):
    # Reemplaza coma por punto y convierte a float
    s_float = pd.to_numeric(s.astype(str).str.replace(',', '.'), errors='coerce')
    is_high = s_float > s_float.quantile(0.75)
    is_low = s_float < s_float.quantile(0.25)
    return ['background-color: #b6fcd5' if h else 'background-color: #ffb6b6' if l else '' for h, l in zip(is_high, is_low)]

def mostrar_tabla_estilizada(df, valor_col, test_col, subtest_col):
    """
    Muestra una tabla con código de colores según rendimiento vs promedio
    """
    if df.empty:
        st.warning("⚠️ No hay datos para mostrar con los filtros seleccionados")
        return
    
    # Obtener unidad del dataframe
    unidad = df['unidad'].iloc[0] if 'unidad' in df.columns else ""
    
    # Crear columna con valor + unidad
    df_display = df.copy()
    
    # 👉 CONVERSIÓN CORRECTA: Convertir valores a numérico primero
    df_display[valor_col] = pd.to_numeric(df_display[valor_col], errors='coerce')
    
    df_display['Valor Completo'] = df_display[valor_col].apply(
        lambda x: f"{x:.10g} {unidad}" if pd.notna(x) else ""
    )
    
    # Seleccionar y renombrar columnas
    columnas_mostrar = ['Nombre y Apellido', 'Posición del jugador', 'Categoría', 'Valor Completo', valor_col]
    df_tabla = df_display[columnas_mostrar].copy()
    df_tabla.columns = ['Nombre', 'Posición', 'Categoría', 'Resultado', 'valor_numerico']
    
    # Resetear índice para evitar problemas
    df_tabla = df_tabla.reset_index(drop=True)
    
    # 👉 ASEGURAR TIPO NUMÉRICO antes de calcular estadísticas
    df_tabla['valor_numerico'] = pd.to_numeric(df_tabla['valor_numerico'], errors='coerce')
    
    # Calcular estadísticas para clasificación
    promedio = df_tabla['valor_numerico'].mean()
    desviacion = df_tabla['valor_numerico'].std()
    
    # 👉 VALIDACIÓN: Verificar que haya desviación estándar válida
    if pd.isna(desviacion) or desviacion == 0:
        st.warning("⚠️ Datos insuficientes para análisis estadístico")
        df_mostrar = df_tabla.drop('valor_numerico', axis=1)
        st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
        return
    
    # Eliminar columna ANTES de aplicar estilos
    df_mostrar = df_tabla.drop('valor_numerico', axis=1).copy()
    
    # Función para aplicar colores según rendimiento
    def aplicar_colores_rendimiento(row):
        styles = []
        # Obtener el valor numérico usando el índice de la fila
        valor = df_tabla.loc[row.name, 'valor_numerico']
        
        # 👉 VALIDAR QUE EL VALOR NO SEA NaN
        if pd.isna(valor):
            # Color gris para valores sin datos
            for col_name in df_mostrar.columns:
                styles.append('background-color: #E0E0E0; color: #757575; padding: 12px;')
            return styles
        
        # Clasificar en 3 categorías
        if valor > promedio + (0.5 * desviacion):
            bg_color = '#C8E6C9'  # Verde
            text_color = '#1B5E20'
        elif valor < promedio - (0.5 * desviacion):
            bg_color = '#FFCDD2'  # Rojo
            text_color = '#B71C1C'
        else:
            bg_color = '#FFF9C4'  # Amarillo
            text_color = '#F57F17'
        
        # Aplicar el mismo color a todas las columnas
        for col_name in df_mostrar.columns:
            styles.append(f'background-color: {bg_color}; color: {text_color}; font-weight: bold; padding: 12px;')
        
        return styles
    
    # Aplicar estilos al dataframe sin la columna valor_numerico
    styled_df = (
        df_mostrar.style
        .apply(aplicar_colores_rendimiento, axis=1)
        .set_properties(**{
            'text-align': 'center',
            'font-family': 'Montserrat, Arial',
            'font-size': '1em',
            'border-radius': '8px',
            'border': '1px solid #e1e1e1'
        })
        .set_table_styles([
            {'selector': 'th', 'props': [
                ('font-size', '1.1em'), 
                ('text-align', 'center'), 
                ('background-color', '#006B8F'), 
                ('color', 'white'),
                ('font-weight', 'bold'),
                ('padding', '15px')
            ]},
            {'selector': 'td', 'props': [
                ('text-align', 'center'), 
                ('font-family', 'Montserrat, Arial'), 
                ('font-size', '1em')
            ]},
            {'selector': 'tr:hover', 'props': [
                ('opacity', '0.9'),
                ('transform', 'scale(1.01)')
            ]},
            {'selector': 'table', 'props': [
                ('border-radius', '8px'), 
                ('border', '2px solid #006B8F'), 
                ('background-color', '#fff'),
                ('box-shadow', '0 4px 8px rgba(0, 0, 0, 0.1)')
            ]}
        ])
    )

    st.markdown("### 📋 Datos Filtrados y Clasificados")
    
    # Leyenda de colores
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("🟢 **Verde**: Por encima del promedio")
    with col2:
        st.markdown("🟡 **Amarillo**: En el promedio")
    with col3:
        st.markdown("🔴 **Rojo**: Por debajo del promedio")
    
    st.caption(f"📊 Promedio: {promedio:.2f} {unidad} | Desv. Est.: {desviacion:.2f} {unidad}")
    
    st.dataframe(styled_df, use_container_width=True, hide_index=True, height=600)

def mostrar_grafico_top_bottom(df_filtrado, jugador_col, valor_col):
    """
    Crea visualización de alto impacto mostrando TOP 3 y BOTTOM 3 jugadores en contenedores separados
    """
    if df_filtrado.empty or len(df_filtrado) < 3:
        st.warning("⚠️ Se necesitan al menos 3 registros para mostrar el gráfico comparativo")
        return
    
    # Calcular promedio por jugador
    df_promedio = df_filtrado.groupby(jugador_col)[valor_col].mean().reset_index()
    df_promedio = df_promedio.sort_values(valor_col, ascending=False)
    
    # Obtener TOP 3 y BOTTOM 3
    top_3 = df_promedio.head(3).copy()
    bottom_3 = df_promedio.tail(3).copy()
    
    # Obtener nombre del test y unidad
    nombre_test = df_filtrado['Test'].iloc[0] if 'Test' in df_filtrado.columns else "Test"
    unidad = df_filtrado['unidad'].iloc[0] if 'unidad' in df_filtrado.columns else ""
    
    st.markdown(f"## Resultado de {nombre_test}")
    
    # Crear dos columnas principales
    col_top, col_bottom = st.columns(2)
    
    # ============= CONTENEDOR TOP 3 =============
    with col_top:
        st.markdown(f"""
            <div style='background: linear-gradient(135deg, #006B8F 0%, #004A6B 100%); 
                        padding: 20px; 
                        border-radius: 15px; 
                        box-shadow: 0 8px 16px rgba(0, 74, 107, 0.5);
                        margin-bottom: 20px;'>
                <h2 style='color: white; text-align: center; margin: 0;'>
                    🏆 LÍDERES DE RENDIMIENTO - {nombre_test.upper()}
                </h2>
            </div>
        """, unsafe_allow_html=True)
        
        for idx, (_, row) in enumerate(top_3.iterrows(), 1):
            medalla = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉"
            
            st.markdown(f"""
                <div style='background: linear-gradient(135deg, #B8E6D5 0%, #A2D5C6 100%);
                            padding: 20px;
                            border-radius: 12px;
                            margin: 10px 0;
                            border-left: 5px solid #006B8F;
                            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div style='flex: 1;'>
                            <h3 style='color: #004A6B; margin: 0 0 5px 0; font-size: 1.4em;'>
                                {medalla} {row[jugador_col]}
                            </h3>
                            <p style='color: #2C3E50; margin: 0; font-size: 1.1em;'>
                                📊 <strong>{nombre_test}</strong>
                            </p>
                        </div>
                        <div style='text-align: right;'>
                            <h2 style='color: #006B8F; margin: 0; font-size: 2.5em; font-weight: bold;'>
                                {row[valor_col]:.10g} <span style='font-size: 0.6em;'>{unidad}</span>
                            </h2>
                            <p style='color: #005A75; margin: 0; font-size: 0.9em;'>
                                ⚡ Excelente
                            </p>
                        </div>
                    </div>    
                </div>       
            """, unsafe_allow_html=True)
    
    # ============= CONTENEDOR BOTTOM 3 =============
    with col_bottom:
        st.markdown(f"""
            <div style='background: linear-gradient(135deg, #C0392B 0%, #922B21 100%); 
                        padding: 20px; 
                        border-radius: 15px; 
                        box-shadow: 0 8px 16px rgba(146, 43, 33, 0.5);
                        margin-bottom: 20px;'>
                <h2 style='color: white; text-align: center; margin: 0;'>
                    ⚠️ ZONA DE ALERTA - {nombre_test.upper()}
                </h2>
            </div>
        """, unsafe_allow_html=True)
        
        for idx, (_, row) in enumerate(bottom_3.iloc[::-1].iterrows(), 1):
            emoji_alerta = "🔴" if idx == 1 else "🟠" if idx == 2 else "🟡"
            
            st.markdown(f"""
                <div style='background: linear-gradient(135deg, #F5B7B1 0%, #E8AAAA 100%);
                            padding: 20px;
                            border-radius: 12px;
                            margin: 10px 0;
                            border-left: 5px solid #C0392B;
                            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div style='flex: 1;'>
                            <h3 style='color: #922B21; margin: 0 0 5px 0; font-size: 1.4em;'>
                                {emoji_alerta} {row[jugador_col]}
                            </h3>
                            <p style='color: #2C3E50; margin: 0; font-size: 1.1em;'>
                                📊 <strong>{nombre_test}</strong>
                            </p>
                        </div>
                        <div style='text-align: right;'>
                            <h2 style='color: #C0392B; margin: 0; font-size: 2.5em; font-weight: bold;'>
                                {row[valor_col]:.10g} <span style='font-size: 0.6em;'>{unidad}</span>
                            </h2>
                            <p style='color: #A93226; margin: 0; font-size: 0.9em;'>
                                💪 Mejorable
                            </p>
                        </div>
                    </div>    
                </div>        
            """, unsafe_allow_html=True)


def physical_area():
    # Header visual mejorado
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
    
    sheet_id = "180ikmYPmc1nxw5UZYFq9lDa0lGfLn_L-7Yb8CmwJAPM"
    nombre_hoja = "Base Test"
    
    # Cargar datos con indicador de progreso
    with st.spinner("📊 Cargando datos desde Google Sheets..."):
        df = cargar_hoja(sheet_id, nombre_hoja)
    
    if df.empty:
        st.error("❌ No se pudo cargar la hoja 'Base Test'.")
        st.info("🔧 Verifica que las credenciales estén configuradas correctamente")
        return

    categoria_col = "Categoría"
    jugador_col = "Nombre y Apellido"
    test_col = "Test"
    subtest_col = "Subtest"
    valor_col = "valor"
    fecha_col = "Marca temporal"
    posicion_col = "Posición del jugador"

    st.markdown("### 🔎 Filtros Interactivos")
    
    # Definir grupos de posiciones DE RUGBY 🏉
    FORWARDS = ["Pilar", "Hooker", "Segunda Línea", "Tercera Línea"]
    BACKS = ["Medio Scrum", "Apertura", "Centro", "Wing","Fullback"]
    
    filtros = {}

    # 1️⃣ FILTRO: Categoría
    categorias = sorted(df[categoria_col].dropna().unique())
    filtros["categoria"] = st.selectbox("📁 Selecciona la categoría", options=categorias)
    df_cat = df[df[categoria_col] == filtros["categoria"]]

    # 2️⃣ FILTRO: Test físico
    tests = sorted(df_cat[test_col].dropna().unique())
    filtros["test"] = st.selectbox("🏃 Selecciona el test físico", options=tests)
    df_test = df_cat[df_cat[test_col] == filtros["test"]]



    # 3️⃣ FILTRO: Grupo de posición (Forwards/Backs)
    col1, col2 = st.columns(2)
    
    with col1:
        grupo_posicion = st.radio(
            "⚡ Selecciona el grupo",
            options=["Todos", "Forwards", "Backs"],
            horizontal=True
        )
    
    # Filtrar según grupo seleccionado
    if grupo_posicion == "Forwards":
        df_grupo = df_test[df_test[posicion_col].isin(FORWARDS)]
    elif grupo_posicion == "Backs":
        df_grupo = df_test[df_test[posicion_col].isin(BACKS)]
    else:
        df_grupo = df_test

    # 4️⃣ FILTRO: Posición específica
    with col2:
        # Obtener posiciones que realmente existen en el dataframe filtrado
        posiciones_en_df = df_grupo[posicion_col].dropna().unique()
        
        # Filtrar solo las posiciones del grupo seleccionado que existen en los datos
        if grupo_posicion == "Forwards":
            posiciones = sorted([p for p in FORWARDS if p in posiciones_en_df])
        elif grupo_posicion == "Backs":
            posiciones = sorted([p for p in BACKS if p in posiciones_en_df])
        else:
            posiciones = sorted(posiciones_en_df)
        
        filtros["posicion"] = st.selectbox(
            "🎯 Selecciona la posición específica",
            options=["Todas"] + posiciones
        )
    
    # Aplicar filtro de posición
    if filtros["posicion"] != "Todas":
        df_pos = df_grupo[df_grupo[posicion_col] == filtros["posicion"]]
    else:
        df_pos = df_grupo

    # 5️⃣ FILTRO: Jugador
    jugadores = sorted(df_pos[jugador_col].dropna().unique())
    
    # Mostrar cantidad de jugadores disponibles
    st.caption(f"🔍 {len(jugadores)} jugadores disponibles en esta selección")
    
    filtros["jugador"] = st.multiselect(
        "👤 Selecciona jugador/es",
        options=jugadores,
        default=[],
        help="Puedes seleccionar múltiples jugadores para comparar"
    )

    # Aplicar filtro de jugador solo si se seleccionó alguno
    if filtros["jugador"]:
        df_jug = df_pos[df_pos[jugador_col].isin(filtros["jugador"])]
    else:
        df_jug = df_pos

    # 6️⃣ FILTRO: Subtest
    subtests = sorted(df_jug[subtest_col].dropna().unique())
    if len(subtests) > 1:
        filtros["subtest"] = st.selectbox("⚙️ Selecciona el subtest", options=["Todos"] + subtests)
        if filtros["subtest"] != "Todos":
            df_filtrado = df_jug[df_jug[subtest_col] == filtros["subtest"]]
        else:
            df_filtrado = df_jug
    else:
        df_filtrado = df_jug

      # Convertir valores
    df_filtrado[valor_col] = df_filtrado[valor_col].astype(str).str.replace(',', '.')
    df_filtrado[valor_col] = pd.to_numeric(df_filtrado[valor_col], errors='coerce')

    # Espacio visual entre filtros y resultados
    st.markdown("<br><br>", unsafe_allow_html=True)
    mostrar_grafico_top_bottom(df_filtrado, jugador_col, valor_col)

    st.markdown("---")
    
    
    mostrar_tabla_estilizada(df_filtrado, valor_col, test_col, subtest_col)
