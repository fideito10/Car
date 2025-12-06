import streamlit as st
import pandas as pd
import os
import sys
import re
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 👇 AGREGAR ESTAS IMPORTACIONES AL INICIO
import json

# Importaciones de otros módulos
try:
    from .areamedica import read_google_sheet_with_headers, create_dataframe_from_sheet
except ImportError:
    read_google_sheet_with_headers = None
    create_dataframe_from_sheet = None

try:
    from .areanutricion import read_new_google_sheet_to_df, filtrar_ultimo_registro_por_jugador
except ImportError:
    read_new_google_sheet_to_df = None
    filtrar_ultimo_registro_por_jugador = None

try:
    from .areafisica import cargar_hoja
except ImportError:
    cargar_hoja = None

# 👇 AGREGAR ESTA FUNCIÓN DE VALIDACIÓN
def validar_credenciales():
    """Valida que existan las credenciales antes de cargar datos"""
    possible_paths = [
        "credentials/service-account-key.json",
        "../credentials/service-account-key.json",
        "credentials/service_account.json",
        "../credentials/service_account.json"
    ]
    
    for cred_path in possible_paths:
        if os.path.exists(cred_path):
            return True  # 👈 Solo retornar True, sin mostrar mensaje
    return False

# ...existing code...

def obtener_df_medica():
    """Obtiene el DataFrame del área médica desde Google Sheets"""
    try:
        if not read_google_sheet_with_headers:
            st.warning("⚠️ Módulo areamedica no disponible")
            return pd.DataFrame()
        
        # 👇 AGREGAR VALIDACIÓN
        if not validar_credenciales():
            return pd.DataFrame()
            
        result = read_google_sheet_with_headers(
            sheet_id="1zGyW-M_VV7iyDKVB1TTd0EEP3QBjdoiBmSJN2tK-H7w"
        )
        
        if result and isinstance(result, dict) and result.get('success'):
            df_medica = pd.DataFrame(result['data'])
            if not df_medica.empty:
                df_medica['origen_modulo'] = 'medica'
                return df_medica
        
        return pd.DataFrame()
        
    except Exception as e:
        st.error(f"❌ Error en área médica: {e}")
        return pd.DataFrame()



    
    

def obtener_df_nutricion():
    """Obtiene el DataFrame del área de nutrición desde Google Sheets"""
    try:
        if not read_new_google_sheet_to_df:
            return pd.DataFrame()
        
        df_nutricion = read_new_google_sheet_to_df(
            sheet_id='12SqV7eAYpCwePD-TA1R1XOou-nGO3R6QUSHUnxa8tAI',
            target_gid=382913329
        )
        
        if df_nutricion is not None and not df_nutricion.empty:
            if filtrar_ultimo_registro_por_jugador:
                df_nutricion = filtrar_ultimo_registro_por_jugador(df_nutricion)
            
            df_nutricion['origen_modulo'] = 'nutricion'
            return df_nutricion
        
        return pd.DataFrame()
        
    except Exception as e:
        return pd.DataFrame()

def obtener_df_fisica():
    """Obtiene el DataFrame del área física desde Google Sheets"""
    try:
        if not cargar_hoja:
            return pd.DataFrame()
        
        sheet_id = "180ikmYPmc1nxw5UZYFq9lDa0lGfLn_L-7Yb8CmwJAPM"
        nombre_hoja = "Base Test"
        
        df_fisica = cargar_hoja(sheet_id, nombre_hoja)
        
        if not df_fisica.empty:
            df_fisica['origen_modulo'] = 'fisica'
            return df_fisica
        
        return pd.DataFrame()
        
    except Exception as e:
        return pd.DataFrame()

@st.cache_data
def crear_dataframe_integrado():
    """Combina los DataFrames de los 3 módulos con cache"""
    
    # Obtener DataFrames de cada módulo
    df_medica = obtener_df_medica()
    df_nutricion = obtener_df_nutricion()
    df_fisica = obtener_df_fisica()
    
    # Verificar qué módulos tienen datos
    dataframes_validos = []
    
    if not df_medica.empty:
        dataframes_validos.append(df_medica)
    
    if not df_nutricion.empty:
        dataframes_validos.append(df_nutricion)
    
    if not df_fisica.empty:
        dataframes_validos.append(df_fisica)
    
    if not dataframes_validos:
        return pd.DataFrame()
    
    # Concatenación vertical
    try:
        df_combinado = pd.concat(dataframes_validos, ignore_index=True, sort=False)
        return df_combinado
    except Exception as e:
        return pd.DataFrame()

def obtener_categorias_disponibles(df_combinado):
    """Obtiene las categorías disponibles en el DataFrame"""
    col_categoria = buscar_columna_categoria(df_combinado)
    if col_categoria and col_categoria in df_combinado.columns:
        categorias = sorted(df_combinado[col_categoria].dropna().unique())
        return categorias, col_categoria
    else:
        # Si no hay categoría, crear una genérica
        return ['Todos los jugadores'], None

def buscar_columna_jugador(df):
    """Busca la columna que contiene los nombres de jugadores - ESPECÍFICA para CAR"""
    posibles_nombres = [
        'Nombre completo:',
        'Nombre',
        'Jugador',
        'Nombre y apellido',
        'Nombre completo',
        'Apellido y Nombre'
    ]
    
    for col in df.columns:
        if col in posibles_nombres:
            return col
    
    return None

def mostrar_foto_jugador():
    """Muestra una foto placeholder del jugador"""
    return """
    <div style="text-align: center; margin-bottom: 1rem;">
        <div style="
            width: 200px; 
            height: 200px; 
            border-radius: 15px; 
            border: 4px solid #1a365d;
            background: linear-gradient(135deg, #ebf8ff 0%, #bee3f8 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto;
            box-shadow: 0 8px 25px rgba(26, 54, 93, 0.15);
        ">
            <div style="font-size: 4rem; color: #1a365d;">👤</div>
        </div>
    </div>
    """
    

