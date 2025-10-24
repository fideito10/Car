"""
Utilidades y funciones auxiliares para el sistema CAR
Funciones de exportación, validación y helpers
"""

import json
import pandas as pd
from datetime import datetime, date
import streamlit as st
from typing import Dict, List, Any
import hashlib
import os

class DataExporter:
    """Clase para exportar datos del sistema"""
    
    @staticmethod
    def export_medical_data(injuries: List[Dict], format_type: str = "csv") -> str:
        """Exportar datos médicos"""
        df = pd.DataFrame(injuries)
        
        if format_type.lower() == "csv":
            return df.to_csv(index=False)
        elif format_type.lower() == "json":
            return df.to_json(orient="records", indent=2)
        elif format_type.lower() == "excel":
            # Para Excel necesitaríamos usar BytesIO
            return df.to_excel(index=False)
        else:
            raise ValueError(f"Formato {format_type} no soportado")
    
    @staticmethod
    def export_nutrition_data(nutrition_data: Dict, format_type: str = "csv") -> str:
        """Exportar datos nutricionales"""
        meal_plans = pd.DataFrame(nutrition_data.get('meal_plans', []))
        supplements = pd.DataFrame(nutrition_data.get('supplements', []))
        
        if format_type.lower() == "csv":
            return {
                "meal_plans": meal_plans.to_csv(index=False),
                "supplements": supplements.to_csv(index=False)
            }
        elif format_type.lower() == "json":
            return json.dumps(nutrition_data, indent=2)
        else:
            raise ValueError(f"Formato {format_type} no soportado")

class DataValidator:
    """Clase para validar datos de entrada"""
    
    @staticmethod
    def validate_injury_data(injury_data: Dict) -> tuple[bool, str]:
        """Validar datos de lesión"""
        required_fields = ['player_name', 'division', 'injury_type', 'severity']
        
        for field in required_fields:
            if not injury_data.get(field):
                return False, f"Campo requerido faltante: {field}"
        
        # Validar fechas
        try:
            if injury_data.get('date_occurred'):
                datetime.fromisoformat(injury_data['date_occurred'])
            if injury_data.get('expected_recovery'):
                datetime.fromisoformat(injury_data['expected_recovery'])
        except ValueError:
            return False, "Formato de fecha inválido"
        
        # Validar severidad
        valid_severities = ['Leve', 'Moderada', 'Grave']
        if injury_data['severity'] not in valid_severities:
            return False, f"Severidad debe ser una de: {valid_severities}"
        
        return True, "Datos válidos"
    
    @staticmethod
    def validate_nutrition_data(nutrition_data: Dict) -> tuple[bool, str]:
        """Validar datos nutricionales"""
        required_fields = ['player_name', 'division', 'plan_type', 'calories_target']
        
        for field in required_fields:
            if not nutrition_data.get(field):
                return False, f"Campo requerido faltante: {field}"
        
        # Validar valores numéricos
        numeric_fields = ['calories_target', 'protein_target', 'carbs_target', 'fat_target']
        for field in numeric_fields:
            value = nutrition_data.get(field)
            if value is not None and (not isinstance(value, (int, float)) or value < 0):
                return False, f"Campo {field} debe ser un número positivo"
        
        return True, "Datos válidos"
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validar formato de email"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

