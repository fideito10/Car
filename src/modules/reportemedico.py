"""
Módulo de Reportes Médicos - Club Argentino de Rugby (CAR)
Interfaz de consulta para doctores - Solo lectura
Unión de datos: Base Central + Área Médica por DNI
"""


import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# =============================================================================
# 🔧 FUNCIONES AUXILIARES CORREGIDAS
# =============================================================================

def get_google_credentials():
    """Obtener credenciales de Google desde secrets con validación"""
    try:
        # 🔍 Verificar si existen las credenciales
        if "google_credentials" not in st.secrets:
            st.error("❌ No se encontraron credenciales de Google en secrets.toml")
            st.info("📝 Verifica que el archivo secrets.toml contenga la sección [google_credentials]")
            return None
            
        creds = st.secrets["google_credentials"]
        
        # 🔍 Verificar campos obligatorios
        required_fields = ["type", "project_id", "private_key_id", "private_key", "client_email", "client_id", "auth_uri", "token_uri"]
        missing_fields = [field for field in required_fields if field not in creds]
        
        if missing_fields:
            st.error(f"❌ Faltan campos en credenciales: {missing_fields}")
            return None
            
        st.success("✅ Credenciales de Google cargadas correctamente")
        return dict(creds)
        
    except Exception as e:
        st.error(f"❌ Error cargando credenciales: {str(e)}")
        return None

def conectar_base_central():
    """Conectar a Base Central - puede ser una hoja diferente"""
    try:
        st.info("🔄 Conectando a Base Central...")
        from areamedica import read_google_sheet_with_headers

        # Usar el ID correcto de la hoja base de jugadores
        result = read_google_sheet_with_headers(
            sheet_id='1LW8nlaIdJ_6bCnrqpMJW5X27Dhr78gRnhLHwKj6DV7E',
            worksheet_name=None  # usar primera hoja o especifica si es necesario
        )
        if not result or not result.get('success'):
            error_msg = result.get('error', 'Error desconocido') if result else 'Sin respuesta'
            st.error(f"❌ Error conectando a Base Central: {error_msg}")
            return []

        data = result.get('data', [])

        if not data:
            st.warning("⚠️ Base Central sin datos")
            return []

        # Procesar datos para formato de jugadores
        jugadores = []
        for registro in data:
            # Unir Nombre y Apellido para el campo 'nombre'
            if 'Nombre' in registro and 'Apellido' in registro:
                nombre = (registro.get('Nombre', '').strip() + ' ' + registro.get('Apellido', '').strip()).strip()
            else:
                nombre = registro.get('Nombre y Apellido', '').strip()
            jugador = {
                'nombre': nombre,
                'dni': str(registro.get('DNI', registro.get('dni', ''))).strip(),
                'categoria': registro.get('Categoria', registro.get('categoria', registro.get('División', 'Sin Categoría'))).strip(),
                'posicion': registro.get('Posición', registro.get('posicion', '')).strip(),
                'estado': registro.get('Estado', registro.get('estado', 'Activo')).strip(),
                'telefono': registro.get('Teléfono', registro.get('telefono', '')).strip(),
                'email': registro.get('Email', registro.get('email', '')).strip()
            }
            if jugador['nombre'] and jugador['dni']:
                jugadores.append(jugador)

        st.success(f"✅ Base Central cargada: {len(jugadores)} jugadores válidos de {len(data)} registros totales")
        return jugadores

    except ImportError:
        st.error("❌ No se puede importar areamedica.py")
        return []
    except Exception as e:
        st.error(f"❌ Error en conectar_base_central: {str(e)}")
        return []

def normalizar_categoria(cat):
    """Normaliza el nombre de la categoría para evitar duplicados por mayúsculas/minúsculas y espacios."""
    if not cat:
        return "Sin Categoría"
    return cat.strip().upper() 
    
