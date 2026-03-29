import os
import asyncio
from dotenv import load_dotenv
from highrise import BaseBot, User, Position
from highrise.__main__ import BotDefinition, main

# Cargar las variables del archivo .env
load_dotenv()

class MyBot(BaseBot):
    async def on_start(self, session_metadata):
        print("¡Bot de High Rise encendido y listo!")

    async def on_chat(self, user: User, message: str):
        if message.lower() == "!hola":
            await self.highrise.chat(f"¡Hola {user.username}!")

# Ejecución
if __name__ == "__main__":
    room_id = os.getenv("ROOM_ID")
    api_token = os.getenv("BOT_TOKEN")
    
    # IMPORTANTE: Aquí pasamos directamente la clase MyBot
    definitions = [
        BotDefinition(
            MyBot(), 
            room_id, 
            api_token
        )
    ]
    
    asyncio.run(main(definitions))