def cargar_estilos_profesionales():
    """Cargar estilos CSS profesionales para el club de rugby"""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    :root {
        --rugby-primary: #1a365d;
        --rugby-secondary: #2d5a87;
        --rugby-accent: #3182ce;
        --rugby-light: #ebf8ff;
        --rugby-success: #38a169;
        --rugby-warning: #ed8936;
        --rugby-danger: #e53e3e;
        --rugby-neutral: #718096;
    }
    
    .main-panel {
        background: linear-gradient(135deg, var(--rugby-light) 0%, #ffffff 100%);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 10px 30px rgba(26, 54, 93, 0.1);
        margin-bottom: 2rem;
    }
    
    .player-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 5px 20px rgba(0,0,0,0.08);
        border-left: 5px solid var(--rugby-primary);
        margin-bottom: 1rem;
    }
    
    .stat-card {
        background: linear-gradient(135deg, var(--rugby-primary) 0%, var(--rugby-secondary) 100%);
        color: white;
        padding: 1.2rem;
        border-radius: 12px;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 4px 15px rgba(26, 54, 93, 0.2);
    }
    
    .stat-card h3 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
        color: white;
    }
    
    .stat-card p {
        margin: 0.3rem 0 0 0;
        font-size: 0.9rem;
        opacity: 0.9;
        color: white;
    }
    
    .module-tab {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        margin-top: 1rem;
    }
    
    .player-photo {
        border-radius: 15px;
        border: 4px solid var(--rugby-primary);
        box-shadow: 0 8px 25px rgba(26, 54, 93, 0.15);
        width: 100%;
        max-width: 250px;
    }
    
    .info-badge {
        background: var(--rugby-light);
        color: var(--rugby-primary);
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        margin: 0.2rem;
        display: inline-block;
    }
    
    .status-available {
        background: var(--rugby-success);
        color: white;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-weight: 600;
    }
    
    .status-injured {
        background: var(--rugby-danger);
        color: white;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-weight: 600;
    }
    
    .metric-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.8rem 0;
        border-bottom: 1px solid #e2e8f0;
    }
    
    .metric-label {
        font-weight: 500;
        color: var(--rugby-neutral);
    }
    
    .metric-value {
        font-weight: 700;
        color: var(--rugby-primary);
        font-size: 1.1rem;
    }
    
    .section-title {
        color: var(--rugby-primary);
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 1rem;
        border-bottom: 2px solid var(--rugby-accent);
        padding-bottom: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: var(--rugby-light);
        border-radius: 10px;
        color: var(--rugby-primary);
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--rugby-primary);
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

def buscar_columna_jugador(df):
    """Busca la columna que contiene los nombres de jugadores - ESPECÍFICA para CAR"""
    # Priorizar las columnas exactas del dataset CAR
    columnas_exactas = [
        'Nombre completo del jugador',  # Área médica
        'Nombre y Apellido',            # Área nutrición y principal
        'nombre',                       # Área física (si existe)
        'Jugador',                      # Backup
        'Nombre'                        # Backup
    ]
    
    # Buscar primero las columnas exactas
    for col in columnas_exactas:
        if col in df.columns:
            return col
    
    # Si no encuentra las exactas, buscar por patrones (backup)
    for col in df.columns:
        if any(x in col.lower() for x in ['nombre', 'jugador', 'player']):
            return col
    
    return None

def buscar_columna_categoria(df):
    """Busca la columna que contiene las categorías - ESPECÍFICA para CAR"""
    # Columna exacta del dataset CAR
    if 'Categoría' in df.columns:
        return 'Categoría'
    
    # Backups si no encuentra la exacta
    columnas_backup = [
        'categoria', 'division', 'plantel', 'equipo', 'category',
        'Division', 'Plantel', 'Equipo'
    ]
    
    for col in columnas_backup:
        if col in df.columns:
            return col
    
    # Búsqueda por patrones (último recurso)
    for col in df.columns:
        if any(x in col.lower() for x in ['categoria', 'division', 'plantel']):
            return col
    
    return None

def buscar_columna_dni(df):
    """Busca la columna que contiene el DNI - ESPECÍFICA para CAR"""
    # Columnas exactas del dataset CAR
    columnas_dni = [
        'Dni',                          # Área nutrición
        'Por Favor completa el Dni',    # Área médica
        'dni',                          # Minúscula
        'DNI',                          # Mayúscula
        'documento',                    # Backup
        'id'                           # Backup
    ]
    
    # Buscar primero las columnas exactas
    for col in columnas_dni:
        if col in df.columns:
            return col
    
    # Búsqueda por patrones
    for col in df.columns:
        if any(x in col.lower() for x in ['dni', 'documento', 'id']):
            return col
    
    return None

def obtener_jugadores_por_categoria(df_combinado, categoria_seleccionada, col_categoria):
    """Obtiene jugadores filtrados por categoría con DNI como identificador único"""
    col_jugador = buscar_columna_jugador(df_combinado)
    col_dni = buscar_columna_dni(df_combinado)
    
    if not col_jugador:
        return []
    
    # Filtrar por categoría
    if col_categoria and categoria_seleccionada != 'Todos los jugadores':
        df_filtrado = df_combinado[df_combinado[col_categoria] == categoria_seleccionada]
    else:
        df_filtrado = df_combinado
    
    # Crear lista de jugadores únicos por DNI
    jugadores_unicos = {}
    
    for _, fila in df_filtrado.iterrows():
        nombre = fila[col_jugador] if pd.notna(fila[col_jugador]) else None
        dni = fila[col_dni] if col_dni and pd.notna(fila[col_dni]) else None
        
        if nombre and dni:
            # Usar DNI como clave única
            clave_unica = str(dni)
            if clave_unica not in jugadores_unicos:
                # Formato: "Nombre y Apellido (DNI: 12345678)"
                jugadores_unicos[clave_unica] = f"{nombre} (DNI: {dni})"
    
    # Retornar lista ordenada de jugadores con formato nombre + DNI
    return sorted(jugadores_unicos.values())

