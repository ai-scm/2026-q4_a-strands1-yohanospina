import json
import os
import urllib.request
from typing import Any, Dict

import boto3
from strands import Agent, tool

# Lectura segura de la variable de entorno para evitar KeyError al importar
SESSIONS_TABLE_NAME = os.environ.get("SESSION_TABLE_NAME", "StrandsAgentSessions")
ddb = boto3.resource("dynamodb")
table = ddb.Table(SESSIONS_TABLE_NAME)


def get_session_history(session_id: str) -> list:
    """Recupera el historial de conversación desde DynamoDB."""
    try:
        response = table.get_item(Key={"SessionId": session_id})
        if "Item" in response:
            return json.loads(response["Item"]["messages"])
        return []
    except Exception as e:
        print(f"Error recuperando historial: {e}")
        return []


def save_session_history(session_id: str, messages: list) -> None:
    """Guarda el historial actualizado en DynamoDB."""
    try:
        table.put_item(
            Item={"SessionId": session_id, "messages": json.dumps(messages)}
        )
    except Exception as e:
        print(f"Error guardando historial: {e}")


@tool
def retrieve(query: str) -> str:
    """Search the travel guides knowledge base in Bedrock for tours, activities, guides, and attractions.

    Args:
        query: The search query or question about tours and travel guides.
    """
    kb_id = os.environ.get("KNOWLEDGE_BASE_ID", "")
    if not kb_id:
        return "Knowledge Base ID no está configurada en las variables de entorno."

    client = boto3.client("bedrock-agent-runtime", region_name="us-east-1")
    try:
        res = client.retrieve(
            knowledgeBaseId=kb_id, retrievalQuery={"text": query}
        )
        results = res.get("retrievalResults", [])
        if not results:
            return "No se encontró información relevante en la guía turística."
        chunks = [
            r["content"]["text"]
            for r in results
            if "content" in r and "text" in r["content"]
        ]
        return "\n---\n".join(chunks)
    except Exception as e:
        print(f"ERROR en retrieve tool: {type(e).__name__}: {str(e)}")
        return f"Error consultando la Knowledge Base: {str(e)}"


@tool
def http_request(url: str) -> str:
    """Make an HTTP GET request to an external API.

    Args:
        url: The full URL to request
    """
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "StrandsAgent/1.0"}
        )
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        return f"Error en la petición HTTP: {str(e)}"


@tool
def flight_search(city: str) -> dict:
    """Get available flight options to a city.

    Args:
        city: The name of the city
    """
    flights = {
        "Atlanta": ["AnyCompany01 Airlines", "AnyCompany09 Airlines"],
        "Seattle": ["AnyCompany05 Airlines", "AnyCompany02 Airlines"],
        "New York": ["AnyCompany03 Airlines", "AnyCompany08 Airlines"],
    }
    return flights.get(city, ["Standard Regional Airlines"])


TRAVEL_AGENT_PROMPT = """You are a travel assistant that can help customers book their travel. 
1. If a customer wants flight options or carriers, use the flight_search tool. 
2. If a customer asks about tour operators, tours, water activities, or local guides, ALWAYS use the retrieve tool to search the Bedrock Knowledge Base. 
3. If a customer asks about weather in the United States, use http_request to fetch forecast data from the National Weather Service API (https://api.weather.gov/points/{lat},{lon} or zip code 98101 for Seattle: 47.6061, -122.3328). 
Be helpful and concise."""


def handler(event: Dict[str, Any], _context) -> Dict[str, Any]:
    try:
        if "body" in event and isinstance(event["body"], str):
            body_data = json.loads(event["body"])
        elif "body" in event and isinstance(event["body"], dict):
            body_data = event["body"]
        else:
            body_data = event

        prompt = body_data.get("prompt", "")
        user_info = body_data.get("user", {})
        session_id = user_info.get("session_id", "default_session")

        history = get_session_history(session_id)

        # Convertir historial plano al formato de mensajes que espera Strands
        strands_messages = []
        for msg in history:
            strands_messages.append({
                "role": msg["role"],
                "content": [{"text": msg["content"]}]
            })

        agent = Agent(
            model="us.amazon.nova-lite-v1:0",
            system_prompt=TRAVEL_AGENT_PROMPT,
            tools=[flight_search, http_request, retrieve],
            messages=strands_messages,
        )

        response_text = str(agent(prompt))

        history.append({"role": "user", "content": prompt})
        history.append({"role": "assistant", "content": response_text})

        save_session_history(session_id, history)

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"response": response_text}),
        }
    except Exception as e:
        print(f"Error procesando solicitud en Lambda: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {"error": f"Error interno en Lambda: {str(e)}"}
            ),
        }