class ReportGenerator:
    """Clase para generar reportes"""
    
    @staticmethod
    def generate_medical_summary(injuries: List[Dict]) -> Dict:
        """Generar resumen médico"""
        if not injuries:
            return {"error": "No hay datos de lesiones"}
        
        df = pd.DataFrame(injuries)
        
        summary = {
            "total_injuries": len(injuries),
            "active_injuries": len(df[df['status'] == 'En recuperación']),
            "recovered": len(df[df['status'] == 'Recuperado']),
            "by_division": df['division'].value_counts().to_dict(),
            "by_severity": df['severity'].value_counts().to_dict(),
            "by_type": df['injury_type'].value_counts().to_dict(),
            "average_recovery_days": 0,  # Calcular cuando tengamos fechas reales
            "most_common_injury": df['injury_type'].mode().iloc[0] if not df.empty else "N/A"
        }
        
        return summary
    
    @staticmethod
    def generate_nutrition_summary(nutrition_data: Dict) -> Dict:
        """Generar resumen nutricional"""
        meal_plans = nutrition_data.get('meal_plans', [])
        supplements = nutrition_data.get('supplements', [])
        
        if not meal_plans:
            return {"error": "No hay datos nutricionales"}
        
        df_plans = pd.DataFrame(meal_plans)
        
        summary = {
            "total_plans": len(meal_plans),
            "total_supplements": len(supplements),
            "average_calories": df_plans['calories_target'].mean() if 'calories_target' in df_plans.columns else 0,
            "average_protein": df_plans['protein_target'].mean() if 'protein_target' in df_plans.columns else 0,
            "by_division": df_plans['division'].value_counts().to_dict() if 'division' in df_plans.columns else {},
            "by_plan_type": df_plans['plan_type'].value_counts().to_dict() if 'plan_type' in df_plans.columns else {},
            "most_common_plan": df_plans['plan_type'].mode().iloc[0] if not df_plans.empty and 'plan_type' in df_plans.columns else "N/A"
        }
        
        return summary

class SecurityHelper:
    """Clase para funciones de seguridad"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Encriptar contraseña"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verificar contraseña"""
        return SecurityHelper.hash_password(password) == hashed_password
    
    @staticmethod
    def generate_session_token() -> str:
        """Generar token de sesión"""
        import secrets
        return secrets.token_hex(32)
    
    @staticmethod
    def is_safe_filename(filename: str) -> bool:
        """Verificar si el nombre de archivo es seguro"""
        import re
        # Solo letras, números, guiones y puntos
        pattern = r'^[a-zA-Z0-9._-]+$'
        return re.match(pattern, filename) is not None

class DateHelper:
    """Clase para funciones de fecha y tiempo"""
    
    @staticmethod
    def format_date(date_string: str, format_type: str = "display") -> str:
        """Formatear fecha"""
        try:
            date_obj = datetime.fromisoformat(date_string)
            if format_type == "display":
                return date_obj.strftime("%d/%m/%Y")
            elif format_type == "full":
                return date_obj.strftime("%d/%m/%Y %H:%M")
            elif format_type == "short":
                return date_obj.strftime("%d/%m")
            else:
                return date_string
        except:
            return date_string
    
    @staticmethod
    def days_between(start_date: str, end_date: str) -> int:
        """Calcular días entre fechas"""
        try:
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            return (end - start).days
        except:
            return 0
    
    @staticmethod
    def is_future_date(date_string: str) -> bool:
        """Verificar si una fecha es futura"""
        try:
            date_obj = datetime.fromisoformat(date_string)
            return date_obj > datetime.now()
        except:
            return False

