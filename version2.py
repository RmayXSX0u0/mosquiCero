import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse
from gtts import gTTS
import io
import re

# ---------------- CONFIGURACIÓN DE LA API ----------------
GEMINI_API_KEY = "AQ.Ab8RN6LlSFPT-m_uzj42fHjVVgCCEamBXpKUJwPzDyeAE2AuPA" # <--- No olvides poner tu clave aquí
genai.configure(api_key=GEMINI_API_KEY)

# ---------------- CONFIGURACIÓN DE LA PÁGINA ----------------
st.set_page_config(page_title="MosquiDex", page_icon="🦟", layout="centered")

st.markdown("""
    <style>
    .pokedex-card {
        background-color: #f0f2f6;
        border-radius: 15px;
        padding: 20px;
        border-left: 8px solid #ff4b4b;
        margin-top: 20px;
        margin-bottom: 15px;
        color: #333;
    }
    .peligro-texto {
        font-weight: bold;
        font-size: 1.2rem;
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🦟 MosquiDex")
st.subheader("Detector de Mosquitos y Posibles Criaderos")

# ---------------- MEMORIA (CACHE) ----------------
# Guardamos los datos en la sesión para no volver a llamar a la API si el usuario presiona otro botón
if "resultado_texto" not in st.session_state:
    st.session_state.resultado_texto = None
if "peligro_num" not in st.session_state:
    st.session_state.peligro_num = 0
if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = None

# ---------------- INTERFAZ DE ENTRADA ----------------
opcion_entrada = st.radio("¿Cómo deseas ingresar la imagen?", ("Usar Cámara", "Subir Archivo"))

img_buffer = None
if opcion_entrada == "Usar Cámara":
    img_buffer = st.camera_input("Captura el objetivo")
else:
    img_buffer = st.file_uploader("Sube una imagen", type=["png", "jpg", "jpeg"])

# Si el usuario cambia la imagen, limpiamos la memoria anterior
if "ultima_imagen" not in st.session_state or st.session_state.ultima_imagen != img_buffer:
    st.session_state.ultima_imagen = img_buffer
    st.session_state.resultado_texto = None

# ---------------- PROCESAMIENTO E IA ----------------
if img_buffer is not None:
    imagen = Image.open(img_buffer)
    st.image(imagen, caption="Objetivo fijado", use_column_width=True)

    if st.button("🔍 Analizar Objetivo"):
        with st.spinner("Consultando la base de datos de MosquiDex..."):
            try:
                # Usamos el modelo con cuota alta
                modelo = genai.GenerativeModel('gemini-2.5-flash')
                
                prompt_pokedex = """
                Actúa como una 'Pokedex' especializada en control de vectores. Analiza la imagen.
                Devuelve la respuesta estrictamente en este formato:
                
                *🦟 OBJETIVO:* [Nombre o tipo de criadero]
                *⚠️ NIVEL DE AMENAZA:* [Nulo / Bajo / Medio / Alto / Crítico]
                *📖 REGISTRO:* [Explicación concisa de 2 líneas]
                *🛡️ ACCIÓN RECOMENDADA:* [Medida preventiva inmediata]
                *🔢 NIVEL_NUMERICO:* [Un número del 0 al 100 indicando el riesgo, solo el número]
                """
                
                respuesta = modelo.generate_content([prompt_pokedex, imagen])
                texto_crudo = respuesta.text
                
                # 1. Extraer el nivel numérico con Regex para la barra de progreso
                match = re.search(r"NIVEL_NUMERICO.*?(\d+)", texto_crudo)
                peligro = int(match.group(1)) if match else 50
                
                # 2. Limpiar el texto para mostrarlo (quitamos la línea del número)
                texto_limpio = re.sub(r"\*?🔢?\s*NIVEL_NUMERICO.*", "", texto_crudo).strip()
                
                # 3. Generar la voz (quitamos emojis y asteriscos para que la IA hable bien)
                texto_para_leer = texto_limpio.replace("*", "").replace("🦟", "").replace("⚠️", "").replace("📖", "").replace("🛡️", "")
                tts = gTTS(text=texto_para_leer, lang='es', tld='com.mx')
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                audio_fp.seek(0)
                
                # Guardar en memoria
                st.session_state.resultado_texto = texto_limpio
                st.session_state.peligro_num = peligro
                st.session_state.audio_bytes = audio_fp.read()
                
            except Exception as e:
                st.error(f"Error en el análisis: {e}")

# ---------------- MOSTRAR RESULTADOS GUARDADOS ----------------
if st.session_state.resultado_texto:
    # Reproducir audio de Pokédex
    st.audio(st.session_state.audio_bytes, format='audio/mp3', autoplay=True)
    
    # Tarjeta de resultados
    st.markdown('<div class="pokedex-card">', unsafe_allow_html=True)
    st.markdown("### 📊 Ficha del Objetivo")
    st.markdown(st.session_state.resultado_texto)
    
    # Barra de amenaza dinámica
    st.markdown(f'<div class="peligro-texto">Nivel de Riesgo Sanitario: {st.session_state.peligro_num}%</div>', unsafe_allow_html=True)
    st.progress(st.session_state.peligro_num / 100.0)
    st.markdown('</div>', unsafe_allow_html=True)

    # Botón de WhatsApp
    mensaje_wa = f"🚨 *REPORTE MOSQUIDEX* 🚨\n\n{st.session_state.resultado_texto}\n\nNivel de riesgo: {st.session_state.peligro_num}%"
    url_whatsapp = f"https://wa.me/?text={urllib.parse.quote(mensaje_wa)}"
    
    st.link_button(
        label="📲 Compartir reporte por WhatsApp", 
        url=url_whatsapp,
        type="primary"
    )