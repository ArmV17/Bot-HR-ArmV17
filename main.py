import os
import asyncio
from dotenv import load_dotenv
from highrise import BaseBot, User, Position
from highrise.__main__ import BotDefinition, main

# Importamos la función de seguridad
from funciones.moderacion.seguridad import registrar_entrada

load_dotenv()

class MyBot(BaseBot):
    async def on_start(self, session_metadata):
        print("Bot V17: Sistema de Seguridad Activo.")

    # Este evento se dispara CADA VEZ que alguien entra
    async def on_user_join(self, user: User, position: Position):
        # Llamamos a nuestra función pasándole el bot y el usuario
        await registrar_entrada(self, user)

    async def on_chat(self, user: User, message: str):
        # Aquí puedes usar los datos guardados si lo necesitas
        if message.lower() == "!mi_id":
            await self.highrise.chat(f"Tu ID registrado es: {user.id}")

if __name__ == "__main__":
    definitions = [BotDefinition(MyBot(), os.getenv("ROOM_ID"), os.getenv("BOT_TOKEN"))]
    asyncio.run(main(definitions))