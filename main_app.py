"""
Sistema Principal del Club Argentino de Rugby (CAR)
Centralizacion de Módulos: Área Médica, Nutrición y Física
Desarrollado con Streamlit
"""
import streamlit as st
import pandas as pd
import os
import sys
import json
import hashlib
from datetime import datetime, date, timedelta
from typing import Dict, List
from google.oauth2 import service_account

# Configuración de credenciales - Manejo de entornos local y producción
credentials = None
try:
    # Intentar cargar desde Streamlit Cloud (producción)
    if hasattr(st, 'secrets') and "gcp_service_account" in st.secrets:
        credentials_dict = dict(st.secrets["gcp_service_account"])
        credentials = service_account.Credentials.from_service_account_info(credentials_dict)
    else:
        # Para desarrollo local - intentar cargar archivo
        credentials_file = 'credentials/service-account-key.json'
        if os.path.exists(credentials_file):
            try:
                credentials = service_account.Credentials.from_service_account_file(credentials_file)
            except Exception as cred_error:
                st.warning(f"⚠️ No se pudieron cargar las credenciales de Google: {cred_error}")
                credentials = None
        else:
            credentials = None
except Exception as e:
    st.warning(f"⚠️ Sistema funcionando sin credenciales de Google Cloud: {str(e)}")
    credentials = None

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
    print()
except ImportError as e:
    mostrar_analisis_nutricion = None
    areanutricion_available = False
    print(f"❌ Error importando areanutricion: {e}")
    import traceback
    traceback.print_exc()
    
    
try:
    from src.modules.dashboard_360 import dashboard_360
    dashboard_360_available = True
except ImportError:
    dashboard_360 = None
    dashboard_360_available = False
    
# Importar módulo de Reportes Médicos
try:
    from src.modules.reportemedico import main_reporte_medico
    reportes_medicos_available = True
except ImportError:
    main_reporte_medico = None
    reportes_medicos_available = False
    
# Importar módulo de Administración (corregir importación)
try:
    from src.modules.administracion import main_administracion
    administracion_available = True
except ImportError as e:
    main_administracion = None
    administracion_available = False
    print(f"Error importando administracion: {e}")  