class UIHelper:
    """Clase para funciones de interfaz de usuario"""
    
    @staticmethod
    def create_metric_card(title: str, value: str, delta: str = None, color: str = "blue") -> str:
        """Crear tarjeta de métrica HTML"""
        color_map = {
            "blue": "#1A2C56",
            "green": "#28a745",
            "red": "#dc3545",
            "yellow": "#ffc107"
        }
        
        bg_color = color_map.get(color, "#1A2C56")
        
        delta_html = ""
        if delta:
            delta_html = f'<p style="margin: 0.5rem 0 0 0; font-size: 0.9rem; opacity: 0.8;">{delta}</p>'
        
        return f"""
        <div style="background: linear-gradient(135deg, {bg_color}, #6BB4E8); 
                   padding: 1.5rem; border-radius: 10px; color: white; 
                   text-align: center; margin: 0.5rem 0;">
            <h3 style="margin: 0; font-size: 2.5rem; font-weight: 700;">{value}</h3>
            <p style="margin: 0.5rem 0 0 0; font-size: 1rem; opacity: 0.9;">{title}</p>
            {delta_html}
        </div>
        """
    
    @staticmethod
    def create_info_card(title: str, content: str, icon: str = "📋") -> str:
        """Crear tarjeta de información"""
        return f"""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; 
                   box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin: 1rem 0; 
                   border-left: 4px solid #6BB4E8;">
            <h3 style="margin: 0 0 1rem 0; color: #1A2C56;">{icon} {title}</h3>
            <div>{content}</div>
        </div>
        """
    
    @staticmethod
    def create_alert(message: str, alert_type: str = "info") -> str:
        """Crear alerta HTML"""
        color_map = {
            "info": {"bg": "#d1ecf1", "border": "#bee5eb", "text": "#0c5460"},
            "success": {"bg": "#d4edda", "border": "#c3e6cb", "text": "#155724"},
            "warning": {"bg": "#fff3cd", "border": "#ffeaa7", "text": "#856404"},
            "danger": {"bg": "#f8d7da", "border": "#f5c6cb", "text": "#721c24"}
        }
        
        colors = color_map.get(alert_type, color_map["info"])
        
        return f"""
        <div style="background-color: {colors['bg']}; border: 1px solid {colors['border']}; 
                   color: {colors['text']}; padding: 0.75rem 1.25rem; margin-bottom: 1rem; 
                   border-radius: 0.25rem;">
            {message}
        </div>
        """

class CalculatorHelper:
    """Clase para cálculos nutricionales y médicos"""
    
    @staticmethod
    def calculate_bmr(weight: float, height: float, age: int, gender: str = "male") -> float:
        """Calcular Tasa Metabólica Basal"""
        if gender.lower() == "male":
            return 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
        else:
            return 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
    
    @staticmethod
    def calculate_tdee(bmr: float, activity_level: str) -> float:
        """Calcular Gasto Energético Total Diario"""
        activity_factors = {
            "sedentario": 1.2,
            "ligero": 1.375,
            "moderado": 1.55,
            "intenso": 1.725,
            "muy_intenso": 1.9
        }
        
        factor = activity_factors.get(activity_level.lower(), 1.55)
        return bmr * factor
    
    @staticmethod
    def calculate_macros(calories: float, protein_pct: float = 20, carbs_pct: float = 50) -> Dict:
        """Calcular macronutrientes"""
        fat_pct = 100 - protein_pct - carbs_pct
        
        return {
            "protein_g": (calories * protein_pct / 100) / 4,
            "carbs_g": (calories * carbs_pct / 100) / 4,
            "fat_g": (calories * fat_pct / 100) / 9,
            "protein_pct": protein_pct,
            "carbs_pct": carbs_pct,
            "fat_pct": fat_pct
        }
    
    @staticmethod
    def calculate_bmi(weight: float, height: float) -> Dict:
        """Calcular Índice de Masa Corporal"""
        height_m = height / 100
        bmi = weight / (height_m ** 2)
        
        if bmi < 18.5:
            category = "Bajo peso"
        elif bmi < 25:
            category = "Normal"
        elif bmi < 30:
            category = "Sobrepeso"
        else:
            category = "Obesidad"
        
        return {
            "bmi": round(bmi, 2),
            "category": category
        }

def load_json_data(filename: str, default_data: Any = None) -> Any:
    """Cargar datos desde archivo JSON"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        if default_data is not None:
            save_json_data(filename, default_data)
            return default_data
        return {}
    except json.JSONDecodeError:
        return default_data if default_data is not None else {}

def save_json_data(filename: str, data: Any) -> bool:
    """Guardar datos en archivo JSON"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Error al guardar {filename}: {e}")
        return False

