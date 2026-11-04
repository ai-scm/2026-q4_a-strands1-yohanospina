# ✈️ Agente de Viajes con Strands SDK & Amazon Bedrock

Agente conversacional de viajes construido con **Strands SDK** y **Amazon Bedrock Nova Lite**, desplegado en arquitectura serverless sobre **AWS Lambda**. Consolida búsqueda de vuelos, clima en tiempo real y guías turísticas en una sola conversación natural, con memoria de sesión persistente en **DynamoDB** y búsqueda semántica RAG sobre documentos propios vía **Bedrock Knowledge Base**.

---

## Arquitectura

```
Usuario (navegador)
      │
      ▼
app.py — Streamlit (local)
      │ HTTP POST
      ▼
Lambda Function URL (AWS us-east-1)
      │
      ├── flight_search   → vuelos por ciudad (datos internos)
      ├── http_request    → clima en tiempo real (NWS API)
      └── retrieve        → búsqueda semántica en Knowledge Base
            │
            ├── DynamoDB         (historial de sesión)
            └── Bedrock KB       (guías turísticas indexadas)
```

**Stack:**
- **Agente**: Strands SDK + Amazon Nova Lite (`us.amazon.nova-lite-v1:0`)
- **Backend**: AWS Lambda Python 3.12 + Function URL pública
- **Memoria**: Amazon DynamoDB (sesiones por UUID)
- **RAG**: Bedrock Knowledge Base + OpenSearch Serverless + Titan Embeddings V2
- **IaC**: AWS SAM (CloudFormation)
- **Frontend**: Streamlit

---

## Inicio rápido

### Requisitos previos

- Python 3.12+
- AWS CLI v2 configurado con perfil SSO (`aws sso login`)
- Docker (para `sam build --use-container`)
- SAM CLI (se instala automáticamente si no está)

### 1. Clonar e instalar dependencias

```bash
git clone https://github.com/ai-scm/2026-q4_a-strands1-yohanospina.git
cd 2026-q4_a-strands1-yohanospina
python3 -m venv .venv
.venv/bin/pip install -r src/requirements.txt
.venv/bin/pip install streamlit requests
```

### 2. Login en AWS

```bash
aws sso login --profile blend360
```

### 3. Levantar todo el stack en AWS

```bash
./deploy.sh
```

El script hace automáticamente:
- Build de la Lambda con Docker
- Deploy del stack SAM (Lambda + DynamoDB + IAM + Function URL)
- Creación del bucket S3 y subida de `travel_guides.txt`
- Sincronización de la Knowledge Base
- Muestra la URL del agente al finalizar

> **Primera vez:** si la Knowledge Base no existe, el script te guía para crearla en la consola de Bedrock (~2 min).

### 4. Abrir la interfaz gráfica

```bash
.venv/bin/streamlit run app.py
```

Abre `http://localhost:8501` en el navegador.

---

## Apagar (dejar costo en $0)

```bash
./teardown.sh
```

Elimina la Knowledge Base (OpenSearch Serverless ~$0.24/hora) y el stack SAM. El código queda intacto en Git. Para volver a levantar: `./deploy.sh`.

---

## Prueba rápida desde terminal

```bash
# Vuelos
curl -s -X POST https://<TU_LAMBDA_URL>/ \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What airlines fly to Seattle?", "user": {"session_id": "test"}}'

# Tours
curl -s -X POST https://<TU_LAMBDA_URL>/ \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What tours are available in Bogota?", "user": {"session_id": "test"}}'

# Clima
curl -s -X POST https://<TU_LAMBDA_URL>/ \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is the weather in Seattle?", "user": {"session_id": "test"}}'
```

---

## Estructura del proyecto

```
skillbuilder-strands/
├── src/
│   ├── lambda_function.py    # Handler Lambda: agente Strands + 3 tools
│   └── requirements.txt      # Dependencias Lambda (strands-agents, boto3)
├── app.py                    # Frontend Streamlit
├── agent.py                  # Prototipo local del agente (consola)
├── test_agent.py             # Test de conectividad con Bedrock
├── template.yaml             # IaC: Lambda, DynamoDB, IAM, Function URL
├── samconfig.toml            # Config de deploy SAM
├── deploy.sh                 # Script: levanta todo el stack
├── teardown.sh               # Script: apaga todo, costo $0
├── travel_guides.txt         # Documentos fuente para la Knowledge Base
└── .gitignore
```

---

## Costos en reposo

| Componente | Costo sin tráfico |
|---|---|
| Lambda | $0.00 |
| DynamoDB | $0.00 |
| Bedrock (Nova Lite) | $0.00 |
| **OpenSearch Serverless (KB)** | **~$0.24/hora** |
| S3 | ~$0.00 |

Ejecuta `./teardown.sh` cuando no lo estés usando.
