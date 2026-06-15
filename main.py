import streamlit as st
import pypdf
import os
import json
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

# Import LangChain integrations
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

# 1. Page Configuration & Custom CSS for premium styling
st.set_page_config(
    page_title="Extractor de Identidad LLM",
    page_icon="🆔",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Dark theme custom glassmorphism stylesheet
st.markdown("""
<style>
    /* Styling the main container */
    .reportview-container {
        background: #0f111a;
    }
    
    /* Clean gradient header */
    .title-container {
        background: linear-gradient(135deg, #4f46e5 0%, #06b6d4 100%);
        padding: 2.5rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        text-align: center;
    }
    .title-container h1 {
        margin: 0;
        font-family: 'Outfit', sans-serif;
        font-size: 2.5rem;
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
        margin-bottom: 1rem;
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
        padding: 10px;
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
    }
    
    /* Badges */
    .badge-true {
        background-color: #16a34a;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: bold;
    }
    .badge-false {
        background-color: #dc2626;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Header Section
st.markdown("""
<div class="title-container">
    <h1>Demo: Extracción Estructurada de Documentos</h1>
    <p>Sube un documento de identidad (DNI, NIE o Permiso de Residencia) en formato PDF para extraer sus datos mediante Llama 3.1 local</p>
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
        description="El número de identificación completo extraído del documento (cadena/str, ej: 12345678Z o X1234567L)."
    )
    ambas_caras: bool = Field(
        ..., 
        description="Indica si se aprecian ambas caras del documento (anverso y reverso) en la información provista."
    )
    fecha_validez: str = Field(
        ..., 
        description="Fecha de validez o fecha de caducidad del documento con el formato dd/mm/yyyy. Si no se indica o no es clara, dejar en blanco."
    )
    tipo_identificacion: TipoIdentificacion = Field(
        ..., 
        description="El tipo del documento analizado: 'dni', 'nie' o 'permiso de residencia'."
    )

# 3. Text Extraction Helper
def extraer_texto_pdf(uploaded_file) -> str:
    """Extrae el contenido de texto de un archivo PDF subido."""
    try:
        reader = pypdf.PdfReader(uploaded_file)
        texto = ""
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                texto += f"--- PÁGINA {i+1} ---\n{page_text}\n\n"
        return texto.strip()
    except Exception as e:
        st.error(f"Error al leer el archivo PDF: {str(e)}")
        return ""

# 4. Processing layout
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown('<div class="card-title">📥 Carga de Documento</div>', unsafe_allow_html=True)
    pdf_file = st.file_uploader("Arrastra tu PDF aquí o haz clic para buscar", type=["pdf"])
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Connection parameters (Hardcoded to Docker Ollama service or local fallback)
    ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    
    st.info(f"Conexión LLM: `{ollama_host}` (Modelo: `llama3.1`)")

with col_right:
    st.markdown('<div class="card-title">📊 Datos Extraídos</div>', unsafe_allow_html=True)
    
    if pdf_file is not None:
        with st.spinner("1. Extrayendo texto del PDF..."):
            texto_pdf = extraer_texto_pdf(pdf_file)
            
        if not texto_pdf:
            st.warning("No se pudo extraer texto del PDF. Asegúrate de que no sea escaneado como imagen pura sin OCR.")
        else:
            with col_left:
                with st.expander("🔍 Ver texto extraído del PDF"):
                    st.code(texto_pdf, language="text")
            
            with st.spinner("2. Procesando con Llama 3.1..."):
                try:
                    # Initialize the ChatOllama model
                    llm = ChatOllama(
                        model="llama3.1",
                        temperature=0.0,
                        base_url=ollama_host
                    )
                    
                    # Bind structured output
                    structured_llm = llm.with_structured_output(ExtraccionDNI)
                    
                    # Create prompt template
                    prompt = ChatPromptTemplate.from_messages([
                        ("system", (
                            "Eres un asistente especializado en extracción de información. Tu única tarea es extraer la información "
                            "requerida a partir del texto de un documento de identidad y rellenar el esquema estructurado.\n"
                            "Normas:\n"
                            "1. 'numero_identificacion': debe contener el número entero (ej. 12345678A o Y1234567B).\n"
                            "2. 'ambas_caras': evalúa si el texto indica o describe elementos del anverso y el reverso.\n"
                            "3. 'fecha_validez': busca la fecha de validez/caducidad y formátala como dd/mm/yyyy. Si no aparece, deja vacío.\n"
                            "4. 'tipo_identificacion': clasifícalo estrictamente en 'dni', 'nie' o 'permiso de residencia'."
                        )),
                        ("human", "Texto extraído:\n\n{text}")
                    ])
                    
                    # Run the LangChain chain
                    chain = prompt | structured_llm
                    resultado: ExtraccionDNI = chain.invoke({"text": texto_pdf})
                    
                    # Display structured outcomes
                    st.success("¡Extracción completada con éxito!")
                    
                    # Render the beautiful table
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
                    
                    # Display Raw JSON inside an expander
                    st.markdown("<br>", unsafe_allow_html=True)
                    with st.expander("⚙️ Ver JSON Estructurado"):
                        # Format as dict for presentation
                        st.json(resultado.model_dump())
                        
                except Exception as e:
                    st.error("Ocurrió un error al consultar el modelo local.")
                    st.error(f"Detalles: {str(e)}")
                    st.warning("Asegúrate de que Ollama esté corriendo y de haber descargado el modelo llama3.1 (`ollama run llama3.1`).")
    else:
        st.info("Sube un archivo PDF en el panel de la izquierda para ver los resultados aquí.")
