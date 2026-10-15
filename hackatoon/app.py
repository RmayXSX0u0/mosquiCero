import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# ---------------- CONFIGURACIÓN DE LA API ----------------
# Reemplaza 'TU_API_KEY' con tu clave real o configúrala como variable de entorno
GEMINI_API_KEY = "AQ.Ab8RN6LlSFPT-m_uzj42fHjVVgCCEamBXpKUJwPzDyeAE2AuPA" 
genai.configure(api_key=GEMINI_API_KEY)

# ---------------- CONFIGURACIÓN DE LA PÁGINA ----------------
st.set_page_config(page_title="MosquiDex", page_icon="🦟", layout="centered")

# Estilos CSS personalizados para darle un toque de "Pokedex"
st.markdown("""
    <style>
    .pokedex-card {
        background-color: #f0f2f6;
        border-radius: 15px;
        padding: 20px;
        border-left: 8px solid #ff4b4b;
        margin-top: 20px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🦟 MosquiDex")
st.subheader("Detector de Mosquitos y Posibles Criaderos")
st.write("Sube una foto o toma una con tu cámara para analizar el objetivo.")

# ---------------- INTERFAZ DE USUARIO ----------------
opcion_entrada = st.radio("¿Cómo deseas ingresar la imagen?", ("Usar Cámara", "Subir Archivo"))

img_buffer = None
if opcion_entrada == "Usar Cámara":
    img_buffer = st.camera_input("Captura el objetivo")
else:
    img_buffer = st.file_uploader("Sube una imagen", type=["png", "jpg", "jpeg"])

# ---------------- PROCESAMIENTO E IA ----------------
if img_buffer is not None:
    # Abrir la imagen con Pillow
    imagen = Image.open(img_buffer)
    st.image(imagen, caption="Objetivo fijado", use_column_width=True)

    if st.button("🔍 Analizar Objetivo"):
        with st.spinner("Procesando imagen con la base de datos de MosquiDex..."):
            try:
                # Usamos el modelo Flash, que es el más rápido y eficiente para visión
                modelo = genai.GenerativeModel('gemini-3.8-flash')
                
                # El "Prompt" que obliga a la IA a actuar como una Pokedex
                prompt_pokedex = """
                Actúa como una 'Pokedex' especializada en control de vectores y epidemiología.
                Analiza la imagen adjunta e identifica si hay mosquitos, larvas o posibles criaderos 
                (como llantas con agua, cubetas, floreros, agua estancada, etc.).
                
                No des explicaciones largas, devuelve la respuesta ESTRICTAMENTE en este formato visual:
                
                **🦟 OBJETIVO IDENTIFICADO:** [Nombre del mosquito o tipo de criadero. Ej: Aedes aegypti / Llanta con agua estancada / Zona limpia]
                **⚠️ NIVEL DE AMENAZA:** [Nulo / Bajo / Medio / Alto / Crítico]
                **📖 DESCRIPCIÓN EN LA BASE DE DATOS:** [Breve descripción de 2 líneas sobre lo encontrado y por qué es peligroso]
                **🛡️ ACCIÓN RECOMENDADA:** [Qué debe hacer el usuario. Ej: Voltear el recipiente, tapar, aplicar larvicida, ninguna]
                """
                
                # Enviar la imagen y el prompt a Gemini
                respuesta = modelo.generate_content([prompt_pokedex, imagen])
                
                # Mostrar el resultado dentro de un contenedor con estilo
                st.markdown('<div class="pokedex-card">', unsafe_allow_html=True)
                st.markdown("### 📊 Resultado del Análisis")
                st.markdown(respuesta.text)
                st.markdown('</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Error de conexión con la base de datos: {e}")