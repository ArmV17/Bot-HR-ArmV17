from highrise import BaseBot, User
from funciones.db import supabase, registrar_moderacion

async def obtener_rol(user_id: str):
    response = supabase.table("usuarios").select("rol").eq("id_jugador", user_id).execute()
    if response.data:
        return response.data[0]['rol']
    return "usuario"

async def manejar_moderacion(bot: BaseBot, user: User, message: str):
    msg = message.lower()
    if not msg.startswith("!"): return

    rol = await obtener_rol(user.id)
    if rol not in ["admin", "owner"]:
        return 

    # --- COMANDO KICK ---
    if msg.startswith("!kick @"):
        target_username = msg.replace("!kick @", "").strip()
        await ejecutar_accion(bot, user, target_username, "kick")

    # --- COMANDO MUTE ---
    elif msg.startswith("!mute @"):
        partes = msg.split()
        if len(partes) < 3:
            # Respuesta en privado si el comando está mal escrito
            await bot.highrise.send_whisper(user.id, "❌ Uso: !mute @nombre segundos")
            return
        target_username = partes[1].replace("@", "")
        try:
            segundos = int(partes[2])
            await ejecutar_accion(bot, user, target_username, "mute", segundos)
        except ValueError:
            await bot.highrise.send_whisper(user.id, "❌ Error: Los segundos deben ser un número.")

    # --- COMANDO UNMUTE ---
    elif msg.startswith("!unmute @"):
        target_username = msg.replace("!unmute @", "").strip()
        await ejecutar_accion(bot, user, target_username, "mute", 1)

    # --- COMANDO BAN ---
    elif msg.startswith("!ban @"):
        target_username = msg.replace("!ban @", "").strip()
        await ejecutar_accion(bot, user, target_username, "ban", 86400)

async def ejecutar_accion(bot, ejecutor, target_name, accion, tiempo=None):
    room_users = await bot.highrise.get_room_users()
    target_user = next((u[0] for u in room_users.content if u[0].username.lower() == target_name.lower()), None)

    if target_user:
        try:
            if accion == "kick":
                await bot.highrise.moderate_room(target_user.id, "kick")
            elif accion == "mute":
                await bot.highrise.moderate_room(target_user.id, "mute", tiempo)
            elif accion == "ban":
                await bot.highrise.moderate_room(target_user.id, "ban", tiempo)

            # Registro en DB
            registrar_moderacion(ejecutor.username, target_user.username, accion)
            
            # RESPUESTA EN PRIVADO AL EJECUTOR
            await bot.highrise.send_whisper(ejecutor.id, f"✅ Has aplicado {accion.upper()} a @{target_name}")

        except Exception as e:
            if "moderate moderators" in str(e):
                await bot.highrise.send_whisper(ejecutor.id, f"⚠️ No puedo moderar a @{target_name} (es moderador).")
            else:
                await bot.highrise.send_whisper(ejecutor.id, f"❌ Error técnico: {e}")
    else:
        # Respuesta en privado si el usuario no está
        await bot.highrise.send_whisper(ejecutor.id, f"❓ No encontré a @{target_name} en la sala.")