"""
Configuración y datos del Club Argentino de Rugby
Archivo de configuración central para el sistema CAR
"""

from datetime import datetime, date
import json

# Configuración principal del club
CLUB_CONFIG = {
    "name": "Club Argentino de Rugby",
    "short_name": "CAR",
    "founded": "1899",
    "location": "Buenos Aires, Argentina",
    "colors": {
        "primary": "#1A2C56",    # Azul oscuro institucional
        "secondary": "#6BB4E8",  # Celeste CAR
        "white": "#FFFFFF",
        "gray": "#F5F5F5",
        "success": "#28a745",
        "warning": "#ffc107",
        "danger": "#dc3545",
        "info": "#17a2b8"
    },
    "divisions": [
        {
            "name": "Primera",
            "category": "Senior",
            "min_age": 18,
            "max_age": None,
            "description": "División principal del club"
        },
        {
            "name": "Reserva",
            "category": "Senior", 
            "min_age": 18,
            "max_age": None,
            "description": "Segunda división senior"
        },
        {
            "name": "Juveniles",
            "category": "Youth",
            "min_age": 17,
            "max_age": 21,
            "description": "División juvenil"
        },
        {
            "name": "Infantiles",
            "category": "Youth",
            "min_age": 15,
            "max_age": 17,
            "description": "División infantil"
        },
        {
            "name": "Mini Rugby",
            "category": "Kids",
            "min_age": 6,
            "max_age": 14,
            "description": "Categorías menores"
        }
    ],
    "medical_staff": [
        {
            "name": "Dr. García",
            "specialty": "Medicina Deportiva",
            "license": "MN 12345",
            "phone": "(011) 4XXX-XXXX",
            "email": "garcia@car.com.ar"
        },
        {
            "name": "Dr. Fernández",
            "specialty": "Traumatología",
            "license": "MN 12346", 
            "phone": "(011) 4XXX-XXXY",
            "email": "fernandez@car.com.ar"
        },
        {
            "name": "Lic. Kinesiólogo Martín",
            "specialty": "Kinesiología Deportiva",
            "license": "KN 5678",
            "phone": "(011) 4XXX-XXXZ",
            "email": "martin@car.com.ar"
        },
        {
            "name": "Lic. Kinesiólogo Ana",
            "specialty": "Rehabilitación",
            "license": "KN 5679",
            "phone": "(011) 4XXX-XXXA",
            "email": "ana@car.com.ar"
        }
    ],
    "nutrition_staff": [
        {
            "name": "Lic. María López",
            "specialty": "Nutrición Deportiva",
            "license": "NN 9876",
            "phone": "(011) 4XXX-XXXB",
            "email": "lopez@car.com.ar"
        },
        {
            "name": "Lic. Juan Nutricionista",
            "specialty": "Nutrición Clínica",
            "license": "NN 9877",
            "phone": "(011) 4XXX-XXXC", 
            "email": "juan@car.com.ar"
        },
        {
            "name": "Dr. Deportólogo Pérez",
            "specialty": "Medicina del Deporte",
            "license": "MN 12347",
            "phone": "(011) 4XXX-XXXD",
            "email": "perez@car.com.ar"
        }
    ],
    "contact_info": {
        "address": "Av. del Libertador 1234, Buenos Aires",
        "phone": "(011) 4XXX-XXXX",
        "email": "info@car.com.ar",
        "website": "www.clubargentinorugby.com.ar",
        "social_media": {
            "facebook": "ClubArgentinoRugby",
            "instagram": "@car_rugby",
            "twitter": "@CARRugby"
        }
    }
}

# Datos de ejemplo para jugadores por división
SAMPLE_PLAYERS = {
    "Primera": [
        {
            "name": "Juan Pérez",
            "position": "Hooker", 
            "age": 28,
            "weight": 95,
            "height": 180,
            "experience": "10 años"
        },
        {
            "name": "Carlos Rodríguez", 
            "position": "Scrum-half",
            "age": 26,
            "weight": 78,
            "height": 175,
            "experience": "8 años"
        },
        {
            "name": "Sebastián López",
            "position": "Fly-half",
            "age": 27,
            "weight": 82,
            "height": 178,
            "experience": "9 años"
        }
    ],
    "Reserva": [
        {
            "name": "Miguel Torres",
            "position": "Prop",
            "age": 24,
            "weight": 105,
            "height": 185,
            "experience": "4 años"
        },
        {
            "name": "Diego Martín",
            "position": "Lock",
            "age": 25,
            "weight": 98,
            "height": 190,
            "experience": "5 años"
        }
    ],
    "Juveniles": [
        {
            "name": "Franco Silva",
            "position": "Wing",
            "age": 19,
            "weight": 75,
            "height": 176,
            "experience": "2 años"
        },
        {
            "name": "Alejandro Ruiz",
            "position": "Flanker", 
            "age": 20,
            "weight": 88,
            "height": 182,
            "experience": "3 años"
        }
    ],
    "Infantiles": [
        {
            "name": "Matías González",
            "position": "Centre",
            "age": 17,
            "weight": 70,
            "height": 174,
            "experience": "1 año"
        }
    ]
}

