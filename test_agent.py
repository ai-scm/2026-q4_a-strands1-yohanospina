from strands import Agent
from strands.models import BedrockModel

model = BedrockModel(
    model_id="amazon.nova-pro-v1:0",
    region_name="us-east-1"
)

agent = Agent(model=model)

response = agent("Hola, confirma si estás activo y disponible.")
print(response)