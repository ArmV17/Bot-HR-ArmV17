from highrise import BaseBot, User
from funciones.db import supabase
from funciones.db import supabase, registrar_moderacion

async def obtener_rol(user_id: str):
    # Consultamos el rol en la base de datos
    response = supabase.table("usuarios").select("rol").eq("id_jugador", user_id).execute()
    if response.data:
        return response.data[0]['rol']
    return "usuario"

async def manejar_moderacion(bot: BaseBot, user: User, message: str):
    msg = message.lower()
    if not msg.startswith("!"): return

    rol = await obtener_rol(user.id)
    
    if msg.startswith("!kick "):
        if rol not in ["admin", "owner"]:
            await bot.highrise.chat(f"❌ @{user.username}, no tienes rango.")
            return

        target_username = msg.replace("!kick @", "").strip()
        
        room_users = await bot.highrise.get_room_users()
        target_user = next((u[0] for u in room_users.content if u[0].username.lower() == target_username.lower()), None)

        if target_user:
            try:
                # 1. Ejecutamos la moderación
                await bot.highrise.moderate_room(target_user.id, "kick")
                
                # 2. GUARDAMOS EN EL HISTORIAL
                registrar_moderacion(
                    ejecutor=user.username, 
                    objetivo=target_user.username, 
                    accion="kick"
                )
                
                await bot.highrise.chat(f"👞 {target_username} expulsado y registrado en historial.")
            except Exception as e:
                await bot.highrise.chat(f"⚠️ Error: {e}")
        else:
            await bot.highrise.chat(f"❓ No veo a @{target_username}.")