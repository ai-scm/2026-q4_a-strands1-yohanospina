#!/bin/bash
# ============================================================
#  teardown.sh — Apaga todo para no generar costos en AWS
#  El código queda en Git, se puede volver a levantar con deploy.sh
#  Uso: ./teardown.sh
# ============================================================
set -e

PROFILE="blend360"
REGION="us-east-1"
STACK_NAME="strands-agent-stack"
KB_NAME="strands-travel-guides"

echo ""
echo "================================================"
echo "  Agente de Viajes — Teardown (apagar todo)"
echo "================================================"
echo ""
echo "  Esto elimina:"
echo "  - Lambda Function"
echo "  - DynamoDB (historial de sesiones)"
echo "  - IAM Role de la Lambda"
echo "  - Function URL"
echo "  - Knowledge Base + OpenSearch Serverless (~\$0.24/hora)"
echo ""
echo "  NO elimina:"
echo "  - El código (sigue en Git)"
echo "  - El bucket S3 con travel_guides.txt"
echo "  - El bucket S3 de artefactos SAM"
echo ""
read -p "  ¿Confirmar? (escribe 'si' para continuar): " CONFIRM
if [ "$CONFIRM" != "si" ]; then
    echo "  Cancelado."
    exit 0
fi

# 1. Eliminar Knowledge Base (el más costoso en reposo)
echo ""
echo "[1/2] Eliminando Knowledge Base..."
KB_ID=$(aws bedrock-agent list-knowledge-bases \
    --region $REGION --profile $PROFILE \
    --query "knowledgeBaseSummaries[?name=='$KB_NAME'].knowledgeBaseId" \
    --output text 2>/dev/null)

if [ -n "$KB_ID" ]; then
    aws bedrock-agent delete-knowledge-base \
        --knowledge-base-id $KB_ID \
        --region $REGION --profile $PROFILE > /dev/null
    echo "  ✅ Knowledge Base $KB_ID eliminada"
else
    echo "  ℹ️  Knowledge Base no encontrada, omitiendo"
fi

# 2. Eliminar stack SAM (Lambda + DynamoDB + IAM)
echo ""
echo "[2/2] Eliminando stack SAM ($STACK_NAME)..."
~/.local/bin/sam delete \
    --stack-name $STACK_NAME \
    --region $REGION \
    --profile $PROFILE \
    --no-prompts 2>&1 | grep -E "Deleted|Error|Successfully" || true
echo "  ✅ Stack eliminado"

echo ""
echo "================================================"
echo "  ✅ Todo apagado. Costo en AWS: \$0.00/hora"
echo "================================================"
echo ""
echo "  Para volver a levantar todo:"
echo "  ./deploy.sh"
echo ""