def extraer_dni_de_seleccion(jugador_seleccionado):
    """Extrae el DNI del formato 'Nombre y Apellido (DNI: 12345678)'"""
    try:
        # Buscar el patrón "(DNI: número)"
        import re
        match = re.search(r'\(DNI: (\d+)\)', jugador_seleccionado)
        if match:
            return match.group(1)
    except:
        pass
    return None

def obtener_datos_jugador(df_combinado, jugador_seleccionado):
    """Obtiene todos los datos de un jugador específico usando DNI como identificador único"""
    col_dni = buscar_columna_dni(df_combinado)
    
    if not col_dni:
        # Si no hay DNI, usar el método anterior por nombre
        col_jugador = buscar_columna_jugador(df_combinado)
        if not col_jugador:
            return pd.DataFrame()
        datos_jugador = df_combinado[df_combinado[col_jugador] == jugador_seleccionado]
        return datos_jugador
    
    # Extraer DNI del formato seleccionado
    dni_jugador = extraer_dni_de_seleccion(jugador_seleccionado)
    
    if not dni_jugador:
        return pd.DataFrame()
    
    # Buscar por DNI (identificador único)
    datos_jugador = df_combinado[df_combinado[col_dni].astype(str) == str(dni_jugador)]
    return datos_jugador



