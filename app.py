import uuid
import requests
import streamlit as st

# Configuración de página sin barra lateral
st.set_page_config(
    page_title="Agente de Viajes IA",
    page_icon="✈️",
    initial_sidebar_state="collapsed",
)

st.title("✈️ Agente de Viajes con Strands SDK & Amazon Bedrock")

# URL de la API Gateway / Lambda Function URL
LAMBDA_URL = (
    "https://pxohlk3jp26643sar7qi3yjimm0gqxqu.lambda-url.us-east-1.on.aws/"
)

# Inicialización automática de ID de sesión y mensajes
if "session_id" not in st.session_state:
    st.session_state.session_id = f"sesion_{uuid.uuid4().hex[:6]}"

if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar el historial del chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Entrada de mensajes del usuario
if prompt := st.chat_input("Escribe tu consulta sobre tours o viajes..."):
    # Guardar y mostrar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Enviar la consulta al backend
    with st.chat_message("assistant"):
        with st.spinner("Consultando agente de viajes..."):
            try:
                payload = {
                    "prompt": prompt,
                    "user": {"session_id": st.session_state.session_id},
                }
                response = requests.post(LAMBDA_URL, json=payload, timeout=90)
                if response.status_code == 200:
                    data = response.json()
                    # Extraer respuesta según el formato retornado
                    if isinstance(data, dict) and "response" in data:
                        res_text = data["response"]
                    else:
                        res_text = str(data)
                    st.write(res_text)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": res_text}
                    )
                else:
                    st.error(
                        f"Error en el servidor ({response.status_code}):"
                        f" {response.text}"
                    )
            except Exception as e:
                st.error(f"Error de conexión: {str(e)}")
