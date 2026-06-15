import streamlit as st
import fitz  # PyMuPDF
import os
import io
import pytesseract
from PIL import Image
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field

# Import LangChain integrations
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

# 1. Page Configuration & Custom CSS for premium styling
st.set_page_config(
    page_title="Extractor de Identidad LLM + OCR",
    page_icon="🆔",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Dark theme custom glassmorphism stylesheet
st.markdown("""
<style>
    .reportview-container {
        background: #0f111a;
    }
    
    /* Clean gradient header */
    .title-container {
        background: linear-gradient(135deg, #4f46e5 0%, #06b6d4 100%);
        padding: 2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        text-align: center;
    }
    .title-container h1 {
        margin: 0;
        font-family: 'Outfit', sans-serif;
        font-size: 2.2rem;
        font-weight: 700;
        letter-spacing: -0.05em;
    }
    .title-container p {
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }

    /* Cards */
    .card {
        background-color: #1e293b;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #334155;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
    }
    
    .card-title {
        color: #38bdf8;
        font-weight: 600;
        font-size: 1.2rem;
        margin-bottom: 1rem;
        border-bottom: 1px solid #334155;
        padding-bottom: 0.5rem;
    }

    /* Table styling */
    .result-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
    }
    .result-table td {
        padding: 12px;
        border-bottom: 1px solid #334155;
    }
    .result-table td.label {
        font-weight: bold;
        color: #94a3b8;
        width: 40%;
    }
    .result-table td.value {
        color: #f8fafc;
        font-family: monospace;
        font-size: 1.05rem;
    }
    
    /* Badges */
    .badge-true {
        background-color: #16a34a;
        color: white;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: bold;
    }
    .badge-false {
        background-color: #dc2626;
        color: white;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Header Section
st.markdown("""
<div class="title-container">
    <h1>Demo: Pipeline OCR + LLM Estructurado</h1>
    <p>PDF ➔ Conversión a Imagen ➔ Tesseract OCR (Localización y Texto) ➔ Llama 3.1 Local (Extracción)</p>
</div>
""", unsafe_allow_html=True)

# 2. Structured Schema Definition
class TipoIdentificacion(str, Enum):
    DNI = "dni"
    NIE = "nie"
    PERMISO_RESIDENCIA = "permiso de residencia"

class ExtraccionDNI(BaseModel):
    numero_identificacion: str = Field(
        ..., 
        description="El número de identificación completo extraído del documento (cadena/str, ej: 12345678Z, X1234567L o similares)."
    )
    ambas_caras: bool = Field(
        ..., 
        description="Indica si se aprecian ambas caras del documento (anverso y reverso) según la información y textos de las páginas extraídas."
    )
    fecha_validez: str = Field(
        ..., 
        description="Fecha de validez o caducidad del documento con el formato estricto dd/mm/yyyy. Si no aparece o no se lee bien, dejar vacío."
    )
    tipo_identificacion: TipoIdentificacion = Field(
        ..., 
        description="El tipo del documento detectado: 'dni', 'nie' o 'permiso de residencia'."
    )

# 3. PDF-to-Image & OCR Pipeline
def ejecutar_pipeline_ocr(uploaded_file) -> tuple[str, list]:
    """
    Convierte el PDF a imágenes, ejecuta Tesseract OCR localmente, y retorna:
    - Un string con todo el texto concatenado para enviar al LLM.
    - La lista de bytes de imágenes para poder mostrarlas en la interfaz de usuario.
    """
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    texto_completo = ""
    imagenes_bytes = []

    for page_idx, page in enumerate(doc):
        pix = page.get_pixmap(dpi=150)
        img_data = pix.tobytes("png")
        imagenes_bytes.append(img_data)

        img = Image.open(io.BytesIO(img_data))

        try:
            page_text = pytesseract.image_to_string(img, lang="spa")
            texto_completo += f"--- PÁGINA {page_idx + 1} ---\n{page_text.strip()}\n\n"
        except Exception as e:
            st.error(f"Error al ejecutar Tesseract OCR: {str(e)}")

    return texto_completo.strip(), imagenes_bytes

# 4. Streamlit Layout
col_left, col_right = st.columns([1, 1], gap="large")

# Configuration (Hardcoded default links to Docker network)
ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

with col_left:
    st.markdown('<div class="card-title">📥 Carga de Documento</div>', unsafe_allow_html=True)
    pdf_file = st.file_uploader("Arrastra tu PDF de DNI/NIE aquí", type=["pdf"])
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.info(f"**Servicios Activos:**\n- OCR: Tesseract (local)\n- LLM: `{ollama_host}` (Modelo: `llama3.1`)")

with col_right:
    st.markdown('<div class="card-title">📊 Datos Extraídos por LLM</div>', unsafe_allow_html=True)

if pdf_file is not None:
    # Execution
    with col_left:
        st.markdown('<div class="card-title">⚙️ Estado del Procesamiento</div>', unsafe_allow_html=True)
        
        with st.spinner("Paso 1: Convirtiendo PDF a Imagen y ejecutando Tesseract OCR..."):
            ocr_text_llm, page_images = ejecutar_pipeline_ocr(pdf_file)
            
    if not ocr_text_llm:
        st.warning("No se obtuvo ningún texto a través del servicio de OCR.")
    else:
        # Render intermediate visualizations on the left side
        with col_left:
            st.success("¡Paso 1/2: OCR Finalizado!")
            
            # Show preview of PDF page rendered as image
            for idx, img_b in enumerate(page_images):
                st.image(img_b, caption=f"Página {idx+1} procesada por Tesseract OCR", use_column_width=True)
                
            # Expandable preview of spatial data
            with st.expander("🔍 Ver texto extraído por Tesseract OCR"):
                st.code(ocr_text_llm, language="text")

        # LLM processing on the right side
        with col_right:
            with st.spinner("Paso 2: Interpretando datos estructurados con Llama 3.1..."):
                try:
                    # Initialize LLM
                    llm = ChatOllama(
                        model="llama3.1",
                        temperature=0.0,
                        base_url=ollama_host
                    )
                    
                    # Bind structured schema
                    structured_llm = llm.with_structured_output(ExtraccionDNI)
                    
                    # Custom prompt template to help parse spatial coords
                    prompt = ChatPromptTemplate.from_messages([
                        ("system", (
                            "Eres un agente experto en extracción y validación de documentos oficiales.\n"
                            "Se te proporciona el texto extraído mediante OCR de un documento de identidad.\n"
                            "Tu única tarea es analizar el texto para rellenar el esquema estructurado.\n\n"
                            "Instrucciones clave:\n"
                            "1. 'numero_identificacion': Extrae el número de DNI (8 números + 1 letra) o NIE (1 letra + 7 números + 1 letra).\n"
                            "2. 'ambas_caras': Responde 'true' si detectas elementos tanto del anverso (foto del titular, fecha de nacimiento, "
                            "nombre) como del reverso (nombres de los padres, código de lectura mecánica/MRZ). De lo contrario 'false'.\n"
                            "3. 'fecha_validez': Localiza la fecha de caducidad o validez del documento y devuélvela como dd/mm/yyyy.\n"
                            "Si no la encuentras, deja una cadena vacía.\n"
                            "4. 'tipo_identificacion': Clasifícalo estrictamente en 'dni', 'nie', o 'permiso de residencia'.\n"
                        )),
                        ("human", "Salida de Tesseract OCR:\n\n{text}")
                    ])
                    
                    chain = prompt | structured_llm
                    resultado: ExtraccionDNI = chain.invoke({"text": ocr_text_llm})
                    
                    st.success("¡Paso 2/2: Extracción Estructurada Completada!")
                    
                    # Beautiful results table
                    badge_ambas_caras = '<span class="badge-true">SÍ</span>' if resultado.ambas_caras else '<span class="badge-false">NO</span>'
                    
                    html_table = f"""
                    <table class="result-table">
                        <tr>
                            <td class="label">Número de Identificación:</td>
                            <td class="value">{resultado.numero_identificacion}</td>
                        </tr>
                        <tr>
                            <td class="label">Tipo de Identificación:</td>
                            <td class="value" style="text-transform: uppercase;">{resultado.tipo_identificacion.value}</td>
                        </tr>
                        <tr>
                            <td class="label">Ambas Caras Presentes:</td>
                            <td class="value">{badge_ambas_caras}</td>
                        </tr>
                        <tr>
                            <td class="label">Fecha de Validez:</td>
                            <td class="value">{resultado.fecha_validez or 'No disponible'}</td>
                        </tr>
                    </table>
                    """
                    st.markdown(html_table, unsafe_allow_html=True)
                    
                    # Show Raw JSON
                    st.markdown("<br>", unsafe_allow_html=True)
                    with st.expander("⚙️ Ver JSON Estructurado"):
                        st.json(resultado.model_dump())
                        
                except Exception as e:
                    st.error("Ocurrió un error al consultar el modelo Ollama.")
                    st.error(f"Detalles: {str(e)}")
                    st.warning("Verifica que el contenedor de Ollama esté corriendo y que el modelo llama3.1 esté descargado.")
else:
    with col_right:
        st.info("Por favor, sube un documento PDF de identidad a la izquierda para iniciar el análisis.")
