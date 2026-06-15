# Demo: Pipeline OCR + LLM Estructurado en Local

Esta aplicación demuestra un pipeline de extracción de información de documentos de identidad (DNI, NIE o Permiso de Residencia) combinando **OCR (Tesseract)** y **LLMs locales**.

El flujo de trabajo es el siguiente:
1. **Carga del PDF:** El usuario sube un archivo PDF del documento.
2. **Conversión a Imagen:** La aplicación Streamlit convierte cada página del PDF en una imagen PNG usando `PyMuPDF` (`fitz`).
3. **Tesseract OCR:** Se ejecuta `pytesseract` localmente sobre cada imagen para extraer todo el texto del documento.
4. **Inferencia LLM (Llama 3.1):** El texto extraído se envía al modelo local `llama3.1` mediante `ChatOllama` y LangChain. El LLM interpreta el texto y extrae los datos en un esquema de **Pydantic** limpio y estructurado (`with_structured_output`).

---

## Arquitectura de Servicios (Docker Compose)

La aplicación utiliza dos contenedores declarados en `docker-compose.yml`:
1. `streamlit-app` (Puerto `8501`): Interfaz web de usuario y coordinamiento del pipeline. Incluye Tesseract OCR instalado directamente en el contenedor.
2. `ollama` (Puerto `11434`): Motor de LLM en local. Su Dockerfile descarga automáticamente el modelo `llama3.1` en la fase de construcción.

---

## Cómo Ejecutar la Aplicación

Para desplegar y probar la aplicación completa con todos sus servicios:

1. Ejecuta el comando de inicio en la raíz de tu proyecto:
   ```bash
   docker compose up --build
   ```
   *(Nota: La construcción del contenedor `ollama` descargará el modelo llama3.1 de forma integrada, lo que puede tardar unos minutos).*

2. Abre tu navegador e ingresa a:
   * **Streamlit App:** [http://localhost:8501](http://localhost:8501)
   * **Ollama API:** [http://localhost:11434](http://localhost:11434)

---

## Desarrollo y Depuración Local (VS Code + `uv`)

Si quieres depurar el código de Streamlit de forma interactiva en tu máquina:

### 1. Instalar Tesseract en el sistema
Necesitas tener Tesseract OCR instalado con el paquete de idioma español:
- **macOS:** `brew install tesseract tesseract-lang`
- **Ubuntu/Debian:** `sudo apt install tesseract-ocr tesseract-ocr-spa`

### 2. Sincronizar el entorno virtual
Instala las dependencias declaradas en `pyproject.toml` en tu máquina local:
```bash
uv sync --link-mode=copy
```

### 3. Iniciar servicios externos en Docker
Para no tener que instalar Ollama nativo, levanta únicamente el contenedor de backend:
```bash
docker compose up -d ollama
```

### 4. Ejecutar el Debugger en VS Code
1. Abre este directorio con VS Code.
2. Presiona `Cmd+Shift+D` o `Ctrl+Shift+D` para abrir el panel de depuración.
3. Selecciona la configuración **"Streamlit App"** y presiona `F5`.
4. El depurador local se conectará a la instancia de Streamlit en tu máquina, permitiendo establecer breakpoints. La aplicación utilizará Tesseract OCR de forma local y `http://localhost:11434` para Ollama.

---

## Datos Extraídos del Documento

El pipeline retornará un JSON estructurado bajo el siguiente esquema:
* `numero_identificacion`: El número del documento de identidad como string (con letras).
* `ambas_caras`: Boolean indicando si se detectaron los elementos del anverso y reverso.
* `fecha_validez`: Fecha en formato estricto `dd/mm/yyyy` (o cadena vacía si no se detecta).
* `tipo_identificacion`: Tipo de documento clasificado estrictamente como `dni`, `nie` o `permiso de residencia`.
