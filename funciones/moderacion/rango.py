from highrise import BaseBot, User
from funciones.db import supabase # Importación centralizada

async def asignar_rango_manual(bot: BaseBot, user: User, message: str):
    """Exclusivo para Armando."""
    if user.username.lower() != "_armando_17_":
        await bot.highrise.send_whisper(user.id, "⛔ Solo el Fundador Supremo puede cambiar rangos.")
        return

    try:
        parts = message.split()
        if len(parts) < 3:
            await bot.highrise.send_whisper(user.id, "❌ Uso: rango @usuario [fundador/admin/usuario]")
            return

        target_username = parts[1].replace("@", "").lower()
        nuevo_rol = parts[2].lower().strip()

        if nuevo_rol not in ["fundador", "admin", "usuario", "owner"]:
            await bot.highrise.send_whisper(user.id, f"❌ '{nuevo_rol}' no es un rango válido.")
            return

        room_users = await bot.highrise.get_room_users()
        target_user = next((u for u, p in room_users.content if u.username.lower() == target_username), None)

        if target_user:
            supabase.table("usuarios").upsert({
                "id_jugador": target_user.id,
                "username": target_username,
                "rol": nuevo_rol
            }).execute()
            await bot.highrise.chat(f"👑 @{user.username} ha actualizado el rango de @{target_username} a: {nuevo_rol.upper()}")
        else:
            await bot.highrise.send_whisper(user.id, f"❌ @{target_username} no está en la sala.")
    except Exception as e:
        print(f"⚠️ Error en rango: {e}")