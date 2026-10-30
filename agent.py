import datetime
import json
import urllib.request

from strands import Agent, tool
from strands.models import BedrockModel

# 1. Definición de Herramientas (Tools)
@tool
def get_current_time() -> str:
    """Devuelve la fecha y hora actual del sistema."""
    now = datetime.datetime.now()
    return f"La fecha y hora actual es: {now.strftime('%Y-%m-%d %H:%M:%S')}"


@tool
def calculate_discount(price: float, discount_percentage: float) -> str:
    """Calcula el precio final aplicando un porcentaje de descuento."""
    final_price = price * (1 - discount_percentage / 100)
    return f"El precio final con un {discount_percentage}% de descuento es {final_price:.2f}"


@tool
def get_weather(city: str) -> str:
    """Obtiene el clima en tiempo real de una ciudad realizando una petición HTTP a una API externa."""
    try:
        coords = {
            "nueva york": (40.7128, -74.0060),
            "bogota": (4.7110, -74.0721),
            "madrid": (40.4168, -3.7038),
        }
        city_clean = city.lower().strip()
        lat, lon = coords.get(city_clean, (40.7128, -74.0060))
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        req = urllib.request.Request(
            url, headers={"User-Agent": "StrandsAgent/1.0"}
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            temp = data["current_weather"]["temperature"]
            return f"El clima actual en {city} reporta una temperatura de {temp}°C."
    except Exception as e:
        return f"No se pudo obtener el clima para {city}: {str(e)}"


# 2. Configuración con un System Prompt Estructurado
model = BedrockModel(model_id="amazon.nova-pro-v1:0", region_name="us-east-1")

# Nuevo System Prompt con formato de reporte obligatorio
SYSTEM_PROMPT = """
Eres un Asistente Ejecutivo de Viajes y Finanzas. Tus respuestas DEBEN seguir SIEMPRE la siguiente estructura en viñetas:
- [USUARIO]: Nombre del usuario (si se conoce)
- [RESUMEN]: Breve resumen de la solicitud
- [DETALLES DE HERRAMIENTAS]: Datos obtenidos de las herramientas utilizadas
- [RECOMENDACIÓN]: Una sugerencia o paso a seguir breve.
"""

agent = Agent(
    model=model,
    tools=[get_current_time, calculate_discount, get_weather],
    system_prompt=SYSTEM_PROMPT,
)

# 3. Bucle Interactivo en Consola
if __name__ == "__main__":
    print("¡Agente Strands Activo! Escribe 'salir' para finalizar.\n")
    while True:
        user_input = input("Tú: ")
        if user_input.lower().strip() in ["salir", "exit", "quit"]:
            print("¡Hasta luego!")
            break
        if not user_input.strip():
            continue
        response = agent(user_input)
        print(f"\nAgente:\n{response}\n" + "-" * 50 + "\n")