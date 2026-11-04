#!/bin/bash
# ============================================================
#  deploy.sh — Levanta el stack completo del Agente de Viajes
#  Uso: ./deploy.sh
# ============================================================
set -e

PROFILE="blend360"
REGION="us-east-1"
STACK_NAME="strands-agent-stack"
KB_NAME="strands-travel-guides"
DOCS_BUCKET="strands-travel-docs-891377180652"
TRAVEL_FILE="travel_guides.txt"

echo ""
echo "================================================"
echo "  Agente de Viajes — Deploy completo"
echo "================================================"

# 1. Verificar credenciales AWS
echo ""
echo "[1/5] Verificando credenciales AWS..."
aws sts get-caller-identity --profile $PROFILE --region $REGION > /dev/null 2>&1 || {
    echo "  ⚠️  Sesión SSO expirada. Ejecuta:"
    echo "      aws sso login --profile $PROFILE"
    exit 1
}
echo "  ✅ Credenciales OK"

# 2. Build y Deploy del stack SAM (Lambda + DynamoDB + IAM + Function URL)
echo ""
echo "[2/5] Build y Deploy del stack SAM..."
~/.local/bin/sam build --use-container --quiet
~/.local/bin/sam deploy \
    --profile $PROFILE \
    --no-confirm-changeset \
    --no-fail-on-empty-changeset 2>&1 | grep -E "UPDATE|CREATE|Error|Successfully|Value"
echo "  ✅ Stack desplegado"

# 3. Crear bucket S3 y subir travel_guides.txt (si no existe)
echo ""
echo "[3/5] Verificando bucket S3 con documentos..."
aws s3api head-bucket --bucket $DOCS_BUCKET --profile $PROFILE 2>/dev/null || {
    echo "  Creando bucket $DOCS_BUCKET..."
    aws s3api create-bucket --bucket $DOCS_BUCKET --region $REGION --profile $PROFILE > /dev/null
}
aws s3 cp $TRAVEL_FILE s3://$DOCS_BUCKET/$TRAVEL_FILE --profile $PROFILE > /dev/null
echo "  ✅ Bucket S3 listo con $TRAVEL_FILE"

# 4. Verificar/Crear Knowledge Base
echo ""
echo "[4/5] Verificando Knowledge Base..."
KB_ID=$(aws bedrock-agent list-knowledge-bases \
    --region $REGION --profile $PROFILE \
    --query "knowledgeBaseSummaries[?name=='$KB_NAME'].knowledgeBaseId" \
    --output text 2>/dev/null)

if [ -z "$KB_ID" ]; then
    echo ""
    echo "  ⚠️  La Knowledge Base no existe."
    echo "      Debes crearla manualmente (1 vez, ~2 min):"
    echo ""
    echo "      1. Ve a: https://console.aws.amazon.com/bedrock/home?region=us-east-1#/knowledge-bases"
    echo "      2. Clic en 'Create knowledge base' → 'Knowledge base with vector store'"
    echo "      3. Nombre: strands-travel-guides"
    echo "      4. Data source: S3 → s3://$DOCS_BUCKET/$TRAVEL_FILE"
    echo "      5. Embedding model: Titan Text Embeddings V2"
    echo "      6. Vector store: Quick create (OpenSearch Serverless)"
    echo "      7. Copia el Knowledge Base ID y vuelve a ejecutar este script"
    echo ""
    echo "      O pasa el ID directamente:"
    echo "      ./deploy.sh <KNOWLEDGE_BASE_ID>"
    exit 0
else
    echo "  ✅ Knowledge Base encontrada: $KB_ID"

    # Actualizar el template con el KB ID si cambió
    CURRENT_KB=$(grep "KNOWLEDGE_BASE_ID" template.yaml | grep -o '"[A-Z0-9]*"' | tr -d '"')
    if [ "$CURRENT_KB" != "$KB_ID" ]; then
        echo "  Actualizando KNOWLEDGE_BASE_ID en template.yaml..."
        sed -i "s/KNOWLEDGE_BASE_ID: \"$CURRENT_KB\"/KNOWLEDGE_BASE_ID: \"$KB_ID\"/" template.yaml
        # Redeploy con el KB ID correcto
        ~/.local/bin/sam build --use-container --quiet
        ~/.local/bin/sam deploy \
            --profile $PROFILE \
            --no-confirm-changeset \
            --no-fail-on-empty-changeset 2>&1 | grep -E "UPDATE|CREATE|Successfully"
    fi

    # Sincronizar data source
    echo "  Sincronizando documentos con la Knowledge Base..."
    DS_ID=$(aws bedrock-agent list-data-sources \
        --knowledge-base-id $KB_ID \
        --region $REGION --profile $PROFILE \
        --query 'dataSourceSummaries[0].dataSourceId' \
        --output text)
    aws bedrock-agent start-ingestion-job \
        --knowledge-base-id $KB_ID \
        --data-source-id $DS_ID \
        --region $REGION --profile $PROFILE > /dev/null
    echo "  ✅ Sincronización iniciada (tarda ~1 min)"
fi

# 5. Obtener y mostrar la URL final
echo ""
echo "[5/5] Obteniendo URL del agente..."
LAMBDA_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION --profile $PROFILE \
    --query 'Stacks[0].Outputs[?OutputKey==`StrandsAgentFunctionUrl`].OutputValue' \
    --output text)

echo ""
echo "================================================"
echo "  ✅ Todo listo!"
echo "================================================"
echo ""
echo "  URL del agente: $LAMBDA_URL"
echo ""
echo "  Para abrir la interfaz gráfica:"
echo "  .venv/bin/streamlit run app.py"
echo ""
echo "  Prueba rápida:"
echo "  curl -s -X POST $LAMBDA_URL \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"prompt\": \"What airlines fly to Seattle?\", \"user\": {\"session_id\": \"test\"}}'"
echo ""