def backup_data(source_file: str, backup_dir: str = "backups") -> bool:
    """Crear backup de archivo de datos"""
    try:
        import shutil
        from pathlib import Path
        
        # Crear directorio de backup si no existe
        Path(backup_dir).mkdir(exist_ok=True)
        
        # Crear nombre de backup con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{Path(source_file).stem}_{timestamp}.json"
        backup_path = Path(backup_dir) / backup_name
        
        # Copiar archivo
        shutil.copy2(source_file, backup_path)
        return True
    except Exception as e:
        st.error(f"Error al crear backup: {e}")
        return False

# Decoradores útiles
def require_authentication(func):
    """Decorador para requerir autenticación"""
    def wrapper(*args, **kwargs):
        if not st.session_state.get('authenticated', False):
            st.error("🔒 Debe iniciar sesión para acceder a esta función")
            st.stop()
        return func(*args, **kwargs)
    return wrapper

def log_action(action_name: str):
    """Decorador para registrar acciones del usuario"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                # Aquí podrías agregar logging real
                # logger.info(f"Usuario {st.session_state.get('username')} ejecutó {action_name}")
                return result
            except Exception as e:
                # logger.error(f"Error en {action_name}: {e}")
                raise e
        return wrapper
    return decorator

if __name__ == "__main__":
    # Tests de las funciones de utilidad
    print("=== TESTS DE UTILIDADES CAR ===")
    
    # Test de validación
    injury_data = {
        "player_name": "Test Player",
        "division": "Primera",
        "injury_type": "Test Injury",
        "severity": "Leve"
    }
    is_valid, message = DataValidator.validate_injury_data(injury_data)
    print(f"Validación de lesión: {is_valid} - {message}")
    
    # Test de cálculos
    bmr = CalculatorHelper.calculate_bmr(80, 180, 25)
    print(f"BMR calculado: {bmr}")
    
    # Test de hash
    password_hash = SecurityHelper.hash_password("test123")
    print(f"Hash de contraseña: {password_hash[:20]}...")
    
    print("Tests completados exitosamente")

def save_medical_data(medical_data: List[Dict]) -> bool:
    """Guardar datos médicos en archivo JSON"""
    try:
        data = {
            "injuries": medical_data,
            "last_updated": datetime.now().isoformat(),
            "total_injuries": len(medical_data)
        }
        return save_json_data('data/medical_records.json', data)
    except Exception as e:
        st.error(f"Error al guardar datos médicos: {e}")
        return False

def save_nutrition_data(nutrition_data: List[Dict]) -> bool:
    """Guardar datos nutricionales en archivo JSON"""
    try:
        data = {
            "meal_plans": nutrition_data,
            "last_updated": datetime.now().isoformat(),
            "total_plans": len(nutrition_data)
        }
        return save_json_data('data/nutrition_records.json', data)
    except Exception as e:
        st.error(f"Error al guardar datos nutricionales: {e}")
        return False

def load_json_data(filename: str, default_data: Any = None) -> Any:
    """Cargar datos desde archivo JSON"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return default_data if default_data is not None else {}
    except Exception as e:
        print(f"Error cargando {filename}: {e}")
        return default_data if default_data is not None else {}

def save_medical_data(medical_data: List[Dict]) -> bool:
    """Guardar datos médicos en archivo JSON"""
    try:
        data = {"injuries": medical_data}
        with open('data/medical_records.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error guardando datos médicos: {e}")
        return False

def save_nutrition_data(nutrition_data: List[Dict]) -> bool:
    """Guardar datos nutricionales en archivo JSON"""
    try:
        with open('data/nutrition_records.json', 'w', encoding='utf-8') as f:
            json.dump(nutrition_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error guardando datos nutricionales: {e}")
        return False

def get_divisions() -> List[str]:
    """Obtener lista de divisiones del club"""
    return [
        "Primera",
        "Reserva", 
        "M21",
        "M19",
        "M17",
        "M15",
        "Femenino",
        "Veteranos",
        "Rugby Infantil",
        "Otra"
    ]