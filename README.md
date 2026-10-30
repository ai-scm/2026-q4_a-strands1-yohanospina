# Agente de Viajes con Strands SDK y Amazon Bedrock

Este proyecto implementa un agente de viajes conversacional inteligente desarrollado con **Strands SDK** y **Amazon Bedrock**, desplegado en una arquitectura serverless sobre **AWS Lambda** con memoria de sesión en **Amazon DynamoDB** e infraestructura como código gestionada por **AWS SAM (Serverless Application Model)**.

---

## 📋 Requisitos Previos

Asegúrate de contar con las siguientes herramientas instaladas y configuradas en tu entorno local:

- **Python 3.12+** y `venv`
- **AWS CLI** configurado con credenciales activas (`aws configure` o perfil IAM/SSO)
- **AWS SAM CLI** instalado
- **Docker** (requerido para la compilación de contenedores con `sam build --use-container`)
- **Git**

---

## 🛠️ Configuración e Instalación Paso a Paso

### 1. Clonar e Inicializar el Repositorio

```bash
git clone <URL_DE_TU_REPOSITORIO_GIT>
cd skillbuilder-strands
git init
```

### 2. Crear y Activar el Entorno Virtual

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar Dependencias del Proyecto

```bash
pip install --upgrade pip
pip install -r src/requirements.txt
```

---

## 🚀 Compilación y Despliegue en AWS

El despliegue en AWS se realiza de forma automatizada a través de AWS SAM:

### 1. Compilar el Proyecto

```bash
sam build --use-container
```

### 2. Desplegar la Infraestructura

Si ejecutas el despliegue interactivo por primera vez:

```bash
sam deploy --guided
```

O utilizando un perfil específico de AWS CLI configurado:

```bash
sam build --use-container && sam deploy --profile PS-PowerUserAccess-891377180652
```

Al finalizar el despliegue, la consola de SAM devolverá la **URL pública de la función Lambda** (`LambdaFunctionUrl`).

---

## 🧪 Pruebas de Interacción desde la Terminal

Puedes enviar peticiones en formato JSON al endpoint del agente utilizando `curl`:

### Consulta de Vuelos

```bash
curl -X POST <TU_LAMBDA_FUNCTION_URL> \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "¿Qué aerolíneas vuelan a Seattle?",
    "user": {
      "session_id": "sesion_prueba_1"
    }
  }'
```

### Consulta de Clima

```bash
curl -X POST <TU_LAMBDA_FUNCTION_URL> \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "¿Cuál es el clima en Seattle?",
    "user": {
      "session_id": "sesion_prueba_1"
    }
  }'
```

---

## 🧱 Estructura del Proyecto

```text
skillbuilder-strands/
├── src/
│   ├── lambda_function.py    # Lógica principal del agente Strands SDK
│   └── requirements.txt      # Dependencias en ejecución (strands-sdk, boto3, etc.)
├── template.yaml             # Plantilla de AWS SAM (Lambda, DynamoDB, Roles)
├── samconfig.toml            # Configuración de parámetros de despliegue SAM
├── travel_guides.txt         # Documento fuente para RAG (Knowledge Base)
├── agent.py                  # Pruebas locales del agente
├── app.py                    # Interfaz gráfica conversacional (Streamlit)
└── .gitignore                # Reglas de archivos excluidos de Git
```

---

## 🏛️ Componentes de Arquitectura

- **Framework de Agentes**: Strands SDK
- **Modelo de Lenguaje**: Amazon Bedrock
- **Capa Serverless**: AWS Lambda con Function URL (Python 3.12)
- **Persistencia de Sesión**: Amazon DynamoDB
- **Herramientas (Tools)**:
  - `flight_search`: Consulta de aerolíneas y vuelos.
  - `http_request`: Consumo en tiempo real de la API de clima del Servicio Meteorológico Nacional.
  - `retrieve`: Búsqueda semántica en Bedrock Knowledge Bases (RAG).
