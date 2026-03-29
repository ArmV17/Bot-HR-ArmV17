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
        print("Bot V17: Sistema de Seguridad y Comandos Activos (Chat + Whisper).")

    # Evento: Alguien entra a la sala
    async def on_user_join(self, user: User, position: Position):
        await registrar_entrada(self, user)

    # Evento: Alguien escribe en el chat PÚBLICO
    async def on_chat(self, user: User, message: str):
        # 1. Ejecutar lógica de moderación
        await manejar_moderacion(self, user, message)

        # 2. Comandos informativos en público
        if message.lower() == "!mi_id":
            await self.highrise.chat(f"@{user.username}, tu ID es: {user.id}")

    # Evento: Alguien le SUSURRA al bot
    async def on_whisper(self, user: User, message: str):
        # 1. También permitimos moderar por susurro para mayor discreción
        await manejar_moderacion(self, user, message)

        # 2. Comandos informativos por susurro
        if message.lower() == "!mi_id":
            await self.highrise.send_whisper(user.id, f"Tu ID es: {user.id}")

if __name__ == "__main__":
    room_id = os.getenv("ROOM_ID")
    api_token = os.getenv("BOT_TOKEN")

    if not room_id or not api_token:
        print("❌ ERROR: No se encontraron ROOM_ID o BOT_TOKEN en el .env")
    else:
        definitions = [BotDefinition(MyBot(), room_id, api_token)]
        asyncio.run(main(definitions))