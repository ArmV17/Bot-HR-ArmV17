import os
import asyncio
from dotenv import load_dotenv
from highrise import BaseBot, User, Position
from highrise.__main__ import BotDefinition, main

# --- IMPORTACIONES DE TUS CARPETAS ---
from funciones.moderacion.seguridad import registrar_entrada
from funciones.moderacion.comandos import manejar_moderacion

load_dotenv()

class MyBot(BaseBot):
    async def on_start(self, session_metadata):
        print("Bot V17: Sistema de Seguridad y Comandos Activos.")

    # Evento: Alguien entra a la sala
    async def on_user_join(self, user: User, position: Position):
        # Registra en Supabase
        await registrar_entrada(self, user)

    # Evento: Alguien escribe en el chat
    async def on_chat(self, user: User, message: str):
        # 1. Ejecutar lógica de moderación (Kick, etc.)
        await manejar_moderacion(self, user, message)

        # 2. Comandos directos o informativos
        if message.lower() == "!mi_id":
            await self.highrise.chat(f"Tu ID registrado es: {user.id}")

if __name__ == "__main__":
    room_id = os.getenv("ROOM_ID")
    api_token = os.getenv("BOT_TOKEN")

    # Verificación de seguridad antes de arrancar
    if not room_id or not api_token:
        print("❌ ERROR: No se encontraron ROOM_ID o BOT_TOKEN en el .env")
    else:
        definitions = [BotDefinition(MyBot(), room_id, api_token)]
        asyncio.run(main(definitions))