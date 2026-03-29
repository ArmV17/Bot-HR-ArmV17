from highrise import BaseBot, User, Position

class MyBot(BaseBot):
    async def on_start(self, session_metadata):
        print("¡El bot está en línea!")

    async def on_chat(self, user: User, message: str):
        print(f"{user.username} dijo: {message}")
        
        # Ejemplo: El bot responde a un saludo
        if message.lower().startswith("hola"):
            await self.highrise.chat(f"¡Hola {user.username}! Bienvenido a la sala.")

    async def on_user_join(self, user: User, position: Position):
        print(f"{user.username} ha entrado en la sala.")
        await self.highrise.chat(f"Bienvenido @{user.username}")