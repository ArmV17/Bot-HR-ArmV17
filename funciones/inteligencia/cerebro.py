import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configuración de la API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Personalidad de Steffi
instruccion_steffi = (
    "Eres Steffi, la bot estrella de esta sala en Highrise. "
    "Tu personalidad es ingeniosa, divertida y un poco sarcástica. "
    "Te gusta el chisme de la sala pero eres leal a tus amigos. "
    "REGLA: Responde siempre en menos de 140 caracteres. Usa emojis ocasionales. "
    "No seas demasiado amigable, mantén ese toque de 'reina de la sala'."
)

# Usamos el nombre de modelo más estándar
# Si sigue fallando, cambia "gemini-1.5-flash" por "gemini-pro"
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=instruccion_steffi
)

async def generar_respuesta_ia(user_name, mensaje_usuario):
    try:
        # Generar contenido
        response = model.generate_content(f"El usuario {user_name} dice: {mensaje_usuario}")
        
        if response and response.text:
            return response.text.strip()
        else:
            return "Ay, me quedé pensando en qué outfit ponerme. ¿Qué decías? 💅"

    except Exception as e:
        # Imprimimos el error para debuggear
        print(f"Error en el cerebro de Steffi: {e}")
        return "Ay, mi sistema se puso lento. ¿Podrías repetir eso? 💅"