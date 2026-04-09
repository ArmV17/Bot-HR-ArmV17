import os
import subprocess
import sys
import asyncio
from highrise import User

def convertir_tiempo_a_segundos(tiempo_str):
    """Convierte formatos como 60m, 1h, 1d a segundos."""
    if not tiempo_str:
        return None
    
    unidad = tiempo_str[-1].lower()
    try:
        valor = int(tiempo_str[:-1])
    except ValueError:
        return None

    if unidad == 'm': return valor * 60
    elif unidad == 'h': return valor * 3600
    elif unidad == 'd': return valor * 84600
    return None

async def rentar_bot(bot, user: User, message: str):
    """
    Comando: rentar [TOKEN] [ROOM_ID] [TIEMPO]
    """
    # Seguridad: Solo tú
    if user.username != "_Armando_17_":
        return

    try:
        parts = message.split()
        if len(parts) < 3:
            await bot.highrise.send_whisper(user.id, "❌ Uso: rentar [TOKEN] [ID_SALA] [TIEMPO(opcional)]")
            return

        token = parts[1]
        sala_destino = parts[2]
        tiempo_str = parts[3] if len(parts) > 3 else None
        
        segundos = convertir_tiempo_a_segundos(tiempo_str)
        sala_original = os.getenv("ROOM_ID")

        await bot.highrise.send_whisper(user.id, f"💼 Rentando bot en sala {sala_destino}...")

        nuevo_env = os.environ.copy()
        nuevo_env["BOT_TOKEN"] = token
        nuevo_env["ROOM_ID"] = sala_destino
        
        if segundos:
            nuevo_env["TIEMPO_RENTA"] = str(segundos)
            nuevo_env["SALA_REGRESO"] = sala_original

        # Lanzamos el proceso
        subprocess.Popen(
            [sys.executable, "main.py"],
            env=nuevo_env,
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
        )

    except Exception as e:
        await bot.highrise.send_whisper(user.id, f"❌ Error en renta: {e}")

async def apagar_bot_actual(bot, user: User):
    """Comando para cerrar el proceso del bot actual."""
    if user.username != "_Armando_17_":
        return
    
    await bot.highrise.chat("👋 Apagado manual activado. ¡Hasta luego!")
    await asyncio.sleep(2)
    os._exit(0)