def conectar_area_medica():
    """Conectar a Área Médica con manejo mejorado de errores"""
    try:
        st.info("🏥 Conectando a Área Médica...")
        
        try:
            from areamedica import read_google_sheet_with_headers
            st.success("✅ Módulo de Área Médica encontrado")
        except ImportError:
            st.warning("⚠️ Módulo areamedica.py no encontrado - Continuando sin datos médicos")
            return []
        
        # Usar el ID correcto de la hoja de historial clínico
        result = read_google_sheet_with_headers(
            sheet_id='1zGyW-M_VV7iyDKVB1TTd0EEP3QBjdoiBmSJN2tK-H7w',
            worksheet_name=None  # usa la primera hoja o especifica si es necesario
        )
        
        if not result:
            st.warning("⚠️ Sin respuesta del módulo médico")
            return []
        
        if not result.get('success'):
            error_msg = result.get('error', 'Error desconocido')
            st.warning(f"⚠️ Error en Área Médica: {error_msg}")
            return []
        
        medical_data = result.get('data', [])
        st.success(f"✅ Área Médica: {len(medical_data)} registros cargados")
        return medical_data
            
    except Exception as e:
        st.warning(f"⚠️ Área Médica no disponible: {e}")
        return []

# AGREGAR ESTAS FUNCIONES QUE FALTAN:

def normalizar_dni(dni):
    """Normalizar DNI para comparación"""
    if not dni:
        return ""
    return str(dni).replace('.', '').replace('-', '').replace(' ', '').strip()

def obtener_historial_por_dni(dni, datos_medicos):
    """Obtener historial médico por DNI"""
    dni_normalizado = normalizar_dni(dni)
    if not dni_normalizado:
        return []
    
    historial = []
    for registro in datos_medicos:
        dni_registro = normalizar_dni(registro.get('DNI', registro.get('Dni', '')))
        if dni_registro and dni_registro == dni_normalizado:
            historial.append(registro)
    
    # Ordenar por fecha (más reciente primero)
    historial.sort(
        key=lambda x: x.get('Fecha de Atención', x.get('Marca temporal', '1900-01-01')),
        reverse=True
    )
    return historial

def diagnosticar_sistema():
    """Función de diagnóstico completo del sistema"""
    st.markdown("## 🔧 **Diagnóstico del Sistema**")
    
    # 1. Verificar secrets
    st.markdown("### 1. 📋 Verificación de Secrets")
    try:
        if hasattr(st, 'secrets'):
            st.success("✅ st.secrets disponible")
            
            if "google_credentials" in st.secrets:
                st.success("✅ google_credentials encontradas en secrets")
                
                # Verificar campos
                creds = st.secrets["google_credentials"]
                required_fields = ["type", "project_id", "private_key", "client_email"]
                missing = [f for f in required_fields if f not in creds]
                
                if not missing:
                    st.success("✅ Todos los campos obligatorios presentes")
                else:
                    st.error(f"❌ Campos faltantes: {missing}")
                    
            else:
                st.error("❌ google_credentials NO encontradas en secrets")
        else:
            st.error("❌ st.secrets no disponible")
    except Exception as e:
        st.error(f"❌ Error verificando secrets: {e}")
    
    # 2. Verificar librerías
    st.markdown("### 2. 📚 Verificación de Librerías")
    try:
        import gspread
        st.success("✅ gspread instalado")
    except ImportError:
        st.error("❌ gspread NO instalado")
        st.error("💡 Ejecuta: pip install gspread")
    
    try:
        from google.oauth2.service_account import Credentials
        st.success("✅ google-auth instalado")
    except ImportError:
        st.error("❌ google-auth NO instalado")
        st.error("💡 Ejecuta: pip install google-auth google-auth-oauthlib")
    
    # 3. Verificar módulos locales
    st.markdown("### 3. 🏥 Verificación de Módulos")
    try:
        from areamedica import read_google_sheet_with_headers
        st.success("✅ Módulo areamedica disponible")
    except ImportError:
        st.warning("⚠️ Módulo areamedica NO disponible")
    
    # 4. Test de conexión básica
    st.markdown("### 4. 🌐 Test de Conexión")
    if st.button("🧪 Probar Conexión a Google Sheets"):
        with st.spinner("Probando conexión..."):
            jugadores = conectar_base_central()
            if jugadores:
                st.success(f"✅ Conexión exitosa: {len(jugadores)} jugadores cargados")
                
                # Mostrar muestra
                st.markdown("**🔍 Muestra de datos:**")
                for i, jugador in enumerate(jugadores[:3]):
                    st.write(f"{i+1}. {jugador['nombre']} - {jugador['categoria']} - DNI: {jugador['dni']}")
            else:
                st.error("❌ Conexión fallida")