def mostrar_ficha_personal_simple(datos_jugador):
    """Muestra la ficha personal del jugador usando solo componentes nativos de Streamlit"""
    if datos_jugador.empty:
        st.warning("No se encontraron datos del jugador")
        return
    
    # Obtener datos básicos usando las columnas exactas del CAR
    jugador_nombre = None
    dni = None
    categoria = None
    posicion = None
    peso = None
    altura = None
    
    # Buscar en todas las filas del jugador para obtener la información más completa
    for _, fila in datos_jugador.iterrows():
        # Nombre del jugador
        if pd.notna(fila.get('Nombre completo del jugador')):
            jugador_nombre = fila['Nombre completo del jugador']
        elif pd.notna(fila.get('Nombre y Apellido')):
            jugador_nombre = fila['Nombre y Apellido']
        
        # DNI
        if pd.notna(fila.get('Dni')):
            dni = fila['Dni']
        elif pd.notna(fila.get('Por Favor completa el Dni')):
            dni = fila['Por Favor completa el Dni']
        
        # Categoría
        if pd.notna(fila.get('Categoría')):
            categoria = fila['Categoría']
        
        # Posición
        if pd.notna(fila.get('Posición del jugador')):
            posicion = fila['Posición del jugador']
    
    # BUSCAR PESO Y ALTURA SOLO EN DATOS DE NUTRICIÓN (origen_modulo == 'nutricion')
    datos_nutricion = datos_jugador[datos_jugador['origen_modulo'] == 'nutricion']
    
    if not datos_nutricion.empty:
        # Ordenar por índice descendente para obtener el más reciente primero
        datos_nutricion_ordenados = datos_nutricion.sort_index(ascending=False)
        
        for _, fila in datos_nutricion_ordenados.iterrows():
            if peso is None and 'Peso (kg): [Número con decimales 88,5]' in datos_nutricion.columns:
                if pd.notna(fila['Peso (kg): [Número con decimales 88,5]']):
                    peso = fila['Peso (kg): [Número con decimales 88,5]']
            
            if altura is None and 'Talla (cm): [Número]' in datos_nutricion.columns:
                if pd.notna(fila['Talla (cm): [Número]']):
                    altura = fila['Talla (cm): [Número]']
            
            if peso is not None and altura is not None:
                break
    
    if not jugador_nombre:
        jugador_nombre = "Jugador sin nombre"
    
    # HEADER DEL PERFIL
    st.subheader("👤 PERFIL DEL JUGADOR")
    
    with st.container():
        col_avatar, col_info = st.columns([1, 3])
        
        with col_avatar:
            if "nahuel clausen" in jugador_nombre.lower().strip():
                try:
                    st.image(r"C:\Users\dell\Desktop\Car\Nahuel Clausen.jpg", width=120)
                except:
                    st.markdown("""
                    <div style="
                        width: 120px; 
                        height: 120px; 
                        border-radius: 50%; 
                        background: linear-gradient(135deg, #1a365d 0%, #2d5a87 100%);
                        color: white;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin: 0 auto;
                        font-size: 3rem;
                        font-weight: bold;
                        box-shadow: 0 8px 25px rgba(26, 54, 93, 0.3);
                    ">👤</div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="
                    width: 120px; 
                    height: 120px; 
                    border-radius: 50%; 
                    background: linear-gradient(135deg, #1a365d 0%, #2d5a87 100%);
                    color: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto;
                    font-size: 3rem;
                    font-weight: bold;
                    box-shadow: 0 8px 25px rgba(26, 54, 93, 0.3);
                ">👤</div>
                """, unsafe_allow_html=True)
            
            st.markdown("<div style='text-align: center; font-size: 0.9rem; margin-top: 0.5rem;'><strong>CLUB ARGENTINO</strong></div>", unsafe_allow_html=True)
            st.markdown("<div style='text-align: center; font-size: 0.9rem;'><strong>DE RUGBY</strong></div>", unsafe_allow_html=True)
        
        with col_info:
            st.markdown(f"""
            <div style="
                font-size: 3rem;
                font-weight: 900;
                color: #1a365d;
                margin-bottom: 1rem;
                text-transform: uppercase;
                letter-spacing: 2px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
                line-height: 1.1;
                text-align: center;
            ">{jugador_nombre}</div>
            """, unsafe_allow_html=True)
            
            # MÉTRICAS CON ESTILO PERSONALIZADO (SIN EMOJIS)
            info_col1, info_col2, info_col3 = st.columns(3)
            
            with info_col1:
                st.markdown(f"""
                <div style="text-align: center; padding: 1rem; background: #f7fafc; border-radius: 10px;">
                    <div style="font-size: 0.85rem; color: #718096; font-weight: 600; margin-bottom: 0.5rem;">DNI</div>
                    <div style="font-size: 1.8rem; color: #1a365d; font-weight: 800;">{dni if dni else "N/A"}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with info_col2:
                st.markdown(f"""
                <div style="text-align: center; padding: 1rem; background: #f7fafc; border-radius: 10px;">
                    <div style="font-size: 0.85rem; color: #718096; font-weight: 600; margin-bottom: 0.5rem;">CATEGORÍA</div>
                    <div style="font-size: 1.8rem; color: #1a365d; font-weight: 800;">{categoria if categoria else "N/A"}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with info_col3:
                st.markdown(f"""
                <div style="text-align: center; padding: 1rem; background: #f7fafc; border-radius: 10px;">
                    <div style="font-size: 0.85rem; color: #718096; font-weight: 600; margin-bottom: 0.5rem;">POSICIÓN</div>
                    <div style="font-size: 1.8rem; color: #1a365d; font-weight: 800;">{posicion if posicion else "N/A"}</div>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # SEGUNDA FILA - INFORMACIÓN FÍSICA (SIN EMOJIS)
    col_peso, col_altura, col_estado = st.columns(3)
    
    with col_peso:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: #f7fafc; border-radius: 10px;">
            <div style="font-size: 0.85rem; color: #718096; font-weight: 600; margin-bottom: 0.5rem;">PESO</div>
            <div style="font-size: 1.8rem; color: #1a365d; font-weight: 800;">{f"{peso} kg" if peso else "N/A"}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_altura:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: #f7fafc; border-radius: 10px;">
            <div style="font-size: 0.85rem; color: #718096; font-weight: 600; margin-bottom: 0.5rem;">ALTURA</div>
            <div style="font-size: 1.8rem; color: #1a365d; font-weight: 800;">{f"{altura} cm" if altura else "N/A"}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_estado:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: #f7fafc; border-radius: 10px;">
            <div style="font-size: 0.85rem; color: #718096; font-weight: 600; margin-bottom: 0.5rem;">ESTADO</div>
            <div style="font-size: 1.8rem; color: #38a169; font-weight: 800;">Activo</div>
        </div>
        """, unsafe_allow_html=True)


        
def mostrar_modulo_nutricion(datos_nutricionales):
    """Muestra información del módulo de nutrición"""
    if datos_nutricionales.empty:
        st.info("🥗 No hay datos nutricionales disponibles para este jugador")
        return
    
    st.markdown("### 🥗 Nutrición")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'Peso (kg): [Número con decimales 88,5]' in datos_nutricionales.columns:
            peso_actual = datos_nutricionales['Peso (kg): [Número con decimales 88,5]'].iloc[-1]
            if pd.notna(peso_actual):
                st.metric("⚖️ Peso Actual", f"{peso_actual} kg")
            else:
                st.metric("⚖️ Peso Actual", "N/A")
        else:
            st.metric("⚖️ Peso Actual", "N/A")
    
    with col2:
        if 'IMC' in datos_nutricionales.columns:
            imc = datos_nutricionales['IMC'].iloc[-1]
            if pd.notna(imc):
                st.metric("📊 IMC", f"{imc:.1f}")
            else:
                st.metric("📊 IMC", "N/A")
        else:
            st.metric("📊 IMC", "N/A")
    
    with col3:
        if '% grasa corporal' in datos_nutricionales.columns:
            grasa = datos_nutricionales['% grasa corporal'].iloc[-1]
            if pd.notna(grasa):
                st.metric("🧈 % Grasa", f"{grasa}%")
            else:
                st.metric("🧈 % Grasa", "N/A")
        else:
            st.metric("🧈 % Grasa", "N/A")
    
    # Evolución del peso si hay múltiples registros
    if len(datos_nutricionales) > 1 and 'Peso (kg): [Número con decimales 88,5]' in datos_nutricionales.columns:
        st.subheader("📈 Evolución del Peso")
        pesos = datos_nutricionales['Peso (kg): [Número con decimales 88,5]'].dropna()
        if len(pesos) > 1:
            fig = px.line(x=range(len(pesos)), y=pesos.values, 
                         title="Evolución del Peso Corporal",
                         labels={'x': 'Evaluación', 'y': 'Peso (kg)'})
            st.plotly_chart(fig, use_container_width=True)
    
    # Tabla detallada
    st.subheader("📋 Datos Nutricionales Completos")
    st.dataframe(datos_nutricionales.drop('origen_modulo', axis=1, errors='ignore'), use_container_width=True)

def mostrar_modulo_medico(datos_medicos):
    """Muestra información del módulo médico"""
    if datos_medicos.empty:
        st.info("🏥 No hay datos médicos disponibles para este jugador")
        return
    
    st.markdown('<p class="section-title">🏥 Área Médica</p>', unsafe_allow_html=True)
    
    # Estado actual
    col1, col2 = st.columns(2)
    
    with col1:
        if '¿Puede participar en entrenamientos?' in datos_medicos.columns:
            participacion = datos_medicos['¿Puede participar en entrenamientos?'].iloc[-1]
            if participacion == "Solo entrenamiento diferenciado":
                st.markdown('<div class="status-available">🟡 LIMITADO</div>', unsafe_allow_html=True)
            elif participacion == "No puede entrenar":
                st.markdown('<div class="status-injured">🔴 NO DISPONIBLE</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="status-available">🟢 DISPONIBLE</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-available">🟢 DISPONIBLE</div>', unsafe_allow_html=True)
    
    with col2:
        total_consultas = len(datos_medicos)
        st.metric("📊 Total Consultas", total_consultas)
    
    # Historial de lesiones
    if 'Tipo de lesión' in datos_medicos.columns:
        st.subheader("🩹 Historial de Lesiones")
        lesiones = datos_medicos['Tipo de lesión'].value_counts()
        if not lesiones.empty:
            fig = px.pie(values=lesiones.values, names=lesiones.index, 
                        title="Distribución por Tipo de Lesión",
                        color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig, use_container_width=True)
    
    # Severidad de lesiones
    if 'Severidad de la lesión' in datos_medicos.columns:
        st.subheader("⚡ Severidad de Lesiones")
        severidad = datos_medicos['Severidad de la lesión'].value_counts()
        if not severidad.empty:
            fig = px.bar(x=severidad.index, y=severidad.values,
                        title="Distribución por Severidad",
                        color_discrete_sequence=['#e53e3e', '#ed8936', '#38a169'])
            st.plotly_chart(fig, use_container_width=True)
    
    # Tabla detallada
    st.subheader("📋 Historial Médico Completo")
    st.dataframe(datos_medicos.drop('origen_modulo', axis=1, errors='ignore'), use_container_width=True)
    
def mostrar_modulo_fisico(datos_fisicos):
    """Muestra información del módulo físico con formato específico Test - Valor - Unidad"""
    if datos_fisicos.empty:
        st.info("💪 No hay datos físicos disponibles para este jugador")
        return
    
    st.markdown("### 💪 Preparación Física")
    
    # Verificar si existen las columnas necesarias
    tiene_test = 'Test' in datos_fisicos.columns
    tiene_subtest = 'Subtest' in datos_fisicos.columns
    tiene_valor = 'valor' in datos_fisicos.columns
    tiene_unidad = 'unidad' in datos_fisicos.columns
    
    if tiene_test and tiene_valor:
        st.subheader("🏋️‍♂️ Resultados de Tests Físicos")
        
        # Crear columnas para mostrar los tests
        tests_unicos = datos_fisicos['Test'].unique()
        
        for test in tests_unicos:
            # Filtrar datos por test
            datos_test = datos_fisicos[datos_fisicos['Test'] == test]
            
            # Si hay subtest, mostrar cada uno
            if tiene_subtest and not datos_test['Subtest'].isna().all():
                for _, fila in datos_test.iterrows():
                    subtest = fila['Subtest'] if pd.notna(fila['Subtest']) else test
                    valor = fila['valor'] if pd.notna(fila['valor']) else 'N/A'
                    unidad = fila['unidad'] if tiene_unidad and pd.notna(fila['unidad']) else ''
                    
                    # Formato específico solicitado
                    if unidad == '"':
                        resultado = f"**{subtest}:** {valor}\""
                    elif unidad == 'kg':
                        resultado = f"**{subtest}:** {valor} kg"
                    else:
                        resultado = f"**{subtest}:** {valor} {unidad}".strip()
                    
                    st.write(f"• {resultado}")
            else:
                # Si no hay subtest, mostrar solo el test principal
                valor = datos_test['valor'].iloc[0] if not datos_test['valor'].isna().any() else 'N/A'
                unidad = datos_test['unidad'].iloc[0] if tiene_unidad and not datos_test['unidad'].isna().any() else ''
                
                if unidad == '"':
                    resultado = f"**{test}:** {valor}\""
                elif unidad == 'kg':
                    resultado = f"**{test}:** {valor} kg"
                else:
                    resultado = f"**{test}:** {valor} {unidad}".strip()
                
                st.write(f"• {resultado}")
        
        # Métricas adicionales
        col1, col2 = st.columns(2)
        
        with col1:
            total_tests = len(tests_unicos)
            st.metric("📊 Tests Realizados", total_tests)
        
        with col2:
            total_evaluaciones = len(datos_fisicos)
            st.metric("📈 Total Evaluaciones", total_evaluaciones)
    
    else:
        # Fallback al método anterior si no están las columnas esperadas
        col1, col2 = st.columns(2)
        
        with col1:
            total_tests = len(datos_fisicos)
            st.metric("📊 Tests Realizados", total_tests)
        
        with col2:
            if 'fecha' in datos_fisicos.columns:
                ultima_fecha = datos_fisicos['fecha'].max()
                st.metric("📅 Último Test", ultima_fecha)
            else:
                st.metric("📅 Último Test", "N/A")
    
    # Tabla detallada completa
    st.subheader("📋 Datos Físicos Completos")
    st.dataframe(datos_fisicos.drop('origen_modulo', axis=1, errors='ignore'), use_container_width=True)

def crear_panel_areas_unificado(datos_jugador):
    """Crea el panel unificado de las 3 áreas con información específica"""
    
    # Separar datos por módulo
    datos_medicos = datos_jugador[datos_jugador['origen_modulo'] == 'medica']
    datos_nutricionales = datos_jugador[datos_jugador['origen_modulo'] == 'nutricion']
    datos_fisicos = datos_jugador[datos_jugador['origen_modulo'] == 'fisica']
    
    st.markdown("### 📊 ÁREAS DE SEGUIMIENTO")
    
    # Crear las 3 columnas principales
    col1, col2, col3 = st.columns(3)
    
    # COLUMNA 1: PREPARACIÓN FÍSICA
    with col1:
        st.markdown("#### 💪 PREPARACIÓN FÍSICA")
        
        if datos_fisicos.empty:
            st.write("• Sin datos físicos")
            st.write("• Sin tests realizados")
            st.write("• Sin evaluaciones")
        else:
            # Verificar si existen las columnas específicas de test
            tiene_test = 'Test' in datos_fisicos.columns
            tiene_subtest = 'Subtest' in datos_fisicos.columns
            tiene_valor = 'valor' in datos_fisicos.columns
            tiene_unidad = 'unidad' in datos_fisicos.columns
            
            if tiene_test and tiene_valor:
                # Mostrar últimos resultados por test
                tests_recientes = {}
                
                for _, fila in datos_fisicos.iterrows():
                    test = fila['Test']
                    subtest = fila['Subtest'] if tiene_subtest and pd.notna(fila['Subtest']) else test
                    valor = fila['valor'] if pd.notna(fila['valor']) else 'N/A'
                    unidad = fila['unidad'] if tiene_unidad and pd.notna(fila['unidad']) else ''
                    
                    # Usar subtest como clave para evitar duplicados
                    tests_recientes[subtest] = (valor, unidad)
                
                # Mostrar los tests (máximo 4 para que quepa en la columna)
                contador = 0
                for subtest, (valor, unidad) in tests_recientes.items():
                    if contador >= 4:  # Limitar a 4 tests para no sobrecargar
                        break
                    
                    if unidad == '"':
                        resultado = f"{valor}\""
                    elif unidad == 'kg':
                        resultado = f"{valor} kg"
                    else:
                        resultado = f"{valor} {unidad}".strip()
                    
                    st.write(f"• **{subtest}:** {resultado}")
                    contador += 1
                
                # Si hay más tests, mostrar cuántos más
                if len(tests_recientes) > 4:
                    st.write(f"• *+{len(tests_recientes) - 4} tests más...*")
                
            else:
                # Fallback al método anterior
                total_tests = len(datos_fisicos)
                st.write(f"• **Tests realizados:** {total_tests}")
                
                # Buscar distancia total si existe
                if 'Distancia total' in datos_fisicos.columns:
                    distancia = datos_fisicos['Distancia total'].iloc[-1]
                    st.write(f"• **Distancia total:** {distancia} m")
                else:
                    st.write("• **Distancia total:** —")
                
                # Última evaluación física
                if 'fecha' in datos_fisicos.columns:
                    ultima_fecha = datos_fisicos['fecha'].max()
                    st.write(f"• **Último test:** {ultima_fecha}")
                else:
                    st.write("• **Último test:** —")
    
    # COLUMNA 2: MEDICINA (sin cambios)
    with col2:
        st.markdown("#### 🏥 MEDICINA")
        
        if datos_medicos.empty:
            st.write("• **Estado actual:** Sin datos")
            st.write("• **Último control:** —")
            st.write("• **Lesión activa:** —")
        else:
            # Estado actual basado en participación en entrenamientos
            if '¿Puede participar en entrenamientos?' in datos_medicos.columns:
                participacion = datos_medicos['¿Puede participar en entrenamientos?'].iloc[-1]
                if participacion == "Solo entrenamiento diferenciado":
                    st.write("• **Estado actual:** 🟡 Limitado")
                elif participacion == "No puede entrenar":
                    st.write("• **Estado actual:** 🔴 No disponible")
                else:
                    st.write("• **Estado actual:** 🟢 Disponible")
            else:
                st.write("• **Estado actual:** 🟢 Disponible")
            
            # Último control médico
            if 'Marca temporal' in datos_medicos.columns:
                ultimo_control = datos_medicos['Marca temporal'].max()
                # Convertir timestamp a fecha legible
                try:
                    fecha_legible = pd.to_datetime(ultimo_control).strftime('%d/%m/%y')
                    st.write(f"• **Último control:** {fecha_legible}")
                except:
                    st.write(f"• **Último control:** {ultimo_control}")
            else:
                st.write("• **Último control:** —")
            
            # Lesión activa
            if 'Tipo de lesión' in datos_medicos.columns:
                lesion_reciente = datos_medicos['Tipo de lesión'].iloc[-1]
                if pd.notna(lesion_reciente) and lesion_reciente.strip():
                    st.write(f"• **Lesión activa:** {lesion_reciente}")
                else:
                    st.write("• **Lesión activa:** Ninguna")
            else:
                st.write("• **Lesión activa:** —")
    
    # COLUMNA 3: NUTRICIÓN (sin cambios)
    with col3:
        st.markdown("#### 🥗 NUTRICIÓN")
        
        if datos_nutricionales.empty:
            st.write("• **Peso actual:** — kg")
            st.write("• **% grasa corporal:** — %")
            st.write("• **IMC:** —")
        else:
            # Peso actual
            if 'Peso (kg): [Número con decimales 88,5]' in datos_nutricionales.columns:
                peso = datos_nutricionales['Peso (kg): [Número con decimales 88,5]'].iloc[-1]
                if pd.notna(peso):
                    st.write(f"• **Peso actual:** {peso} kg")
                else:
                    st.write("• **Peso actual:** — kg")
            else:
                st.write("• **Peso actual:** — kg")
            
            # Porcentaje de grasa corporal
            if '% grasa corporal' in datos_nutricionales.columns:
                grasa = datos_nutricionales['% grasa corporal'].iloc[-1]
                if pd.notna(grasa):
                    st.write(f"• **% grasa corporal:** {grasa}%")
                else:
                    st.write("• **% grasa corporal:** — %")
            else:
                st.write("• **% grasa corporal:** — %")
            
            # IMC
            if 'IMC' in datos_nutricionales.columns:
                imc = datos_nutricionales['IMC'].iloc[-1]
                if pd.notna(imc):
                    st.write(f"• **IMC:** {imc:.1f}")
                else:
                    st.write("• **IMC:** —")
            else:
                st.write("• **IMC:** —")
            
            # Última evaluación nutricional
            if 'fecha' in datos_nutricionales.columns:
                ultima_evaluacion = datos_nutricionales['fecha'].max()
                st.write(f"• **Última evaluación:** {ultima_evaluacion}")
            else:
                st.write("• **Última evaluación:** —")

def crear_panel_areas_unificado(datos_jugador):
    """Crea el panel unificado de las 3 áreas con información específica"""
    
    # Separar datos por módulo
    datos_medicos = datos_jugador[datos_jugador['origen_modulo'] == 'medica']
    datos_nutricionales = datos_jugador[datos_jugador['origen_modulo'] == 'nutricion']
    datos_fisicos = datos_jugador[datos_jugador['origen_modulo'] == 'fisica']
    
    st.markdown("### 📊 ÁREAS DE SEGUIMIENTO")
    
    # Crear las 3 columnas principales
    col1, col2, col3 = st.columns(3)
    
    # COLUMNA 1: PREPARACIÓN FÍSICA CON SOMBRA GRIS
    with col1:
        contenido_html = '<div style="padding: 1.5rem; background: #f7fafc; border-radius: 10px; min-height: 250px;">'
        contenido_html += '<h4 style="color: #1a365d; margin-top: 0;">💪 PREPARACIÓN FÍSICA</h4>'
        
        if datos_fisicos.empty:
            contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Press Banca:</strong> —</p>'
            contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Remo Acostado:</strong> —</p>'
            contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Vel Max:</strong> —</p>'
        else:
            tests_mapeo = {
                'Press Banca': ['Press Banca'],
                'Remo Acostado': ['Remo Acostado'], 
                'Vel Max': ['Vel Max']
            }
            
            tiene_test = 'Test' in datos_fisicos.columns
            tiene_subtest = 'Subtest' in datos_fisicos.columns
            tiene_valor = 'valor' in datos_fisicos.columns
            tiene_unidad = 'unidad' in datos_fisicos.columns
            
            if tiene_test and tiene_valor:
                for test_display, test_busqueda_lista in tests_mapeo.items():
                    resultado_encontrado = False
                    
                    for _, fila in datos_fisicos.iterrows():
                        test = str(fila['Test']).strip() if pd.notna(fila['Test']) else ''
                        subtest = str(fila['Subtest']).strip() if tiene_subtest and pd.notna(fila['Subtest']) else ''
                        
                        for test_buscar in test_busqueda_lista:
                            if (test == test_buscar or subtest == test_buscar):
                                valor = fila['valor'] if pd.notna(fila['valor']) else 'N/A'
                                unidad = str(fila['unidad']).strip() if tiene_unidad and pd.notna(fila['unidad']) else ''
                                
                                if unidad == '"':
                                    resultado = f"{valor}\""
                                elif unidad == 'kg':
                                    resultado = f"{valor} kg"
                                elif unidad == 'Km/h' or unidad == 'km/h':
                                    resultado = f"{valor} km/h"
                                elif unidad == 's':
                                    resultado = f"{valor} s"
                                else:
                                    resultado = f"{valor} {unidad}".strip() if unidad else str(valor)
                                
                                contenido_html += f'<p style="margin: 0.5rem 0;">• <strong>{test_display}:</strong> {resultado}</p>'
                                resultado_encontrado = True
                                break
                        
                        if resultado_encontrado:
                            break
                    
                    if not resultado_encontrado:
                        contenido_html += f'<p style="margin: 0.5rem 0;">• <strong>{test_display}:</strong> —</p>'
            else:
                contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Press Banca:</strong> —</p>'
                contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Remo Acostado:</strong> —</p>'
                contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Vel Max:</strong> —</p>'
        
        contenido_html += '</div>'
        st.markdown(contenido_html, unsafe_allow_html=True)
    
    # COLUMNA 2: MEDICINA CON SOMBRA GRIS
    with col2:
        contenido_html = '<div style="padding: 1.5rem; background: #f7fafc; border-radius: 10px; min-height: 250px;">'
        contenido_html += '<h4 style="color: #1a365d; margin-top: 0;">🏥 MEDICINA</h4>'
        
        if datos_medicos.empty:
            contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Estado actual:</strong> Sin datos</p>'
            contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Último control:</strong> —</p>'
            contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Lesión activa:</strong> —</p>'
        else:
            if '¿Puede participar en entrenamientos?' in datos_medicos.columns:
                participacion = datos_medicos['¿Puede participar en entrenamientos?'].iloc[-1]
                if participacion == "Solo entrenamiento diferenciado":
                    contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Estado actual:</strong> 🟡 Limitado</p>'
                elif participacion == "No puede entrenar":
                    contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Estado actual:</strong> 🔴 No disponible</p>'
                else:
                    contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Estado actual:</strong> 🟢 Disponible</p>'
            else:
                contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Estado actual:</strong> 🟢 Disponible</p>'
            
            if 'Marca temporal' in datos_medicos.columns:
                ultimo_control = datos_medicos['Marca temporal'].max()
                try:
                    fecha_legible = pd.to_datetime(ultimo_control).strftime('%d/%m/%y')
                    contenido_html += f'<p style="margin: 0.5rem 0;">• <strong>Último control:</strong> {fecha_legible}</p>'
                except:
                    contenido_html += f'<p style="margin: 0.5rem 0;">• <strong>Último control:</strong> {ultimo_control}</p>'
            else:
                contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Último control:</strong> —</p>'
            
            if 'Tipo de lesión' in datos_medicos.columns:
                lesion_reciente = datos_medicos['Tipo de lesión'].iloc[-1]
                if pd.notna(lesion_reciente) and lesion_reciente.strip():
                    contenido_html += f'<p style="margin: 0.5rem 0;">• <strong>Lesión activa:</strong> {lesion_reciente}</p>'
                else:
                    contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Lesión activa:</strong> Ninguna</p>'
            else:
                contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Lesión activa:</strong> —</p>'
        
        contenido_html += '</div>'
        st.markdown(contenido_html, unsafe_allow_html=True)
    
    # COLUMNA 3: NUTRICIÓN CON SOMBRA GRIS
    with col3:
        contenido_html = '<div style="padding: 1.5rem; background: #f7fafc; border-radius: 10px; min-height: 250px;">'
        contenido_html += '<h4 style="color: #1a365d; margin-top: 0;">🥗 NUTRICIÓN</h4>'
        
        if datos_nutricionales.empty:
            contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Peso actual:</strong> — kg</p>'
            contenido_html += '<p style="margin: 0.5rem 0;">• <strong>% grasa corporal:</strong> — %</p>'
            contenido_html += '<p style="margin: 0.5rem 0;">• <strong>IMC:</strong> —</p>'
        else:
            if 'Peso (kg): [Número con decimales 88,5]' in datos_nutricionales.columns:
                peso = datos_nutricionales['Peso (kg): [Número con decimales 88,5]'].iloc[-1]
                if pd.notna(peso):
                    contenido_html += f'<p style="margin: 0.5rem 0;">• <strong>Peso actual:</strong> {peso} kg</p>'
                else:
                    contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Peso actual:</strong> — kg</p>'
            else:
                contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Peso actual:</strong> — kg</p>'
            
            if '% grasa corporal' in datos_nutricionales.columns:
                grasa = datos_nutricionales['% grasa corporal'].iloc[-1]
                if pd.notna(grasa):
                    contenido_html += f'<p style="margin: 0.5rem 0;">• <strong>% grasa corporal:</strong> {grasa}%</p>'
                else:
                    contenido_html += '<p style="margin: 0.5rem 0;">• <strong>% grasa corporal:</strong> — %</p>'
            else:
                contenido_html += '<p style="margin: 0.5rem 0;">• <strong>% grasa corporal:</strong> — %</p>'
            
            if 'IMC' in datos_nutricionales.columns:
                imc = datos_nutricionales['IMC'].iloc[-1]
                if pd.notna(imc):
                    contenido_html += f'<p style="margin: 0.5rem 0;">• <strong>IMC:</strong> {imc:.1f}</p>'
                else:
                    contenido_html += '<p style="margin: 0.5rem 0;">• <strong>IMC:</strong> —</p>'
            else:
                contenido_html += '<p style="margin: 0.5rem 0;">• <strong>IMC:</strong> —</p>'
            
            if 'fecha' in datos_nutricionales.columns:
                ultima_evaluacion = datos_nutricionales['fecha'].max()
                contenido_html += f'<p style="margin: 0.5rem 0;">• <strong>Última evaluación:</strong> {ultima_evaluacion}</p>'
            else:
                contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Última evaluación:</strong> —</p>'
        
        contenido_html += '</div>'
        st.markdown(contenido_html, unsafe_allow_html=True)
        
                
                
# Modificar la función panel_profesional_jugador()
def panel_profesional_jugador():
    """Panel principal profesional para la gestión de jugadores"""
    
    # Header profesional con fondo azul
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #1a365d 0%, #2d5a87 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(26, 54, 93, 0.3);
        text-align: center;
    ">
        <div style="
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 2rem;
            flex-wrap: wrap;
        ">
            <div style="
                width: 80px;
                height: 80px;
                background: white;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 2.5rem;
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            ">
                🏉
            </div>
            <div>
                <h1 style="
                    color: white;
                    margin: 0;
                    font-size: 2.5rem;
                    font-weight: 800;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                ">CLUB ARGENTINO DE RUGBY</h1>
                <p style="
                    color: #bee3f8;
                    margin: 0.5rem 0 0 0;
                    font-size: 1.2rem;
                    font-weight: 500;
                ">Panel Profesional de Gestión de Jugadores</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Obtener datos integrados
    with st.spinner("🔄 Cargando datos integrados..."):
        df_combinado = crear_dataframe_integrado()
    
    if df_combinado.empty:
        st.error("❌ No se pudieron cargar datos de los módulos")
        st.info("💡 Verifica las credenciales de Google Sheets y la conexión a internet")
        return
    
    # Selectores superiores
    st.markdown("### 🎯 Selección de Jugador")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Selector de categoría
        categorias_disponibles, col_categoria = obtener_categorias_disponibles(df_combinado)
        categoria_seleccionada = st.selectbox(
            "📋 Seleccionar Categoría:",
            categorias_disponibles,
            key="categoria_selector"
        )
    
    with col2:
        # Selector de jugador
        jugadores_disponibles = obtener_jugadores_por_categoria(
            df_combinado, categoria_seleccionada, col_categoria
        )
        
        if not jugadores_disponibles:
            st.warning("No hay jugadores disponibles en esta categoría")
            return
        
        jugador_seleccionado = st.selectbox(
            "👤 Seleccionar Jugador:",
            jugadores_disponibles,
            key="jugador_selector"
        )
    
    if not jugador_seleccionado:
        st.info("👆 Selecciona un jugador para ver su ficha completa")
        return
    
    # Obtener datos del jugador seleccionado
    datos_jugador = obtener_datos_jugador(df_combinado, jugador_seleccionado)
    
    if datos_jugador.empty:
        st.error("❌ No se encontraron datos para el jugador seleccionado")
        return
    
    st.divider()
    
    # FICHA PERSONAL DEL JUGADOR (ANCHO COMPLETO)
    mostrar_ficha_personal_simple(datos_jugador)
    
    # SEPARADOR
    st.divider()
    
    # ÁREA DE SEGUIMIENTO (ANCHO COMPLETO DEBAJO DE LA FICHA)
    crear_panel_areas_unificado(datos_jugador)
    
    # Footer con información adicional
    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        registros_totales = len(datos_jugador)
        st.metric("📊 Registros Totales", registros_totales)
    
    with col2:
        modulos_activos = datos_jugador['origen_modulo'].nunique()
        st.metric("🏢 Módulos con Datos", modulos_activos)
    
    with col3:
        ultima_actualizacion = datetime.now().strftime("%d/%m/%Y %H:%M")
        st.metric("🔄 Última Actualización", ultima_actualizacion)
    
    with col4:
        # Botón de descarga
        csv_datos = datos_jugador.to_csv(index=False)
        st.download_button(
            label="📥 Descargar Datos",
            data=csv_datos,
            file_name=f"car_{jugador_seleccionado.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
        
        
def dashboard_360():
    """Función principal del módulo 360"""
    panel_profesional_jugador()