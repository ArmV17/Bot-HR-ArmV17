import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configuración de Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Definimos la personalidad de Steffi
instruccion_steffi = (
    "Eres Steffi, la bot estrella de esta sala en Highrise. "
    "Personalidad: Ingeniosa, divertida y un poco sarcástica. "
    "Te gusta el chisme de la sala pero eres leal a tus amigos. "
    "REGLA: Responde siempre en menos de 140 caracteres. Usa emojis ocasionales. "
    "No seas demasiado amigable, mantén ese toque de 'reina de la sala'."
)

# Cambiamos a 'gemini-1.5-flash-latest' que es el modelo más compatible actualmente
try:
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash-latest", 
        system_instruction=instruccion_steffi
    )
except:
    # Si el anterior falla, usamos el básico
    model = genai.GenerativeModel(model_name="gemini-pro")

async def generar_respuesta_ia(user_name, mensaje_usuario):
    try:
        # Enviamos el contexto del usuario
        prompt = f"El usuario {user_name} dice: {mensaje_usuario}"
        
        # Generar respuesta
        response = model.generate_content(prompt)
        
        if response and response.text:
            return response.text.strip()
        else:
            return "Ay, me quedé procesando... literal. 💅"

    except Exception as e:
        print(f"Error en el cerebro de Steffi: {e}")
        return "Ay, mi sistema se puso lento. ¿Podrías repetir eso? 💅"