def main_reporte_medico():
    """Función principal - Interfaz simplificada con diagnóstico"""
    
    # 🎨 CSS personalizado
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #1e3c72, #2a5298);
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
    }
    .filter-container {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        border-left: 5px solid #2a5298;
    }
    .resumen-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 5px solid #28a745;
    }
    .stat-card {
        background: linear-gradient(135deg, #28a745, #20c997);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 🏥 Header principal
    st.markdown("""
    <div class="main-header">
        <h1>🏥 Consulta Médica</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # 🔧 Botón de diagnóstico
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔧 Diagnóstico", help="Verificar configuración del sistema"):
            diagnosticar_sistema()
            st.stop()
    
        # 📊 Cargar datos con mejor feedback
    with st.spinner("🔄 Cargando datos del sistema..."):
        jugadores = conectar_base_central()
        datos_medicos = conectar_area_medica()

    # 👀 Mostrar DataFrames para inspección
    st.markdown("### 👀 **Vista previa de datos de jugadores**")
    if jugadores:
        st.dataframe(pd.DataFrame(jugadores))
    else:
        st.warning("No se encontraron datos de jugadores.")

    st.markdown("### 👀 **Vista previa de historial médico**")
    if datos_medicos:
        st.dataframe(pd.DataFrame(datos_medicos))
    else:
        st.warning("No se encontraron datos médicos.")
    
    # 🎯 Resto de la interfaz (sin cambios)...
    # [El resto del código sigue igual desde aquí]
    
       # 🔍 FILTROS PRINCIPALES
    st.markdown('<div class="filter-container">', unsafe_allow_html=True)
    st.markdown("### 🔍 **Filtros de Búsqueda**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 📂 Filtro por categoría (mezcla jugadores y datos médicos)
        categorias_jugadores = [
            normalizar_categoria(j.get('categoria', j.get('Categoria', j.get('División', 'Sin Categoría')))
            ) for j in jugadores if j.get('categoria') or j.get('Categoria') or j.get('División')
        ]
        categorias_medicas = [
            normalizar_categoria(r.get('Categoria', r.get('categoria', r.get('División', 'Sin Categoría')))
            ) for r in datos_medicos if r.get('Categoria') or r.get('categoria') or r.get('División')
        ]
        categorias_disponibles = sorted(list(set(categorias_jugadores + categorias_medicas)))
        categoria_seleccionada = st.selectbox(
            "**📂 Categoría:**",
            options=['Todas'] + categorias_disponibles,
            key="filtro_categoria"
        )
        
    with col2:
        # 👤 Filtro por nombre (solo jugadores de la categoría seleccionada)
        if categoria_seleccionada != 'Todas':
            registros_categoria = [
                r for r in datos_medicos
                if normalizar_categoria(r.get('Categoria', r.get('categoria', r.get('División', 'Sin Categoría'))) ) == categoria_seleccionada
            ]
        else:
            registros_categoria = datos_medicos

        nombres_disponibles = sorted(list(set([
            registro.get('Nombre y Apellido', f"{registro.get('Nombre', '').strip()} {registro.get('Apellido', '').strip()}").strip()
            for registro in registros_categoria if registro.get('Nombre') or registro.get('Nombre y Apellido')
        ])))
        jugador_seleccionado = st.selectbox(
            "**👤 Nombre y Apellido:**",
            options=['Seleccionar jugador...'] + nombres_disponibles,
            key="filtro_jugador"
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 🎯 Filtrar registros médicos según selección
    registros_filtrados = datos_medicos
    
    # Filtrar por categoría
    if categoria_seleccionada != 'Todas':
        registros_filtrados = [
            r for r in registros_filtrados
            if r.get('Categoria', r.get('categoria', r.get('División', 'Sin Categoría'))) == categoria_seleccionada
        ]
    
    # Encontrar jugador específico
    jugador_actual = None
    if jugador_seleccionado != 'Seleccionar jugador...':
        for registro in registros_filtrados:
            nombre_registro = registro.get('Nombre y Apellido', f"{registro.get('Nombre', '').strip()} {registro.get('Apellido', '').strip()}").strip()
            if nombre_registro == jugador_seleccionado:
                jugador_actual = registro
                break
    
 # ...existing code...
    if jugador_actual:
        # 📊 Obtener historial médico
        dni_jugador = jugador_actual.get('DNI', jugador_actual.get('Dni', '')).strip()
        historial_medico = obtener_historial_por_dni(dni_jugador, datos_medicos)
        
        st.markdown('<div class="resumen-card">', unsafe_allow_html=True)
        
        # 👤 Información básica del jugador
        nombre_jugador = jugador_actual.get('Nombre y Apellido', f"{jugador_actual.get('Nombre', '').strip()} {jugador_actual.get('Apellido', '').strip()}").strip()
        categoria_jugador = jugador_actual.get('Categoria', jugador_actual.get('categoria', jugador_actual.get('División', 'Sin Categoría')))
        posicion_jugador = jugador_actual.get('Posición', jugador_actual.get('posicion', '')).strip()
        estado_jugador = jugador_actual.get('Estado', jugador_actual.get('estado', 'Activo')).strip()
        telefono_jugador = jugador_actual.get('Teléfono', jugador_actual.get('telefono', '')).strip()
        email_jugador = jugador_actual.get('Email', jugador_actual.get('email', '')).strip()
        
        st.markdown(f"## 👤 **{nombre_jugador}**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            **🆔 DNI:** {dni_jugador}  
            **🏉 Categoría:** {categoria_jugador}  
            **⚽ Posición:** {posicion_jugador}
            """)
        
        with col2:
            estado_emoji = "🟢" if estado_jugador == 'Activo' else "🔴"
            st.markdown(f"""
            **📊 Estado:** {estado_emoji} {estado_jugador}  
            **📞 Teléfono:** {telefono_jugador}  
            **📧 Email:** {email_jugador}
            """)

        
        with col3:
            # Estadísticas rápidas del historial
            total_registros = len(historial_medico)
            registros_2024 = len([h for h in historial_medico if '2024' in str(h.get('Fecha de Atención', h.get('Marca temporal', '')))])
            lesiones_graves = len([h for h in historial_medico if 'alta' in str(h.get('Severidad de la Lesión', '')).lower() or 'grave' in str(h.get('Severidad de la Lesión', '')).lower()])
            
            st.markdown(f"""
            <div class="stat-card">
                <h3>📋 {total_registros}</h3>
                <p>Registros Médicos</p>
            </div>
            
            <div class="stat-card">
                <h3>📅 {registros_2024}</h3>
                <p>En 2024</p>
            </div>
            
            <div class="stat-card">
                <h3>⚠️ {lesiones_graves}</h3>
                <p>Lesiones Graves</p>
            </div>
            """, unsafe_allow_html=True)
        
        # 🏥 Mostrar historial si existe
        if historial_medico:
            st.markdown("---")
            st.markdown("### 🏥 **Resumen de Historia Clínica**")
            
            # Mostrar último registro
            ultimo_registro = historial_medico[0]
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 📊 **Estado Actual**")
                puede_entrenar = ultimo_registro.get('¿Puede participar en entrenamientos?', 'No especificado')
                
                if 'sí' in puede_entrenar.lower():
                    st.success(f"✅ Puede entrenar: {puede_entrenar}")
                elif 'no' in puede_entrenar.lower():
                    st.error(f"❌ No puede entrenar: {puede_entrenar}")
                else:
                    st.warning(f"❓ Estado incierto: {puede_entrenar}")
                
                st.markdown(f"**🩺 Último Diagnóstico:** {ultimo_registro.get('Tipo de Lesión', 'Sin diagnóstico')}")
                st.markdown(f"**📅 Última Consulta:** {ultimo_registro.get('Fecha de Atención', ultimo_registro.get('Marca temporal', 'Sin fecha'))}")
            
            with col2:
                st.markdown("#### 📋 **Historial Resumido**")
                st.markdown(f"**Total de registros:** {len(historial_medico)}")
                
                # Lesiones más frecuentes
                lesiones = [h.get('Tipo de Lesión', '') for h in historial_medico if h.get('Tipo de Lesión')]
                if lesiones:
                    lesion_mas_frecuente = max(set(lesiones), key=lesiones.count)
                    st.markdown(f"**Lesión más frecuente:** {lesion_mas_frecuente}")
            
            # Mostrar registros expandibles
            st.markdown("#### 📋 **Registros Detallados**")
            
            for i, registro in enumerate(historial_medico[:3]):  # Solo los 3 más recientes
                fecha = registro.get('Fecha de Atención', registro.get('Marca temporal', 'Sin fecha'))
                diagnostico = registro.get('Tipo de Lesión', 'Sin diagnóstico')
                
                with st.expander(f"📄 {i+1}. {fecha} - {diagnostico}", expanded=(i==0)):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"""
                        **👨‍⚕️ Doctor:** {registro.get('Nombre del Doctor', 'No especificado')}  
                        **🩺 Diagnóstico:** {diagnostico}  
                        **⚠️ Severidad:** {registro.get('Severidad de la Lesión', 'No especificada')}  
                        **🎯 Parte Afectada:** {registro.get('Parte del Cuerpo Afectada', 'No especificada')}
                        """)
                    
                    with col2:
                        st.markdown(f"""
                        **🏃‍♂️ Puede Entrenar:** {registro.get('¿Puede participar en entrenamientos?', 'No especificado')}  
                        **🔪 Requiere Cirugía:** {registro.get('¿Requiere Cirugía?', 'No especificado')}  
                        **📅 Próx. Evaluación:** {registro.get('Fecha de Próxima Evaluación', 'No programada')}  
                        **📊 Estado Caso:** {registro.get('Estado del Caso', 'No especificado')}
                        """)
                    
                    if registro.get('Tratamiento Prescrito'):
                        st.markdown(f"**💊 Tratamiento:** {registro['Tratamiento Prescrito']}")
                    
                    if registro.get('Observaciones Adicionales'):
                        st.markdown(f"**📝 Observaciones:** {registro['Observaciones Adicionales']}")
        
        else:
            st.info("📋 **Sin registros médicos previos** - Jugador sin historial clínico registrado")
        
        st.markdown('</div>', unsafe_allow_html=True)
    

    else:
        # 📋 Mostrar lista de jugadores disponibles
        if categoria_seleccionada != 'Todas':
            st.markdown(f"### 👥 Jugadores en **{categoria_seleccionada}** ({len(registros_filtrados)} total)")
        else:
            st.markdown(f"### 👥 Todos los Jugadores ({len(registros_filtrados)} total)")
        
        # Mostrar lista organizada
# ...existing code...
        for registro in registros_filtrados[:10]:  # Mostrar solo los primeros 10
            nombre = registro.get('Nombre y Apellido', f"{registro.get('Nombre', '').strip()} {registro.get('Apellido', '').strip()}").strip()
            dni = registro.get('DNI', registro.get('Dni', '')).strip()
            categoria = registro.get('Categoria', registro.get('categoria', registro.get('División', 'Sin Categoría')))
            estado = registro.get('Estado', registro.get('estado', 'Activo')).strip()
            historial_count = len(obtener_historial_por_dni(dni, datos_medicos))
            historial_emoji = "🏥" if historial_count > 0 else "👤"
            estado_emoji = "🟢" if estado == 'Activo' else "🔴"
            
            st.markdown(f"""
            **{historial_emoji} {estado_emoji} {nombre}**  
            📂 {categoria} | 🆔 {dni} | 📋 {historial_count} registros médicos
            """)
# ...existing code...
        
        if len(registros_filtrados) > 10:
            st.info(f"... y {len(registros_filtrados) - 10} jugadores más. Selecciona uno para ver detalles.")

    # Footer informativo
    st.markdown("---")
    st.caption("📊 **Fuentes de datos:** Base Central (jugadores) + Área Médica (historiales) | 🔄 Actualización en tiempo real")

# Ejecutar si es llamado directamente
if __name__ == "__main__":
    main_reporte_medico()