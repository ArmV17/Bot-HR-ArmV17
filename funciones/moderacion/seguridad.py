from highrise import BaseBot, User
from funciones.db import guardar_usuario_db # Importamos la DB

async def registrar_entrada(bot: BaseBot, user: User):
    # Guardamos en la nube (Supabase)
    guardar_usuario_db(user.id, user.username)
    
    # Mensaje de log
    print(f"Seguridad: Registrado {user.username} con ID {user.id}")