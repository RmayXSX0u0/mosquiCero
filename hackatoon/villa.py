import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse
from gtts import gTTS
import io
import re

# ---------------- CONFIGURACIÓN DE LA API ----------------
GEMINI_API_KEY = "TU_API_KEY" # <--- No olvides poner tu clave aquí
genai.configure(api_key=GEMINI_API_KEY)

# ---------------- CONFIGURACIÓN DE LA PÁGINA ----------------
st.set_page_config(page_title="MosquiCero", page_icon="🦟", layout="centered", initial_sidebar_state="collapsed")

# ---------------- ESTILOS CSS PERSONALIZADOS (Inspirado en MosquiCero) ----------------
st.markdown("""
    <style>
    /* Paleta de colores: Verde azulado, Naranja Coral, Blanco y Grises claros */
    :root {
        --color-primario: #389e93; 
        --color-secundario: #ff8c69; 
        --color-fondo: #fafafa;
        --color-tarjeta: #ffffff;
        --color-texto: #333333;
        --color-borde: #e0e0e0;
    }

    /* Fondo general */
    .stApp {
        background-color: var(--color-fondo);
    }

    /* Estilo del Header/Logo */
    .header-logo {
        color: var(--color-primario);
        font-family: 'Arial Black', sans-serif;
        font-size: 2.5rem;
        margin-bottom: -10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .badge-demo {
        font-size: 0.8rem;
        font-weight: normal;
        color: #888;
        background-color: #eee;
        padding: 4px 10px;
        border-radius: 12px;
        border: 1px solid #ccc;
    }

    /* Estilo de los Tabs (Pestañas) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        border-bottom: 2px solid var(--color-borde);
    }
    .stTabs [data-baseweb="tab"] {
        height: 60px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 0px 0px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        color: #777;
    }
    .stTabs [aria-selected="true"] {
        border-bottom: 3px solid var(--color-secundario) !important;
        color: var(--color-secundario) !important;
        font-weight: bold;
    }

    /* Tarjetas tipo contenedor blanco */
    .contenedor-blanco {
        background-color: var(--color-tarjeta);
        border: 1px solid var(--color-borde);
        border-radius: 12px;
        padding: 30px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        margin-top: 20px;
    }

    /* Botón Principal (Analizar Fotografía) */
    .stButton>button {
        background-color: var(--color-primario) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        font-weight: bold !important;
        width: 100% !important;
        margin-top: 15px !important;
    }
    .stButton>button:hover {
        background-color: #2b7a72 !important;
    }

    /* Estilos para el texto de resultados */
    .pokedex-card {
        background-color: #f8fbfb;
        border-radius: 12px;
        padding: 20px;
        border-left: 6px solid var(--color-secundario);
        margin-top: 20px;
        margin-bottom: 15px;
        color: var(--color-texto);
        text-align: left;
    }
    .peligro-texto {
        font-weight: bold;
        font-size: 1.1rem;
        margin-top: 10px;
        color: var(--color-primario);
    }
    
    /* Títulos secundarios (Naranja) */
    .titulo-naranja {
        color: var(--color-secundario);
        text-align: center;
        font-weight: bold;
        font-size: 1.5rem;
    }
    .subtitulo-gris {
        color: #777;
        text-align: center;
        font-size: 0.9rem;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------- ENCABEZADO ----------------
st.markdown("""
<div class="header-logo">
    Mosqui<span style="font-size: 0.8em;">🦟</span>ero
    <span class="badge-demo">● Demo IA</span>
</div>
""", unsafe_allow_html=True)
st.write("---") 

# ---------------- MEMORIA (CACHE) ----------------
if "resultado_texto" not in st.session_state:
    st.session_state.resultado_texto = None
if "peligro_num" not in st.session_state:
    st.session_state.peligro_num = 0
if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = None

# ---------------- NAVEGACIÓN (TABS) ----------------
tab1, tab2, tab3 = st.tabs(["📷\nDetección", "📋\nPatio Cero", "💡\nPrevención"])

# ==========================================
# PESTAÑA 1: DETECCIÓN (Escáner de Entorno)
# ==========================================
with tab1:
    st.markdown('<div class="titulo-naranja">Escáner de Entorno</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitulo-gris">Toma una foto de tu patio o áreas sospechosas.</div>', unsafe_allow_html=True)
    
    # Contenedor punteado
    st.markdown('<div class="contenedor-blanco" style="border-style: dashed; border-width: 2px;">', unsafe_allow_html=True)
    
    opcion_entrada = st.radio("Método de entrada", ("Tomar Foto (Cámara)", "Galería (Subir archivo)"), label_visibility="collapsed", horizontal=True)

    img_buffer = None
    if "Cámara" in opcion_entrada:
        img_buffer = st.camera_input("Captura el objetivo")
    else:
        img_buffer = st.file_uploader("Selecciona una imagen", type=["png", "jpg", "jpeg"])

    if "ultima_imagen" not in st.session_state or st.session_state.ultima_imagen != img_buffer:
        st.session_state.ultima_imagen = img_buffer
        st.session_state.resultado_texto = None

    if img_buffer is not None:
        imagen = Image.open(img_buffer)
        st.image(imagen, caption="Imagen cargada", use_column_width=True)

        if st.button("🔍 ANALIZAR FOTOGRAFÍA"):
            with st.spinner("Procesando imagen..."):
                try:
                    modelo = genai.GenerativeModel('gemini-2.5-flash')
                    prompt = """
                    Analiza la imagen adjunta e identifica si hay mosquitos, larvas o posibles criaderos de mosquitos.
                    Devuelve la respuesta estrictamente en este formato:
                    
                    *🦟 OBJETIVO:* [Nombre o tipo de criadero]
                    *⚠️ NIVEL DE AMENAZA:* [Nulo / Bajo / Medio / Alto / Crítico]
                    *📖 REGISTRO:* [Explicación concisa]
                    *🛡️ ACCIÓN RECOMENDADA:* [Medida preventiva inmediata]
                    *🔢 NIVEL_NUMERICO:* [Número del 0 al 100, sin símbolo %]
                    """
                    respuesta = modelo.generate_content([prompt, imagen])
                    texto_crudo = respuesta.text
                    
                    match = re.search(r"NIVEL_NUMERICO.*?(\d+)", texto_crudo)
                    peligro = int(match.group(1)) if match else 50
                    texto_limpio = re.sub(r"\*?🔢?\s*NIVEL_NUMERICO.*", "", texto_crudo).strip()
                    
                    texto_para_leer = texto_limpio.replace("*", "").replace("🦟", "").replace("⚠️", "").replace("📖", "").replace("🛡️", "")
                    tts = gTTS(text=texto_para_leer, lang='es', tld='com.mx')
                    audio_fp = io.BytesIO()
                    tts.write_to_fp(audio_fp)
                    audio_fp.seek(0)
                    
                    st.session_state.resultado_texto = texto_limpio
                    st.session_state.peligro_num = peligro
                    st.session_state.audio_bytes = audio_fp.read()
                    
                except Exception as e:
                    st.error(f"Error en el análisis: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- RESULTADOS ---
    if st.session_state.resultado_texto:
        st.audio(st.session_state.audio_bytes, format='audio/mp3', autoplay=True)
        
        st.markdown('<div class="pokedex-card">', unsafe_allow_html=True)
        st.markdown("### Resultado del Análisis")
        st.markdown(st.session_state.resultado_texto)
        st.markdown(f'<div class="peligro-texto">Nivel de Riesgo: {st.session_state.peligro_num}%</div>', unsafe_allow_html=True)
        st.progress(st.session_state.peligro_num / 100.0)
        st.markdown('</div>', unsafe_allow_html=True)

        # Botón de WhatsApp ajustado
        mensaje_wa = f"🚨 *REPORTE MOSQUICERO* 🚨\n\n{st.session_state.resultado_texto}\n\nRiesgo: {st.session_state.peligro_num}%"
        url_whatsapp = f"https://wa.me/?text={urllib.parse.quote(mensaje_wa)}"
        st.link_button("📲 Compartir reporte por WhatsApp", url=url_whatsapp, type="primary")

# ==========================================
# PESTAÑA 2: PATIO CERO (Checklist)
# ==========================================
with tab2:
    st.markdown('<div class="titulo-naranja">Patio Cero Criaderos</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitulo-gris">Marca las tareas que ya realizaste.</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="contenedor-blanco" style="text-align: left;">', unsafe_allow_html=True)
    
    tareas = ["Volteé cubetas", "Tapé el tinaco", "Limpié bebederos", "Revisé canaletas", "Deseché llantas"]
    
    completadas = 0
    for i, tarea in enumerate(tareas):
        if st.checkbox(tarea, key=f"tarea_{i}"):
            completadas += 1
            
    porcentaje = int((completadas / len(tareas)) * 100)
    
    st.markdown("---")
    st.markdown(f'<div style="display:flex; justify-content:space-between; color:var(--color-primario); font-weight:bold;"><span>NIVEL DE PROTECCIÓN</span><span style="font-size:1.5rem;">{porcentaje}%</span></div>', unsafe_allow_html=True)
    st.progress(porcentaje / 100.0)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# PESTAÑA 3: PREVENCIÓN (Acordeones)
# ==========================================
with tab3:
    st.markdown('<div class="titulo-naranja">Guía Preventiva</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitulo-gris">Información esencial sobre el Dengue y control de vectores.</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="contenedor-blanco" style="text-align: left; padding: 10px;">', unsafe_allow_html=True)
    
    with st.expander("🦟 ¿Cómo es el mosquito?"):
        st.write("El mosquito *Aedes aegypti* es oscuro con manchas blancas en las patas y un dibujo en forma de lira en el tórax. Suele picar durante el día, principalmente temprano por la mañana y al atardecer.")
        
    with st.expander("➕ Síntomas de Alerta"):
        st.write("""
        Acude al médico si presentas:
        * Fiebre alta repentina
        * Dolor detrás de los ojos
        * Dolor muscular y articular severo
        * Erupción en la piel (sarpullido)
        * Náuseas o vómitos
        """)
        
    with st.expander("🛡️ Tratamiento y Cuidados"):
        st.write("No te automediques. Evita tomar aspirina o ibuprofeno, ya que pueden aumentar el riesgo de sangrado. Mantente hidratado, guarda reposo y acude a tu centro de salud más cercano.")
        
    st.markdown('</div>', unsafe_allow_html=True)