def get_gcp_credentials():
    """Obtener credenciales de Google Cloud desde Streamlit secrets o archivo local"""
    try:
        # Si ya tenemos credenciales globales, usarlas
        if 'credentials' in globals() and credentials is not None:
            return credentials
            
        # Intentar cargar desde Streamlit Cloud
        if hasattr(st, 'secrets') and "gcp_service_account" in st.secrets:
            credentials_dict = dict(st.secrets["gcp_service_account"])
            return service_account.Credentials.from_service_account_info(
                credentials_dict,
                scopes=['https://www.googleapis.com/auth/spreadsheets', 
                        'https://www.googleapis.com/auth/drive']
            )
        
        # Para desarrollo local - buscar en múltiples ubicaciones
        possible_paths = [
            'credentials/service-account-key.json',
            '../credentials/service-account-key.json',
            'credentials/service_account.json',
            '../credentials/service_account.json'
        ]
        
        for credentials_file in possible_paths:
            if os.path.exists(credentials_file):
                try:
                    # Leer y validar el JSON primero
                    with open(credentials_file, 'r', encoding='utf-8') as f:
                        creds_dict = json.load(f)
                    
                    # Verificar que tenga los campos necesarios
                    required_fields = ['type', 'project_id', 'private_key', 'client_email']
                    if all(field in creds_dict for field in required_fields):
                        creds = service_account.Credentials.from_service_account_info(
                            creds_dict,
                            scopes=['https://www.googleapis.com/auth/spreadsheets',
                                    'https://www.googleapis.com/auth/drive']
                        )
                        st.success(f"✅ Credenciales cargadas desde: {credentials_file}")
                        return creds
                    else:
                        st.warning(f"⚠️ Archivo {credentials_file} incompleto")
                        
                except json.JSONDecodeError as e:
                    st.error(f"❌ Error JSON en {credentials_file}: {e}")
                    continue
                except Exception as e:
                    st.warning(f"⚠️ Error leyendo {credentials_file}: {e}")
                    continue
        
        # Sin credenciales disponibles
        st.error("❌ No se encontraron credenciales válidas de Google Cloud")
        return None
        
    except Exception as e:
        st.error(f"Error crítico al obtener credenciales: {str(e)}")
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
    page_icon="car.jpg",  # También funciona con car.ico
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
    /* #MainMenu {visibility: hidden;} */        /* ← COMENTADO PARA MOSTRAR MENÚ */
    footer {visibility: hidden;}
    /* header {visibility: hidden;} */           /* ← COMENTADO PARA MOSTRAR HEADER */
    </style>
    """, unsafe_allow_html=True)
    
class AuthManager:
    def __init__(self, credentials_file='credentials/users_credentials.json'):
        self.credentials_file = credentials_file
        self.ensure_credentials_file()
        
    def ensure_credentials_file(self):
        """Asegurar que existe el archivo de credenciales"""
        # Crear carpeta si no existe
        os.makedirs(os.path.dirname(self.credentials_file), exist_ok=True)
        
        # Hash correcto de la contraseña "Sistemacar2026"
        correct_hash = "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"
        
        # Usuario por defecto
        default_users = {
            "admin": {
                "password": correct_hash,
                "name": "Administrador",
                "email": "admin@car.com.ar",
                "role": "admin",
                "created_at": datetime.now().isoformat()
            }
        }
        
        # Siempre sobrescribir para asegurar que esté correcto
        with open(self.credentials_file, 'w', encoding='utf-8') as f:
            json.dump(default_users, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Credenciales regeneradas en: {self.credentials_file}")
    
    def hash_password(self, password: str) -> str:
        """Generar hash SHA256 de la contraseña"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def authenticate(self, username: str, password: str) -> Dict:
        """Autenticar usuario"""
        try:
            with open(self.credentials_file, 'r', encoding='utf-8') as f:
                users = json.load(f)
            
            if username in users:
                stored_password = users[username]['password']
                input_password_hash = self.hash_password(password)
                
                if stored_password == input_password_hash:
                    return users[username]
            return None
        except Exception as e:
            print(f"❌ Error en autenticación: {e}")
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
    """Página de inicio de sesión con diseño mejorado - AUTENTICACIÓN HARDCODED"""
    
    import base64
    
    # Cargar y codificar la imagen de fondo
    def get_base64_image(image_path):
        try:
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()
        except:
            return None
    
    bg_image = get_base64_image("entrada.png")
    
    # CSS personalizado para el login con imagen de fondo
    if bg_image:
        bg_style = f"""
        .stApp {{
            background-image: url("data:image/png;base64,{bg_image}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
            font-family: 'Inter', sans-serif;
        }}
        """
    else:
        bg_style = """
        .stApp {
            background: linear-gradient(135deg, #1A2C56 0%, #2C4A7A 50%, #6BB4E8 100%);
            font-family: 'Inter', sans-serif;
        }
        """
    
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* Ocultar elementos de Streamlit */
    .stApp > header {{visibility: hidden;}}
    .stDeployButton {{display: none;}}
    footer {{visibility: hidden;}}
    #MainMenu {{visibility: hidden;}}
    
    /* Fondo con imagen */
    {bg_style}
    
    /* Overlay oscuro sobre la imagen */
    .stApp::before {{
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(26, 44, 86, 0.65);
        z-index: 0;
    }}
    
    /* Contenedor principal */
    .main .block-container {{
        position: relative;
        z-index: 1;
        padding-top: 5rem;
        max-width: 500px;
        margin: 0 auto;
    }}
    
    /* Título principal */
    .login-title {{
        text-align: center;
        color: white;
        margin-bottom: 3rem;
        text-shadow: 2px 2px 8px rgba(0, 0, 0, 0.8);
    }}
    
    .login-title h1 {{
        font-size: 2.8rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: 1px;
        text-transform: uppercase;
    }}
    
    .login-title h2 {{
        font-size: 3.5rem;
        font-weight: 800;
        margin: 0.5rem 0 0 0;
        letter-spacing: 8px;
        color: #6BB4E8;
    }}
    
    .login-subtitle {{
        font-size: 1.1rem;
        font-weight: 400;
        margin-top: 0.5rem;
        opacity: 0.95;
        letter-spacing: 2px;
    }}
    
    /* Inputs */
    .stTextInput > div > div > input {{
        background: white;
        border: 2px solid #E0E0E0;
        border-radius: 8px;
        padding: 0.5rem 0.75rem;
        font-size: 0.95rem;
        transition: all 0.3s ease;
        max-width: 350px;
        width: 100%;
    }}
    
    .stTextInput > div {{
        max-width: 350px;
        margin: 0 auto;
    }}
    
    .stTextInput > div > div > input:focus {{
        border-color: #6BB4E8;
        box-shadow: 0 0 0 2px rgba(107, 180, 232, 0.2);
    }}
    
    /* Botón de ingresar */
    .stButton > button {{
        background: linear-gradient(135deg, #1A2C56 0%, #6BB4E8 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        font-size: 0.95rem;
        font-weight: 600;
        letter-spacing: 1px;
        transition: all 0.3s ease;
        text-transform: uppercase;
        max-width: 350px;
        margin: 0 auto;
        display: block;
        margin-top: 1rem;
    }}
    
    .stButton > button:hover {{
        background: linear-gradient(135deg, #6BB4E8 0%, #1A2C56 100%);
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(107, 180, 232, 0.4);
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # Título principal
    st.markdown("""
    <div class="login-title">
        <h1>Club Argentino de Rugby</h1>
        <h2>CAR</h2>
        <p class="login-subtitle">ACCESO AL SISTEMA</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Formulario de login - VERSIÓN SIMPLIFICADA CON HARDCODE
    username = st.text_input("USUARIO", placeholder="Ingresa tu usuario", label_visibility="collapsed", key="username_input")
    st.markdown('<div style="height: 1rem;"></div>', unsafe_allow_html=True)
    
    password = st.text_input("CONTRASEÑA", type="password", placeholder="Ingresa tu contraseña", label_visibility="collapsed", key="password_input")
    
    remember_me = st.checkbox("🔄 Recordarme")
    
    if st.button("INGRESAR"):
        # AUTENTICACIÓN HARDCODED - Sin archivo JSON
        if username == "admin" and password == "Sistemacar2026":
            st.session_state.authenticated = True
            st.session_state.user_data = {
                "name": "Administrador",
                "email": "admin@car.com.ar",
                "role": "admin",
                "created_at": datetime.now().isoformat()
            }
            st.session_state.username = username
            st.session_state.remember_me = remember_me
            st.success("✅ Acceso exitoso")
            st.rerun()
        else:
            st.error("❌ Usuario o contraseña incorrectos")
            # Debug info (remover en producción)
            st.info(f"🔍 Usuario ingresado: '{username}' | Contraseña: '{password}'")
    
    st.markdown("""
    <div class="forgot-password" style="text-align: center; margin-top: 1rem;">
        <a href="#" style="color: white; text-decoration: none;">¿Olvidaste tu contraseña?</a>
    </div>
    """, unsafe_allow_html=True)
    
    # Credenciales de prueba (pequeño y discreto)
    st.markdown("""
    <div style="text-align: center; margin-top: 2rem; color: rgba(255,255,255,0.7); font-size: 0.85rem;">
        <p>🔑 Credenciales de prueba: <strong>Consultar +2213571957</strong>
    </div>
    """, unsafe_allow_html=True)

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



# ...existing code...

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
    
    st.sidebar.markdown("### 🧭 Menú Principal")
    
    # Botones individuales en el sidebar (como estaba antes)
    if st.sidebar.button("🏠 Portada", use_container_width=True):
        st.session_state.current_page = "dashboard"
        st.rerun()
    
    if st.sidebar.button("📊 Panel del Jugador", use_container_width=True):
        st.session_state.current_page = "dashboard_360"
        st.rerun()
    
    if st.sidebar.button("🏥 Área Médica", use_container_width=True):
        st.session_state.current_page = "medical"
        st.rerun()
    
    if st.sidebar.button("📄 Reportes Médicos", use_container_width=True):
        st.session_state.current_page = "medical_reports"
        st.rerun()
    
    if st.sidebar.button("🥗 Área Nutrición", use_container_width=True):
        st.session_state.current_page = "nutricion"
        st.rerun()
    
    if st.sidebar.button("🏋️ Área Física", use_container_width=True):
        st.session_state.current_page = "physical"
        st.rerun()
    
    if st.sidebar.button("📋 Administración", use_container_width=True):
        st.session_state.current_page = "administracion"
        st.rerun()
    
    if st.sidebar.button("⚙️ Configuración", use_container_width=True):
        st.session_state.current_page = "settings"
        st.rerun()
    
    # Navegación por páginas (mantener igual)
    if st.session_state.current_page == "dashboard":
        dashboard_main()
    
    elif st.session_state.current_page == "dashboard_360":
        if dashboard_360_available and dashboard_360 is not None:
            try:
                dashboard_360()
            except Exception as e:
                st.error(f"❌ Error en Dashboard 360: {e}")
        else:
            st.error("❌ Dashboard 360 no disponible")
    
    elif st.session_state.current_page == "medical":
        medical_area()
    
    elif st.session_state.current_page == "nutricion":
        if areanutricion_available and mostrar_analisis_nutricion is not None:
            try:
                mostrar_analisis_nutricion()
            except Exception as e:
                st.error(f"❌ Error en Área Nutrición: {e}")
                st.info("🔧 Verifica la configuración del módulo de nutrición")
        else:
            st.error("❌ Área Nutrición no disponible")
            st.info("🔧 Verifica que el archivo src/modules/areanutricion.py esté presente")
    
    elif st.session_state.current_page == "physical":
        if physical_area_available and physical_area is not None:
            try:
                physical_area()
            except Exception as e:
                st.error(f"❌ Error en Área Física: {e}")
                st.info("🔧 Verifica la configuración del módulo de área física")
        else:
            st.error("❌ Área Física no disponible")
            st.info("🔧 Verifica que el archivo src/modules/areafisica.py esté presente")
    
    elif st.session_state.current_page == "medical_reports":
        if reportes_medicos_available and main_reporte_medico is not None:
            try:
                main_reporte_medico()
            except Exception as e:
                st.error(f"❌ Error en Reportes Médicos: {e}")
                st.info("🔧 Verifica la configuración del módulo de reportes médicos")
        else:
            st.error("❌ Reportes Médicos no disponible")
            st.info("🔧 Verifica que el archivo src/modules/reportemedico.py esté presente")
    
    elif st.session_state.current_page == "administracion":
        if administracion_available and main_administracion is not None:
            try:
                main_administracion()
            except Exception as e:
                st.error(f"❌ Error en el módulo de administración: {e}")
                st.error(f"Detalle del error: {str(e)}")
                st.info("🔧 Verifica la configuración del módulo de administración")
                
                # Mostrar traceback para debug
                import traceback
                st.code(traceback.format_exc())
        else:
            st.error("❌ Módulo de Administración no disponible")
            st.info(f"🔧 administracion_available: {administracion_available}")
            st.info(f"🔧 main_administracion: {main_administracion is not None}")
    
    elif st.session_state.current_page == "settings":
        settings_page()
    
    # Botón de logout (mantener igual)
    if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()




# ...existing code... (línea ~850 aprox, función dashboard_main)

def dashboard_main():
    """Dashboard principal del sistema CAR - Versión comercial con branding profesional"""
    
    # CSS personalizado con diseño premium
    st.markdown("""
    <style>
    /* Hero Container con gradiente premium */
    .hero-container {
        background: linear-gradient(135deg, #0B132B 0%, #1C3A6E 50%, #1E90FF 100%);
        padding: 3.5rem 2.5rem;
        border-radius: 25px;
        margin-bottom: 2.5rem;
        position: relative;
        overflow: hidden;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    }
    
    /* Efecto de brillo animado */
    .hero-container::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, 
            transparent, 
            rgba(57, 255, 20, 0.03), 
            transparent
        );
        animation: shine 3s ease-in-out infinite;
    }
    
    @keyframes shine {
        0% { transform: translateX(-100%) translateY(-100%) rotate(30deg); }
        100% { transform: translateX(100%) translateY(100%) rotate(30deg); }
    }
    
    /* Títulos del hero - MEJORADOS PARA LEGIBILIDAD */
    .hero-title {
        color: white;
        font-size: 48px;
        font-weight: 900;
        margin-bottom: 20px;
        line-height: 1.2;
        text-shadow: 
            3px 3px 8px rgba(0,0,0,0.8),
            0 0 30px rgba(57, 255, 20, 0.3);
        letter-spacing: -1px;
        position: relative;
        z-index: 2;
    }
    
    .hero-accent {
        color: #39FF14;
        text-shadow: 
            3px 3px 8px rgba(0,0,0,0.8),
            0 0 40px rgba(57, 255, 20, 0.6),
            0 0 60px rgba(57, 255, 20, 0.4);
        font-size: 56px;
        display: block;
        margin-top: 10px;
    }
    
    .hero-subtitle {
        color: #FFFFFF;
        font-size: 22px;
        font-weight: 600;
        margin-bottom: 18px;
        line-height: 1.4;
        text-shadow: 
            2px 2px 6px rgba(0,0,0,0.7),
            0 0 20px rgba(0,0,0,0.5);
        position: relative;
        z-index: 2;
    }
    
    .hero-description {
        color: rgba(255,255,255,0.95);
        font-size: 17px;
        margin-bottom: 0;
        line-height: 1.6;
        text-shadow: 
            2px 2px 4px rgba(0,0,0,0.6),
            0 0 15px rgba(0,0,0,0.4);
        position: relative;
        z-index: 2;
    }
    
    /* Sección de principios */
    .principles-section {
        margin-top: 3rem;
    }
    
    .section-header {
        display: flex;
        align-items: center;
        margin-bottom: 2rem;
        padding-bottom: 1rem;
        border-bottom: 3px solid #1E90FF;
    }
    
    .section-icon {
        font-size: 2.5rem;
        margin-right: 1rem;
    }
    
    .section-title {
        font-size: 2rem;
        font-weight: 700;
        color: #1A2C56;
        margin: 0;
    }
    
    /* Cards de principios */
    .principle-card {
        background: linear-gradient(135deg, #1A2C56 0%, #2C4A7A 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 1.5rem;
        color: white;
        box-shadow: 0 5px 20px rgba(0,0,0,0.15);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .principle-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(30, 144, 255, 0.3);
    }
    
    .principle-number {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 50px;
        height: 50px;
        background: #39FF14;
        color: #0B132B;
        border-radius: 12px;
        font-size: 24px;
        font-weight: 900;
        margin-bottom: 1rem;
        box-shadow: 0 5px 15px rgba(57, 255, 20, 0.3);
    }
    
    .principle-title {
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 0.8rem;
        color: white;
    }
    
    .principle-text {
        font-size: 1rem;
        line-height: 1.6;
        opacity: 0.95;
    }
    
    .principle-highlight {
        color: #39FF14;
        font-weight: 600;
    }
    
    /* Why section */
    .why-section {
        margin-top: 3rem;
        padding: 2rem;
        background: linear-gradient(135deg, #F8F9FA 0%, #E9ECEF 100%);
        border-radius: 20px;
        border-left: 5px solid #FFC107;
    }
    
    .why-title {
        font-size: 2rem;
        font-weight: 700;
        color: #1A2C56;
        margin-bottom: 2rem;
        display: flex;
        align-items: center;
    }
    
    .why-title::before {
        content: '💡';
        font-size: 2.5rem;
        margin-right: 1rem;
    }
    
    /* Benefits grid */
    .benefit-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 3px 15px rgba(0,0,0,0.1);
        height: 100%;
        border-top: 4px solid #1E90FF;
    }
    
    .benefit-icon {
        font-size: 2rem;
        margin-bottom: 1rem;
    }
    
    .benefit-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #1A2C56;
        margin-bottom: 1rem;
    }
    
    .benefit-list {
        list-style: none;
        padding: 0;
        margin: 0;
    }
    
    .benefit-list li {
        padding: 0.5rem 0;
        color: #495057;
        display: flex;
        align-items: flex-start;
    }
    
    .benefit-list li::before {
        content: '✓';
        color: #28a745;
        font-weight: bold;
        margin-right: 0.5rem;
        font-size: 1.2rem;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .hero-title {
            font-size: 32px;
        }
        
        .hero-accent {
            font-size: 38px;
        }
        
        .hero-subtitle {
            font-size: 16px;
        }
        
        .section-title {
            font-size: 1.5rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Layout con dos columnas para hero - AJUSTADO LOGO MÁS PEQUEÑO
    col_text, col_logo = st.columns([2.5, 1])
    
    with col_text:
        st.markdown("""
        <div class="hero-container">
            <h1 class="hero-title">
                SISTEMA DE
                <span class="hero-accent">RENDIMIENTO ELITE</span>
            </h1>
            <h2 class="hero-subtitle">
                La plataforma integral que revoluciona la gestión deportiva
            </h2>
            <p class="hero-description">
                Centralizamos datos médicos, físicos y nutricionales para una toma de decisiones inteligente
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_logo:
        # Logo más pequeño y centrado
        try:
            st.markdown('<div style="padding: 2rem 0; display: flex; justify-content: center;">', unsafe_allow_html=True)
            st.image("logo.png", width=400)  # Tamaño reducido de logo
            st.markdown('</div>', unsafe_allow_html=True)
        except Exception as e:
            st.markdown("""
            <div style="
                background: linear-gradient(45deg, #39FF14, #1E90FF);
                border-radius: 20px;
                padding: 1.5rem;
                text-align: center;
                color: white;
                font-size: 2.5rem;
                font-weight: 900;
                box-shadow: 0 10px 40px rgba(0,0,0,0.4);
                width: 200px;
                margin: 2rem auto;
            ">
                SRE
            </div>
            """, unsafe_allow_html=True)
    
    # Sección de Principios
    st.markdown("""
    <div class="principles-section">
        <div class="section-header">
            <span class="section-icon">🚀</span>
            <h2 class="section-title">Los Principios de la Digitalización Deportiva</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Principio 1
    st.markdown("""
    <div class="principle-card">
        <div class="principle-number">1</div>
        <h3 class="principle-title">Capacitación Profesional</h3>
        <p class="principle-text">
            La digitalización exitosa comienza con <span class="principle-highlight">profesionales capacitados</span>. 
            Nuestro sistema no solo te da las herramientas, sino que <span class="principle-highlight">forma a tu equipo</span> 
            para maximizar el potencial de cada dato recopilado.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Principio 2
    st.markdown("""
    <div class="principle-card">
        <div class="principle-number">2</div>
        <h3 class="principle-title">Centralización de Información</h3>
        <p class="principle-text">
            Todos los datos en un solo lugar: rendimiento físico, análisis técnico, bienestar del jugador y 
            <span class="principle-highlight">métricas de salud</span>. La centralización elimina silos de información 
            y permite una <span class="principle-highlight">visión integral del atleta</span>.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Principio 3
    st.markdown("""
    <div class="principle-card">
        <div class="principle-number">3</div>
        <h3 class="principle-title">Toma de Decisiones Basada en Datos</h3>
        <p class="principle-text">
            Con información centralizada y profesionales capacitados, las decisiones dejan de ser intuitivas 
            para convertirse en <span class="principle-highlight">estratégicas y fundamentadas</span>. Cada cambio 
            de entrenamiento, cada rotación, cada plan nutricional tiene <span class="principle-highlight">respaldo científico</span>.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sección "¿Por qué digitalizar?"
    st.markdown("""
    <div class="why-section">
        <h2 class="why-title">¿Por qué digitalizar tu club deportivo?</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Grid de beneficios
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="benefit-card">
            <div class="benefit-icon">☑️</div>
            <h3 class="benefit-title">Mejora del Rendimiento</h3>
            <ul class="benefit-list">
                <li>Monitoreo en tiempo real de métricas clave de cada atleta</li>
                <li>Prevención de lesiones mediante análisis predictivo</li>
                <li>Optimización de entrenamientos basada en datos objetivos</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="benefit-card">
            <div class="benefit-icon">🎯</div>
            <h3 class="benefit-title">Ventaja Competitiva</h3>
            <ul class="benefit-list">
                <li>Decisiones estratégicas respaldadas por información precisa</li>
                <li>Identificación de talentos mediante análisis de rendimiento</li>
                <li>Planificación táctica con base en datos históricos y actuales</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="benefit-card">
            <div class="benefit-icon">⚡</div>
            <h3 class="benefit-title">Eficiencia Operativa</h3>
            <ul class="benefit-list">
                <li>Reducción de costos en lesiones y tiempo perdido</li>
                <li>Automatización de reportes y seguimiento</li>
                <li>Integración de todas las áreas del club en una plataforma</li>
            </ul>
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
    # Inicializar session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "dashboard"
    
    if not st.session_state.authenticated:
        login_page()
    else:
        main_dashboard()


if __name__ == "__main__":
    main()