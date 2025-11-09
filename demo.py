import streamlit as st
from pathlib import Path

# -------------------------
# Config & Constants
# -------------------------
LOGO_PATH = "C:/Users/dell/Desktop/Car/logo.png"  # replace with your logo path if different

COL_BG = "#0B132B"      # Azul Medianoche
COL_ACCENT = "#39FF14"  # Verde Neón
COL_SECOND = "#1E90FF"  # Azul Ciber
COL_WHITE = "#FFFFFF"

st.set_page_config(page_title="SRE - Sistema de Rendimiento Élite", layout="wide", page_icon="⚡")

# -------------------------
# Custom CSS
# -------------------------
st.markdown(f"""
<style>
:root {{
  --bg: {COL_BG};
  --accent: {COL_ACCENT};
  --second: {COL_SECOND};
  --white: {COL_WHITE};
}}

html, body, .stApp {{
  background-color: var(--bg);
  color: var(--white);
}}

/* Header / Hero */
.hero {{
  padding: 40px 0 20px 0;
  text-align: center;
}}
.hero h1 {{
  font-size: 36px;
  margin: 8px 0 4px 0;
}}
.hero p {{
  color: rgba(255,255,255,0.8);
  margin: 0 0 18px 0;
}}

/* CTA */
.btn-cta {{
  background: linear-gradient(90deg, var(--accent), var(--second));
  color: #02121a !important;
  padding: 10px 18px;
  border-radius: 8px;
  font-weight: 700;
  text-decoration: none;
}}

/* Cards */
.card {{
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.04);
  padding: 18px;
  border-radius: 12px;
}}

.metric {{
  background: rgba(255,255,255,0.02);
  padding: 12px;
  border-radius: 8px;
}}

.footer {{
  color: rgba(255,255,255,0.6);
  font-size: 13px;
  padding: 18px 0;
}}

a.stButton > button {{
  background: var(--accent);
  color: #000;
  font-weight: 700;
}}

</style>
""", unsafe_allow_html=True)

# -------------------------
# Utilities
# -------------------------

def load_logo(path: str):
    p = Path(path)
    if p.exists():
        return str(p)
    return None

# -------------------------
# Header / Hero
# -------------------------
logo = load_logo(LOGO_PATH)

with st.container():
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown("""
        <div style="padding: 60px 0 40px 0;">
            <h1 style="font-size: 56px; font-weight: 900; color: white; margin-bottom: 20px; line-height: 1.1;">
                DIGITALIZA TU CLUB<br>
                <span style="color: #39FF14;">TRANSFORMA EL DEPORTE</span>
            </h1>
            <h2 style="font-size: 24px; color: rgba(255,255,255,0.8); margin: 20px 0; font-weight: 300;">
                La plataforma integral que revoluciona la gestión deportiva
            </h2>
            <p style="font-size: 18px; color: rgba(255,255,255,0.7); margin: 30px 0;">
                Capacitamos profesionales y centralizamos datos para una toma de decisiones inteligente
            </p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        if logo:
            st.image(logo, width=500)
        else:
            st.markdown("""
            <div style="background: linear-gradient(45deg, #39FF14, #1E90FF); 
                        width: 500px; height: 500px; border-radius: 20px; 
                        display: flex; align-items: center; justify-content: center; margin: 40px 0;">
                <h2 style="color: #0B132B; font-size: 60px; font-weight: 900;">SRE</h2>
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# -------------------------
# Principios de Digitalización
# -------------------------
st.markdown("""
## 🚀 **Los Principios de la Digitalización Deportiva**

### **1. Capacitación Profesional**
La digitalización exitosa comienza con profesionales capacitados. Nuestro sistema no solo te da las herramientas, 
sino que **forma a tu equipo** para maximizar el potencial de cada dato recopilado.

### **2. Centralización de Información**
Todos los datos en un solo lugar: rendimiento físico, análisis técnico, bienestar del jugador y métricas de salud. 
La **centralización** elimina silos de información y permite una visión integral del atleta.

### **3. Toma de Decisiones Basada en Datos**
Con información centralizada y profesionales capacitados, las decisiones dejan de ser intuitivas para convertirse en 
**estratégicas y fundamentadas**. Cada cambio de entrenamiento, cada rotación, cada plan nutricional tiene respaldo científico.
""")

st.markdown("---")

# -------------------------
# Modules Section (Cards)
# -------------------------
st.subheader("Módulos Principales")
cols = st.columns(4)
modules = [
    ("Rendimiento Físico", "Datos GPS: distancia, sprints, aceleraciones"),
    ("Eventos Técnicos", "Contactos, kicks, scrums por sesión"),
    ("Bienestar", "Wellness, sueño, dolores y carga subjetiva"),
    ("Comparativo", "Benchmarks y alertas por tendencia")
]
for col, mod in zip(cols, modules):
    with col:
        st.markdown(f"<div class=\"card\"><h4>{mod[0]}</h4><p style='color:rgba(255,255,255,0.7)'>{mod[1]}</p><hr><button style='background:{COL_ACCENT}; padding:8px 10px; border-radius:8px;'>Abrir</button></div>", unsafe_allow_html=True)

st.markdown("---")

# -------------------------
# Beneficios de la Digitalización
# -------------------------
st.markdown("""
## 💡 **¿Por qué digitalizar tu club deportivo?**

### **📈 Mejora del Rendimiento**
- **Monitoreo en tiempo real** de métricas clave de cada atleta
- **Prevención de lesiones** mediante análisis predictivo
- **Optimización de entrenamientos** basada en datos objetivos

### **🎯 Ventaja Competitiva**
- **Decisiones estratégicas** respaldadas por información precisa
- **Identificación de talentos** mediante análisis de rendimiento
- **Planificación táctica** con base en datos históricos y actuales

### **⚡ Eficiencia Operativa**
- **Reducción de costos** en lesiones y tiempo perdido
- **Automatización** de reportes y seguimiento
- **Integración** de todas las áreas del club en una plataforma
""")

st.markdown("---")

# -------------------------
# Contact / Request Demo
# -------------------------
st.subheader("Solicitar Demo")
with st.form(key='demo_form'):
    name = st.text_input('Nombre / Club')
    email = st.text_input('Email')
    message = st.text_area('Mensaje (qué querés ver en la demo)')
    submitted = st.form_submit_button('Enviar solicitud')
    if submitted:
        st.success('Gracias — tu solicitud fue enviada. Nos comunicamos por email para coordinar la demo.')

# -------------------------
# Footer
# -------------------------
st.markdown('<div class="footer">SRE — Sistema de Rendimiento Élite • Diseño: SRE Visual • © 2025</div>', unsafe_allow_html=True)
