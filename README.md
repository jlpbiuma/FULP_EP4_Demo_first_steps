# Demo: Extractor de Documentos de Identidad con LLM Local

Esta es una pequeña aplicación construida con **Streamlit**, **LangChain** y **Ollama** diseñada para automatizar la extracción de datos de documentos de identidad (DNI, NIE o Permiso de Residencia) en formato PDF utilizando un modelo LLM en local (`llama3.1`).

La aplicación está completamente dockerizada, no requiere de archivos `.env` (todas las configuraciones están declaradas en Docker Compose o parametrizadas en el código) y cuenta con soporte para depuración local en VS Code mediante `uv`.

---

## 🎯 Requisitos de Extracción

El sistema analiza el texto extraído del PDF y retorna de forma estructurada los siguientes campos obligatorios:
1. **Número de Identificación** (`numero_identificacion`): Cadena de texto (`str`) con el identificador completo (ej: DNI o NIE con letra).
2. **Ambas caras** (`ambas_caras`): Booleano (`bool`) que especifica si la información leída indica que el PDF contiene el documento por ambas caras (anverso y reverso).
3. **Fecha de validez** (`fecha_validez`): Fecha de caducidad en formato estructurado `dd/mm/yyyy` (cadena vacía si no se detecta).
4. **Tipo de identificación** (`tipo_identificacion`): Tipo de documento detectado, limitado estrictamente a: `dni`, `nie` o `permiso de residencia`.

---

## 🚀 Cómo Ejecutar la Aplicación con Docker Compose

La aplicación arranca con un único comando. Docker Compose levantará tanto el servidor de Ollama, un contenedor auxiliar que descarga automáticamente el modelo `llama3.1`, y el servicio web de Streamlit.

### Pasos:

1. Asegúrate de tener instalado **Docker** y **Docker Compose** en tu sistema.
2. Desde la raíz de este proyecto, ejecuta:
   ```bash
   docker compose up --build
   ```
3. El servicio `ollama-pull-model` se conectará al servicio de Ollama y descargará automáticamente el modelo `llama3.1` (esto puede tomar varios minutos la primera vez dependiendo de tu velocidad de conexión a Internet).
4. Una vez completado, abre tu navegador e ingresa a:
   * **Streamlit App:** [http://localhost:8501](http://localhost:8501)
   * **Ollama API (Verificación):** [http://localhost:11434](http://localhost:11434)

---

## 🔧 Desarrollo y Depuración Local (VS Code + `uv`)

Si deseas ejecutar la aplicación localmente fuera de Docker (para hacer debugging con puntos de interrupción directamente en el código), sigue estos pasos:

### 1. Preparar el entorno con `uv`
Dado que el proyecto utiliza el gestor `uv`, puedes instalar todas las dependencias locales en el entorno virtual (`.venv`) ejecutando:
```bash
uv sync --link-mode=copy
```

### 2. Levantar el servicio Ollama en Docker
Para no consumir recursos instalando Ollama en tu sistema operativo principal, puedes iniciar únicamente el contenedor de Ollama desde Docker Compose:
```bash
docker compose up -d ollama
```

*Nota: Asegúrate de descargar el modelo en tu Ollama local ejecutando:*
```bash
docker exec -it ollama ollama pull llama3.1
```

### 3. Iniciar la depuración desde VS Code
El proyecto incluye un archivo `.vscode/launch.json` configurado para este propósito:
1. Abre este directorio en VS Code.
2. Abre la pestaña de **Run and Debug** (o presiona `Ctrl+Shift+D` / `Cmd+Shift+D`).
3. Selecciona la configuración **"Streamlit App"**.
4. Pulsa el botón verde **Play** (o presiona `F5`).
5. VS Code iniciará la aplicación de Streamlit usando el binario Python del entorno local `.venv` y adjuntará el depurador para capturar breakpoints y excepciones.

---

## 🧠 ¿Cómo funciona la Extracción Estructurada?

La aplicación utiliza el método `with_structured_output` provisto por la integración `langchain-ollama`.

1. **Definición del Esquema:** Declaramos una estructura de datos estricta usando **Pydantic**:
   ```python
   class ExtraccionDNI(BaseModel):
       numero_identificacion: str
       ambas_caras: bool
       fecha_validez: str
       tipo_identificacion: TipoIdentificacion  # (Enum: 'dni', 'nie', 'permiso de residencia')
   ```

2. **Asociación del Modelo:** Pasamos este esquema a nuestro LLM local:
   ```python
   llm = ChatOllama(model="llama3.1", base_url="http://localhost:11434")
   structured_llm = llm.with_structured_output(ExtraccionDNI)
   ```

3. **Inferencia:** El LLM genera una respuesta en formato JSON que respeta exactamente los tipos de datos descritos en la clase Pydantic, garantizando que el backend de Streamlit reciba datos limpios y listos para ser consumidos o guardados.
