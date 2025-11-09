"""
Sistema Principal del Club Argentino de Rugby (CAR)
Centralizacion de Módulos: Área Médica, Nutrición y Física
Desarrollado con Streamlit
Fecha: Octubre 2025
"""

import streamlit as st
import json
import hashlib
from datetime import datetime, date, timedelta
import pandas as pd
from typing import Dict, List
import plotly.express as px
import plotly.graph_objects as go
import os
import sys
from google.oauth2 import service_account

# Crear la carpeta 'credentials' si no existe
if not os.path.exists('credentials'):
    os.makedirs('credentials')



# Agregar carpetas al path de Python
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'modules'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'sheets'))

# Importar módulo de Google Sheets
try:
    from src.sheets.sheets_interface import google_sheets_page
    google_sheets_available = True
except ImportError:
    google_sheets_page = None
    google_sheets_available = False

# Importar módulo de Área Física
try:
    from src.modules.areafisica import physical_area
    physical_area_available = True
except ImportError:
    physical_area = None
    physical_area_available = False

# Importar módulo de Formularios Médicos
try:
    # LAZY LOADING - no importar directamente
    area_medica_main = None
    formularios_medicos_available = True
    area_medica_enhanced_available = True
except ImportError:
    area_medica_main = None
    formularios_medicos_available = False
    area_medica_enhanced_available = False
    
# Importar utilidades
try:
    from src.utils import load_json_data
    utils_available = True
except ImportError:
    utils_available = False
    
    
try:
    from src.modules.areanutricion import mostrar_analisis_nutricion
    areanutricion_available = True
except ImportError:
    mostrar_analisis_nutricion = None
    areanutricion_available = False   
    
try:
    from src.modules.dashboard_360 import dashboard_360
    dashboard_360_available = True
except ImportError:
    dashboard_360 = None
    dashboard_360_available = False



def get_gcp_credentials():
    """Obtener credenciales de Google Cloud desde Streamlit secrets"""
    try:
        gcp_service_account = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(gcp_service_account)
        return credentials
    except Exception as e:
        st.error(f"Error al cargar credenciales: {e}")
        return None

def load_json_data(filename, default_data=None):
    """Función de respaldo para cargar JSON"""
    filepath = os.path.join('credentials', filename)
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return default_data if default_data is not None else {}