# Tipos de lesiones comunes en rugby
INJURY_TYPES = [
    "Esguince de tobillo",
    "Distensión muscular",
    "Contusión",
    "Fractura menor",
    "Contractura muscular",
    "Desgarro muscular",
    "Luxación",
    "Conmoción cerebral",
    "Corte/Herida",
    "Tendinitis",
    "Bursitis",
    "Lesión de ligamentos"
]

# Tipos de planes nutricionales
NUTRITION_PLAN_TYPES = [
    "Mantenimiento",
    "Ganancia de masa muscular", 
    "Definición",
    "Crecimiento",
    "Recuperación post-lesión",
    "Pre-competencia",
    "Post-competencia"
]

# Suplementos comunes
COMMON_SUPPLEMENTS = [
    "Proteína Whey",
    "Creatina",
    "BCAA",
    "Glutamina",
    "Multivitamínico",
    "Omega 3",
    "Magnesio",
    "Vitamina D",
    "Bebida isotónica",
    "Cafeína"
]

# Funciones de utilidad
def get_club_info():
    """Retorna información básica del club"""
    return CLUB_CONFIG

def get_divisions():
    """Retorna lista de divisiones del club"""
    return [division["name"] for division in CLUB_CONFIG["divisions"]]

def get_division_details(division_name):
    """Retorna detalles de una división específica"""
    for division in CLUB_CONFIG["divisions"]:
        if division["name"] == division_name:
            return division
    return None

def get_medical_staff():
    """Retorna lista del personal médico"""
    return [staff["name"] for staff in CLUB_CONFIG["medical_staff"]]

def get_nutrition_staff():
    """Retorna lista del personal de nutrición"""
    return [staff["name"] for staff in CLUB_CONFIG["nutrition_staff"]]

def get_medical_staff_details():
    """Retorna detalles completos del personal médico"""
    return CLUB_CONFIG["medical_staff"]

def get_nutrition_staff_details():
    """Retorna detalles completos del personal de nutrición"""
    return CLUB_CONFIG["nutrition_staff"]

def get_sample_players(division=None):
    """Retorna lista de jugadores de ejemplo"""
    if division:
        return SAMPLE_PLAYERS.get(division, [])
    return SAMPLE_PLAYERS

def get_injury_types():
    """Retorna tipos de lesiones comunes"""
    return INJURY_TYPES

def get_nutrition_plan_types():
    """Retorna tipos de planes nutricionales"""
    return NUTRITION_PLAN_TYPES

def get_common_supplements():
    """Retorna lista de suplementos comunes"""
    return COMMON_SUPPLEMENTS

def get_club_colors():
    """Retorna paleta de colores del club"""
    return CLUB_CONFIG["colors"]

def get_contact_info():
    """Retorna información de contacto del club"""
    return CLUB_CONFIG["contact_info"]

# Configuración del sistema
SYSTEM_CONFIG = {
    "version": "1.0.0",
    "last_updated": "2025-10-08",
    "developer": "Sistema de Digitalización CAR",
    "database_version": "1.0",
    "backup_frequency": "daily",
    "max_file_size": "10MB",
    "supported_formats": ["JSON", "CSV", "PDF"],
    "session_timeout": 3600,  # 1 hora en segundos
    "max_login_attempts": 3,
    "password_requirements": {
        "min_length": 6,
        "require_uppercase": False,
        "require_lowercase": False,
        "require_numbers": False,
        "require_special": False
    }
}

def get_system_config():
    """Retorna configuración del sistema"""
    return SYSTEM_CONFIG

def get_system_version():
    """Retorna versión del sistema"""
    return SYSTEM_CONFIG["version"]

# Configuración de reportes
REPORT_CONFIG = {
    "medical_reports": {
        "weekly_summary": True,
        "monthly_analysis": True,
        "division_breakdown": True,
        "severity_tracking": True
    },
    "nutrition_reports": {
        "plan_compliance": True,
        "supplement_tracking": True,
        "calorie_analysis": True,
        "division_comparison": True
    },
    "export_formats": ["PDF", "Excel", "CSV"],
    "auto_generate": False,
    "email_reports": False
}

def get_report_config():
    """Retorna configuración de reportes"""
    return REPORT_CONFIG

if __name__ == "__main__":
    # Test de las funciones
    print("=== CONFIGURACIÓN CLUB ARGENTINO DE RUGBY ===")
    print(f"Club: {get_club_info()['name']}")
    print(f"Divisiones: {get_divisions()}")
    print(f"Personal Médico: {get_medical_staff()}")
    print(f"Personal Nutrición: {get_nutrition_staff()}")
    print(f"Versión del Sistema: {get_system_version()}")