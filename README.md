# Demo: Pipeline OCR + LLM Estructurado en Local

Esta aplicación demuestra un pipeline de extracción de información de documentos de identidad (DNI, NIE o Permiso de Residencia) combinando **OCR (Optical Character Recognition)** y **LLMs locales**. 

El flujo de trabajo es el siguiente:
1. **Carga del PDF:** El usuario sube un archivo PDF del documento.
2. **Conversión a Imagen:** La aplicación Streamlit convierte cada página del PDF en una imagen PNG usando `PyMuPDF` (`fitz`).
3. **Servicio PaddleOCR:** La imagen se envía a un microservicio local de **FastAPI + PaddleOCR** que detecta el texto y sus coordenadas en la página.
4. **Formateo Espacial:** Streamlit organiza las lecturas en una cadena espacializada (ej: `Coordenadas: [[x, y], ...] | Texto: "CADUCIDAD"`).
5. **Inferencia LLM (Llama 3.1):** Esta estructura visual-textual se envía al modelo local `llama3.1` mediante `ChatOllama` y LangChain. El LLM interpreta la disposición de los datos y los extrae en un esquema de **Pydantic** limpio y estructurado (`with_structured_output`).

---

## 🛠️ Arquitectura de Servicios (Docker Compose)

La aplicación utiliza tres contenedores declarados en `docker-compose.yml`:
1. `streamlit-app` (Puerto `8501`): Interfaz web de usuario y coordinamiento del pipeline.
2. `paddle-ocr` (Puerto `8000`): Microservicio REST en Python 3.10 que envuelve la librería `paddleocr` y procesa las imágenes.
3. `ollama` (Puerto `11434`): Motor de LLM en local. Su Dockerfile descarga automáticamente el modelo `llama3.1` en la fase de construcción.

---

## 🚀 Cómo Ejecutar la Aplicación

Para desplegar y probar la aplicación completa con todos sus servicios:

1. Ejecuta el comando de inicio en la raíz de tu proyecto:
   ```bash
   docker compose up --build
   ```
   *(Nota: La construcción del contenedor `ollama` descargará el modelo llama3.1 de forma integrada, y la del contenedor `paddle-ocr` descargará los pesos del detector y reconocedor OCR por defecto en su primera inicialización, lo que puede tardar unos minutos).*

2. Abre tu navegador e ingresa a:
   * **Streamlit App:** [http://localhost:8501](http://localhost:8501)
   * **PaddleOCR Endpoint:** [http://localhost:8000/docs](http://localhost:8000/docs) (Para probar la API de OCR de forma aislada)
   * **Ollama API:** [http://localhost:11434](http://localhost:11434)

---

## 🔧 Desarrollo y Depuración Local (VS Code + `uv`)

Si quieres depurar el código de Streamlit de forma interactiva en tu máquina:

### 1. Sincronizar el entorno virtual
Instala las dependencias declaradas en `pyproject.toml` en tu máquina local:
```bash
uv sync --link-mode=copy
```

### 2. Iniciar servicios externos en Docker
Para no tener que instalar PaddleOCR ni Ollama nativos, levanta únicamente los contenedores de backend:
```bash
docker compose up -d ollama paddle-ocr
```

### 3. Ejecutar el Debugger en VS Code
1. Abre este directorio con VS Code.
2. Presiona `Cmd+Shift+D` o `Ctrl+Shift+D` para abrir el panel de depuración.
3. Selecciona la configuración **"Streamlit App"** y presiona `F5`.
4. El depurador local se conectará a la instancia de Streamlit en tu máquina, permitiendo establecer breakpoints. La aplicación utilizará por defecto `http://localhost:8000` para el OCR y `http://localhost:11434` para Ollama.

---

## 📄 Datos Extraídos del Documento

El pipeline retornará un JSON estructurado bajo el siguiente esquema:
* `numero_identificacion`: El número del documento de identidad como string (con letras).
* `ambas_caras`: Boolean indicando si se detectaron los elementos del anverso y reverso.
* `fecha_validez`: Fecha en formato estricto `dd/mm/yyyy` (o cadena vacía si no se detecta).
* `tipo_identificacion`: Tipo de documento clasificado estrictamente como `dni`, `nie` o `permiso de residencia`.