# Configuración de la página
st.set_page_config(
    page_title="Club Argentino de Rugby - Sistema de Gestión",
    page_icon="🏉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para el CAR
def load_car_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    :root {
        --car-blue-dark: #1A2C56;
        --car-blue-light: #6BB4E8;
        --car-white: #FFFFFF;
        --car-gray: #F5F5F5;
        --car-success: #28a745;
        --car-warning: #ffc107;
        --car-danger: #dc3545;
    }
    
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, var(--car-blue-dark) 0%, var(--car-blue-light) 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        font-family: 'Inter', sans-serif;
    }
    
    .area-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 4px solid var(--car-blue-light);
    }
    
    .metric-card {
        background: linear-gradient(135deg, var(--car-blue-light) 0%, var(--car-blue-dark) 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .metric-card h3 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .metric-card p {
        margin: 0.5rem 0 0 0;
        font-size: 1rem;
        opacity: 0.9;
    }
    
    .login-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
    }
    
    .stButton > button {
        background: linear-gradient(45deg, var(--car-blue-dark), var(--car-blue-light));
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(107, 180, 232, 0.4);
    }
    
    .stSelectbox > div > div > select {
        border-radius: 10px;
        border: 2px solid #E9ECEF;
    }
    
    .stTextInput > div > div > input {
        border-radius: 10px;
        border: 2px solid #E9ECEF;
    }
    
    .stTextArea > div > div > textarea {
        border-radius: 10px;
        border: 2px solid #E9ECEF;
    }
    
    /* Ocultar elementos de Streamlit */
    .stDeployButton {display: none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

class AuthManager:
    def __init__(self, credentials_file='credentials/users_credentials.json'):
        self.credentials_file = credentials_file
        self.ensure_credentials_file()
        
        
    def ensure_credentials_file(self):
        try:
            with open(self.credentials_file, 'r', encoding='utf-8') as f:
                json.load(f)
        except FileNotFoundError:
            default_users = {
                "admin": {
                    "password": self.hash_password("admin123"),
                    "name": "Administrador",
                    "email": "admin@car.com.ar",
                    "role": "admin",
                    "created_at": datetime.now().isoformat()
                }
            }
            with open(self.credentials_file, 'w', encoding='utf-8') as f:
                json.dump(default_users, f, indent=2, ensure_ascii=False)
    
    def hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    
    def authenticate(self, username: str, password: str) -> Dict:
        try:
            with open(self.credentials_file, 'r', encoding='utf-8') as f:
                users = json.load(f)
            
            if username in users:
                stored_password = users[username]['password']
                if stored_password == self.hash_password(password):
                    return users[username]
            return None
        except:
            return None

class MedicalManager:
    def __init__(self):
        self.injuries_file = 'credentials/medical_records.json'
        self.ensure_medical_file()
    
    def ensure_medical_file(self):
        try:
            with open(self.injuries_file, 'r', encoding='utf-8') as f:
                json.load(f)
        except FileNotFoundError:
            # Datos de ejemplo para el área médica
            sample_data = {
                "injuries": [
                    {
                        "id": 1,
                        "player_name": "Juan Pérez",
                        "division": "Primera",
                        "injury_type": "Esguince de tobillo",
                        "severity": "Leve",
                        "date_occurred": "2025-09-15",
                        "expected_recovery": "2025-10-15",
                        "status": "En recuperación",
                        "doctor": "Dr. García",
                        "notes": "Reposo y fisioterapia"
                    },
                    {
                        "id": 2,
                        "player_name": "Carlos Rodríguez",
                        "division": "Primera",
                        "injury_type": "Distensión muscular",
                        "severity": "Moderada",
                        "date_occurred": "2025-09-20",
                        "expected_recovery": "2025-10-20",
                        "status": "En recuperación",
                        "doctor": "Dr. García",
                        "notes": "Tratamiento kinesiológico"
                    },
                    {
                        "id": 3,
                        "player_name": "Miguel Torres",
                        "division": "Reserva",
                        "injury_type": "Contusión",
                        "severity": "Leve",
                        "date_occurred": "2025-10-01",
                        "expected_recovery": "2025-10-10",
                        "status": "Recuperado",
                        "doctor": "Dr. García",
                        "notes": "Apto para entrenar"
                    },
                    {
                        "id": 4,
                        "player_name": "Franco Silva",
                        "division": "Juveniles",
                        "injury_type": "Fractura menor",
                        "severity": "Grave",
                        "date_occurred": "2025-08-30",
                        "expected_recovery": "2025-11-30",
                        "status": "En recuperación",
                        "doctor": "Dr. García",
                        "notes": "Inmovilización y seguimiento"
                    },
                    {
                        "id": 5,
                        "player_name": "Diego Martín",
                        "division": "Reserva",
                        "injury_type": "Contractura muscular",
                        "severity": "Leve",
                        "date_occurred": "2025-10-05",
                        "expected_recovery": "2025-10-12",
                        "status": "En recuperación",
                        "doctor": "Dr. Fernández",
                        "notes": "Elongación y masajes"
                    }
                ]
            }
            with open(self.injuries_file, 'w', encoding='utf-8') as f:
                json.dump(sample_data, f, indent=2, ensure_ascii=False)
    
    def get_injuries(self):
        with open(self.injuries_file, 'r', encoding='utf-8') as f:
            return json.load(f)['injuries']
    
    def add_injury(self, injury_data):
        try:
            with open(self.injuries_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            data = {"injuries": []}
        
        injuries = data['injuries']
        new_id = max([injury['id'] for injury in injuries], default=0) + 1
        injury_data['id'] = new_id
        injuries.append(injury_data)
        
        with open(self.injuries_file, 'w', encoding='utf-8') as f:
            json.dump({"injuries": injuries}, f, indent=2, ensure_ascii=False)

class NutritionManager:
    def __init__(self):
        self.nutrition_file = 'credentials/nutrition_records.json'
        self.ensure_nutrition_file()
    
    def ensure_nutrition_file(self):
        try:
            with open(self.nutrition_file, 'r', encoding='utf-8') as f:
                json.load(f)
        except FileNotFoundError:
            # Datos de ejemplo para nutrición
            sample_data = {
                "meal_plans": [
                    {
                        "id": 1,
                        "player_name": "Juan Pérez",
                        "division": "Primera",
                        "plan_type": "Ganancia de masa muscular",
                        "calories_target": 3500,
                        "protein_target": 150,
                        "carbs_target": 400,
                        "fat_target": 120,
                        "created_date": "2025-09-01",
                        "nutritionist": "Lic. María López",
                        "notes": "Plan para aumento de peso controlado"
                    },
                    {
                        "id": 2,
                        "player_name": "Carlos Rodríguez",
                        "division": "Primera",
                        "plan_type": "Mantenimiento",
                        "calories_target": 3000,
                        "protein_target": 130,
                        "carbs_target": 350,
                        "fat_target": 100,
                        "created_date": "2025-09-15",
                        "nutritionist": "Lic. María López",
                        "notes": "Plan equilibrado para rendimiento"
                    },
                    {
                        "id": 3,
                        "player_name": "Miguel Torres",
                        "division": "Reserva",
                        "plan_type": "Definición",
                        "calories_target": 2800,
                        "protein_target": 140,
                        "carbs_target": 300,
                        "fat_target": 90,
                        "created_date": "2025-09-20",
                        "nutritionist": "Lic. Juan Nutricionista",
                        "notes": "Reducción de grasa corporal"
                    },
                    {
                        "id": 4,
                        "player_name": "Franco Silva",
                        "division": "Juveniles",
                        "plan_type": "Crecimiento",
                        "calories_target": 3200,
                        "protein_target": 120,
                        "carbs_target": 380,
                        "fat_target": 110,
                        "created_date": "2025-09-25",
                        "nutritionist": "Lic. María López",
                        "notes": "Plan para desarrollo juvenil"
                    }
                ]
            }
            with open(self.nutrition_file, 'w', encoding='utf-8') as f:
                json.dump(sample_data, f, indent=2, ensure_ascii=False)
    
    def get_nutrition_data(self):
        with open(self.nutrition_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def add_meal_plan(self, plan_data):
        try:
            with open(self.nutrition_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            data = {"meal_plans": []}
        
        meal_plans = data['meal_plans']
        new_id = max([plan['id'] for plan in meal_plans], default=0) + 1
        plan_data['id'] = new_id
        meal_plans.append(plan_data)
        
        with open(self.nutrition_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

def login_page():
    load_car_styles()
    
    # Fondo con gradiente
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #1A2C56 0%, #2C4A7A 50%, #6BB4E8 100%);
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="main-header">
        <h1>🏉 Club Argentino de Rugby</h1>
        <h3>Sistema de Digitalización</h3>
        <p>Centralizacion de Módulos: Área Médica, Nutrición y Física</p>
    </div>
    """, unsafe_allow_html=True)
    
    auth_manager = AuthManager()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown("### 🔐 Iniciar Sesión")
        
        username = st.text_input("👤 Usuario", placeholder="Ingresa tu usuario")
        password = st.text_input("🔒 Contraseña", type="password", placeholder="Ingresa tu contraseña")
        
        remember_me = st.checkbox("🔄 Recordarme")
        
        if st.button("🚀 Ingresar", use_container_width=True):
            if username and password:
                user_data = auth_manager.authenticate(username, password)
                if user_data:
                    st.session_state.authenticated = True
                    st.session_state.user_data = user_data
                    st.session_state.username = username
                    st.session_state.remember_me = remember_me
                    st.success("✅ Acceso exitoso")
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos")
            else:
                st.warning("⚠️ Por favor completa todos los campos")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Credenciales de prueba
        st.info("🔑 **Credenciales de prueba:**\n\n**Usuario:** admin\n\n**Contraseña:** admin123")


def medical_area():
    """Área médica usando el sistema completo de areamedica.py"""
    
    try:
        # LAZY LOADING - importar solo cuando se necesite
        from src.modules.areamedica import main_streamlit as area_medica_main
        
        # Usar la función main_streamlit() 
        area_medica_main()
        
    except ImportError as e:
        st.error(f"❌ Error al cargar el módulo de área médica: {e}")
        st.info("🔧 Verifica que el archivo src/modules/areamedica.py esté disponible")
        show_basic_medical_system()
        
    except Exception as e:
        st.error(f"❌ Error inesperado en el área médica: {e}")
        st.info("🔧 Problema con la configuración de Google Sheets")
        show_basic_medical_system()


def show_basic_medical_system():
    """Sistema médico básico cuando el principal falla"""
    
    st.markdown("""
    <div class="main-header">
        <h1>🏥 Área Médica - CAR</h1>
        <h3>Sistema de Gestión Médica (Modo Seguro)</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Intentar cargar datos médicos locales
    try:
        medical_manager = MedicalManager()
        injuries = medical_manager.get_injuries()
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_injuries = len(injuries)
            st.markdown(f"""
            <div class="metric-card">
                <h3>{total_injuries}</h3>
                <p>Total Lesiones</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            active_injuries = len([i for i in injuries if i.get('status') == 'En recuperación'])
            st.markdown(f"""
            <div class="metric-card">
                <h3>{active_injuries}</h3>
                <p>Lesiones Activas</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            severe_injuries = len([i for i in injuries if i.get('severity') == 'Grave'])
            st.markdown(f"""
            <div class="metric-card">
                <h3>{severe_injuries}</h3>
                <p>Casos Graves</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            doctors = len(set([i.get('doctor', 'Sin asignar') for i in injuries]))
            st.markdown(f"""
            <div class="metric-card">
                <h3>{doctors}</h3>
                <p>Médicos</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Tabla de lesiones
        st.markdown('<div class="area-card">', unsafe_allow_html=True)
        st.subheader("📋 Registros Médicos")
        
        if injuries:
            df_injuries = pd.DataFrame(injuries)
            st.dataframe(df_injuries, use_container_width=True)
        else:
            st.info("📝 No hay registros médicos disponibles")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Formulario básico para nueva lesión
        st.markdown('<div class="area-card">', unsafe_allow_html=True)
        st.subheader("➕ Registrar Nueva Lesión")
        
        with st.form("nueva_lesion_basica", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                player_name = st.text_input("👤 Nombre del Jugador")
                division = st.selectbox("🏉 División", ["Primera", "Reserva", "Juveniles", "Infantiles"])
                injury_type = st.text_input("🩺 Tipo de Lesión")
                severity = st.selectbox("⚠️ Severidad", ["Leve", "Moderada", "Grave"])
            
            with col2:
                date_occurred = st.date_input("📅 Fecha de la Lesión", value=date.today())
                doctor = st.text_input("👨‍⚕️ Médico", value="Dr. García")
                notes = st.text_area("📝 Observaciones")
            
            if st.form_submit_button("💾 Guardar Lesión", use_container_width=True):
                if player_name and division and injury_type:
                    new_injury = {
                        "player_name": player_name,
                        "division": division,
                        "injury_type": injury_type,
                        "severity": severity,
                        "date_occurred": date_occurred.isoformat(),
                        "expected_recovery": (date_occurred + timedelta(days=14)).isoformat(),
                        "status": "En recuperación",
                        "doctor": doctor,
                        "notes": notes
                    }
                    
                    medical_manager.add_injury(new_injury)
                    st.success("✅ Lesión registrada exitosamente")
                    st.rerun()
                else:
                    st.error("❌ Por favor completa los campos obligatorios")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
    except Exception as fallback_error:
        st.error(f"❌ Error en el sistema de respaldo: {fallback_error}")
        
        # Sistema mínimo de emergencia
        st.markdown("""
        <div style="background: #f0f2f6; padding: 2rem; border-radius: 10px; text-align: center;">
            <h3>🏥 Área Médica - Modo Emergencia</h3>
            <p>El sistema médico no está disponible temporalmente.</p>
            <p>Por favor contacta al administrador del sistema.</p>
            <br>
            <h4>📞 Contacto de Emergencia:</h4>
            <p><strong>Email:</strong> medico@car.com.ar</p>
            <p><strong>Teléfono:</strong> (011) 4XXX-XXXX</p>
        </div>
        """, unsafe_allow_html=True)


def main_dashboard():
    load_car_styles()
    
    # Sidebar para navegación
    st.sidebar.markdown(f"""
    <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #1A2C56, #6BB4E8); 
                color: white; border-radius: 10px; margin-bottom: 1rem;">
        <h3>👋 Bienvenido</h3>
        <p><strong>{st.session_state.user_data['name']}</strong></p>
        <p>Rol: {st.session_state.user_data['role'].title()}</p>
        <p>🏉 CAR - Sistema Digital</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Menú de navegación
    menu_options = {
        "🏠 Portada": "dashboard",
        "📊 Panel del Jugador": "dashboard_360",
        "🏥 Área Médica": "medical",
        "🥗 Área Nutrición": "nutricion",
        "🏋️ Área Física": "physical",
        "⚙️ Configuración": "settings"
    }
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "dashboard"
    
    st.sidebar.markdown("### 📋 Menú Principal")
    
    for option_name, option_key in menu_options.items():
        button_style = "🔹" if st.session_state.current_page == option_key else ""
        if st.sidebar.button(f"{button_style} {option_name}", use_container_width=True):
            st.session_state.current_page = option_key
            st.rerun()
    
    st.sidebar.markdown("---")
    
    if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("**📞 Contacto CAR:**")
    st.sidebar.markdown("📧 calvoj550@mail.com")
    st.sidebar.markdown("📱 (2213571957)")

    # ✅ NAVEGACIÓN CORREGIDA
    if st.session_state.current_page == "dashboard":
        dashboard_main()
        
    elif st.session_state.current_page == "medical":
        medical_area()
        
    elif st.session_state.current_page == "nutricion":
        # ✅ Usar el módulo avanzado de nutrición
        if areanutricion_available and mostrar_analisis_nutricion is not None:
            try:
                mostrar_analisis_nutricion()
            except Exception as e:
                st.error(f"❌ Error en el módulo de nutrición: {e}")
                st.info("🔧 Verifica la configuración del módulo areanutricion.py")
        else:
            st.error("❌ Módulo de Área de Nutrición no disponible")
            st.info("🔧 Verifica que el archivo src/modules/areanutricion.py esté correctamente configurado")

    elif st.session_state.current_page == "physical":
        physical_page()
    
    # AGREGAR ESTA NUEVA SECCIÓN
    elif st.session_state.current_page == "dashboard_360":
        if dashboard_360_available and dashboard_360 is not None:
            try:
                dashboard_360()
            except Exception as e:
                st.error(f"❌ Error en el Panel del Jugador: {e}")
                st.info("🔧 Verifica la configuración del módulo dashboard_360.py")
                st.info("💡 Asegúrate de que los módulos médico, físico y nutrición estén funcionando")
        else:
            st.error("❌ Panel del Jugador no disponible")
            st.info("🔧 Verifica que el archivo src/modules/360.py esté presente")
            st.info("📋 Funcionalidades requeridas:")
            st.code("""
            - src/modules/360.py
            - src/modules/areamedica.py  
            - src/modules/areafisica.py
            - src/modules/areanutricion.py
            """)
        
    elif st.session_state.current_page == "settings":
        settings_page()
        
    else:
        # ✅ Manejo de páginas no reconocidas
        st.error(f"❌ Página '{st.session_state.current_page}' no reconocida")
        st.info("🔄 Regresando al dashboard principal...")
        st.session_state.current_page = "dashboard"
        st.rerun()



def dashboard_main():
    """Dashboard principal del sistema CAR - Versión comercial simplificada"""
    
    # CSS personalizado con tu branding
    st.markdown("""
    <style>
    .hero-container {
        background: linear-gradient(135deg, #0B132B 0%, #1E90FF 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .hero-content {
        flex: 2;
        color: white;
    }
    .hero-logo {
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        padding-left: 2rem;
    }
    .hero-title {
        color: white;
        font-size: 48px;
        font-weight: 900;
        margin-bottom: 15px;
        line-height: 1.1;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    .hero-accent {
        color: #39FF14;
    }
    .hero-subtitle {
        color: rgba(255,255,255,0.9);
        font-size: 22px;
        font-weight: 400;
        margin-bottom: 15px;
    }
    .hero-description {
        color: rgba(255,255,255,0.8);
        font-size: 17px;
        margin-bottom: 0;
        line-height: 1.4;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Contenedor azul con título, subtítulo y logo
    st.markdown("""
    <div class="hero-container">
        <div class="hero-content">
            <h1 class="hero-title">
                SISTEMA DE<br>
                <span class="hero-accent">RENDIMIENTO ELITE</span>
            </h1>
            <h2 class="hero-subtitle">
                La plataforma integral que revoluciona la gestión deportiva
            </h2>
            <p class="hero-description">
                Centralizamos datos médicos, físicos y nutricionales para una toma de decisiones inteligente
            </p>
        </div>
        <div class="hero-logo">
    """, unsafe_allow_html=True)
    
    # Logo dentro del contenedor
    try:
        st.image(r"C:\Users\dell\Desktop\Car\logo.png", width=200)
    except:
        # Respaldo con logo estilizado
        st.markdown("""
        <div style="
            background: linear-gradient(45deg, #39FF14, #1E90FF); 
            width: 150px; height: 150px; 
            border-radius: 20px; 
            display: flex; align-items: center; justify-content: center; 
            color: #0B132B; font-size: 36px; font-weight: 900;
            margin: 0 auto;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        ">
            SRE
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Los Principios de la Digitalización - Versión Streamlit nativa
    st.markdown("## 🚀 Los Principios de la Digitalización Deportiva")
    st.markdown("---")
    
    # Principio 1
    st.markdown("### 1️⃣ **Capacitación Profesional**")
    st.write("""
    La digitalización exitosa comienza con profesionales capacitados. Nuestro sistema no solo te da las herramientas, 
    sino que **forma a tu equipo** para maximizar el potencial de cada dato recopilado.
    """)
    
    # Principio 2  
    st.markdown("### 2️⃣ **Centralización de Información**")
    st.write("""
    Todos los datos en un solo lugar: rendimiento físico, análisis técnico, bienestar del jugador y métricas de salud. 
    La **centralización** elimina silos de información y permite una visión integral del atleta.
    """)
    
    # Principio 3
    st.markdown("### 3️⃣ **Toma de Decisiones Basada en Datos**")
    st.write("""
    Con información centralizada y profesionales capacitados, las decisiones dejan de ser intuitivas para convertirse en 
    **estratégicas y fundamentadas**. Cada cambio de entrenamiento, cada rotación, cada plan nutricional tiene respaldo científico.
    """)
    
    # Beneficios de la Digitalización - Versión Streamlit nativa
    st.markdown("## 💡 ¿Por qué digitalizar tu club deportivo?")
    st.markdown("---")
    
    # Crear las 3 columnas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📈 **Mejora del Rendimiento**")
        st.write("- **Monitoreo en tiempo real** de métricas clave de cada atleta")
        st.write("- **Prevención de lesiones** mediante análisis predictivo")
        st.write("- **Optimización de entrenamientos** basada en datos objetivos")
    
    with col2:
        st.markdown("### 🎯 **Ventaja Competitiva**")
        st.write("- **Decisiones estratégicas** respaldadas por información precisa")
        st.write("- **Identificación de talentos** mediante análisis de rendimiento")
        st.write("- **Planificación táctica** con base en datos históricos y actuales")
    
    with col3:
        st.markdown("### ⚡ **Eficiencia Operativa**")
        st.write("- **Reducción de costos** en lesiones y tiempo perdido")
        st.write("- **Automatización** de reportes y seguimiento")
        st.write("- **Integración** de todas las áreas del club en una plataforma")
    
    # Solicitar Demo - Usando tu contenido de demo.py
    st.markdown("""
    <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); padding: 2rem; border-radius: 15px; margin: 2rem 0;">
        <h2 style="color: #39FF14; text-align: center; margin-bottom: 2rem;">Solicitar Demo</h2>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form(key='demo_form'):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input('Nombre / Club', placeholder="Ej: Club Atlético San Lorenzo")
            email = st.text_input('Email', placeholder="contacto@tuclub.com")
        with col2:
            phone = st.text_input('Teléfono (opcional)', placeholder="(011) 4XXX-XXXX")
            club_type = st.selectbox('Tipo de Club', ['Rugby', 'Fútbol', 'Hockey', 'Básquet', 'Otro'])
        
        message = st.text_area('Mensaje (qué querés ver en la demo)', placeholder="Contanos qué aspectos te interesan más del sistema...")
        
        submitted = st.form_submit_button('Enviar solicitud', use_container_width=True)
        
        if submitted:
            if name and email:
                st.success('🎉 Gracias — tu solicitud fue enviada. Nos comunicamos por email para coordinar la demo.')
                st.info('📱 También podés contactarnos directamente por WhatsApp: **+54 9 221 357-1957**')
            else:
                st.error('Por favor completá al menos el nombre y email')
    
    # Footer con tu información
    st.markdown("""
    <div style="color: rgba(255,255,255,0.6); font-size: 13px; padding: 2rem 0; text-align: center; border-top: 1px solid rgba(255,255,255,0.1); margin-top: 2rem;">
        <p><strong>SRE — Sistema de Rendimiento Élite</strong></p>
        <p>📧 calvoj550@gmail.com • 📱 +54 9 221 357-1957</p>
        <p>Desarrollado con ❤️ para la digitalización deportiva • © 2025</p>
    </div>
    """, unsafe_allow_html=True)
    
    

def settings_page():
    st.markdown("""
    <div class="main-header">
        <h1>⚙️ Configuración del Sistema</h1>
        <h3>Personalización y Administración</h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="area-card">', unsafe_allow_html=True)
    st.subheader("👤 Información del Usuario")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("📛 Nombre", value=st.session_state.user_data['name'], disabled=True)
        st.text_input("📧 Email", value=st.session_state.user_data['email'], disabled=True)
        st.text_input("👤 Usuario", value=st.session_state.username, disabled=True)
    
    with col2:
        st.text_input("🎭 Rol", value=st.session_state.user_data['role'].title(), disabled=True)
        created_at = st.session_state.user_data.get('created_at', 'No disponible')
        if created_at != 'No disponible':
            try:
                created_date = datetime.fromisoformat(created_at).strftime("%d/%m/%Y %H:%M")
            except:
                created_date = created_at
        else:
            created_date = created_at
        st.text_input("📅 Fecha de Registro", value=created_date, disabled=True)
        
        # Última sesión
        last_login = datetime.now().strftime("%d/%m/%Y %H:%M")
        st.text_input("🕐 Última Sesión", value=last_login, disabled=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="area-card">', unsafe_allow_html=True)
    st.subheader("🎨 Personalización del Sistema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🌈 Configuración Visual:**")
        theme_option = st.selectbox("Tema del Sistema", ["Clásico CAR", "Modo Oscuro", "Alto Contraste"], disabled=True)
        language = st.selectbox("Idioma", ["Español", "English"], disabled=True)
        st.checkbox("Mostrar tips de ayuda", value=True, disabled=True)
    
    with col2:
        st.markdown("**🔔 Notificaciones:**")
        st.checkbox("Nuevas lesiones", value=True, disabled=True)
        st.checkbox("Planes nutricionales", value=True, disabled=True)
        st.checkbox("Recordatorios médicos", value=False, disabled=True)
    
    st.info("🚧 **Próximamente:** Estas configuraciones estarán disponibles en futuras versiones del sistema.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="area-card">', unsafe_allow_html=True)
    st.subheader("📊 Estadísticas de Uso")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🔐 Sesiones Iniciadas", "1", delta="Actual")
    
    with col2:
        st.metric("📝 Registros Creados", "0", delta="Esta sesión")
    
    with col3:
        st.metric("⏱️ Tiempo en Sistema", "< 1 hora", delta="Sesión actual")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="area-card">', unsafe_allow_html=True)
    st.subheader("🛠️ Herramientas de Administración")
    
    if st.session_state.user_data['role'] == 'admin':
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📊 Exportar Datos:**")
            if st.button("📥 Descargar Datos Médicos"):
                st.info("Funcionalidad en desarrollo - Próximamente disponible")
            
            if st.button("📥 Descargar Datos Nutricionales"):
                st.info("Funcionalidad en desarrollo - Próximamente disponible")
        
        with col2:
            st.markdown("**🔧 Mantenimiento:**")
            if st.button("🔄 Actualizar Base de Datos"):
                st.success("Base de datos actualizada correctamente")
            
            if st.button("📋 Generar Reporte Completo"):
                st.info("Generando reporte... Funcionalidad en desarrollo")
    else:
        st.info("🔒 Las herramientas de administración están disponibles solo para administradores.")
    
    st.markdown('</div>', unsafe_allow_html=True)

def sheets_page():
    """Página de integración con Google Sheets"""
    if google_sheets_available and google_sheets_page is not None:
        google_sheets_page()
    else:
        st.error("❌ Módulo de Google Sheets no disponible")
        st.info("🔧 Verifica que los archivos google_sheets_sync.py y sheets_interface.py estén presentes")
        st.info("🔧 También verifica que las dependencias de Google estén instaladas")

def physical_page():
    """Página del Área Física"""
    if physical_area_available and physical_area is not None:
        physical_area()
    else:
        st.error("❌ Módulo de Área Física no disponible")
        st.info("🔧 Verifica que el archivo physical_area.py esté presente")

def main():
    # Verificar autenticación
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        login_page()
    else:
        main_dashboard()

if __name__ == "__main__":
    main()