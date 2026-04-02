from highrise import BaseBot, User
from funciones.movimiento.perimetro import supabase

async def asignar_rango_manual(bot: BaseBot, user: User, message: str):
    """
    Comando: rango @usuario [fundador/admin/usuario]
    Restricción: Exclusivo para _Armando_17_
    """
    # 1. BLOQUEO DE SEGURIDAD PARA EL FUNDADOR SUPREMO
    if user.username.lower() != "_armando_17_":
        await bot.highrise.send_whisper(user.id, "⛔ Solo El Fundador supremo tiene autoridad para cambiar rangos.")
        return

    try:
        parts = message.split()
        if len(parts) < 3:
            await bot.highrise.send_whisper(user.id, "❌ Uso: rango @usuario [fundador/admin/usuario]")
            return

        target_username = parts[1].replace("@", "").lower()
        nuevo_rol = parts[2].lower().strip()

        # 2. VALIDACIÓN DE TUS 3 RANGOS ESPECÍFICOS
        rangos_permitidos = ["fundador", "admin", "usuario"]
        if nuevo_rol not in rangos_permitidos:
            await bot.highrise.send_whisper(user.id, f"❌ '{nuevo_rol}' no es un rango válido (fundador, admin, usuario).")
            return

        # 3. LOCALIZAR AL USUARIO EN LA SALA
        room_users = (await bot.highrise.get_room_users()).content
        target_user = next((u for u, p in room_users if u.username.lower() == target_username), None)

        if target_user:
            # 4. ACTUALIZACIÓN EN LA TABLA 'usuarios'
            try:
                # Usamos upsert para actualizar el rol basado en el id_jugador
                supabase.table("usuarios").upsert({
                    "id_jugador": target_user.id,
                    "username": target_username,
                    "rol": nuevo_rol
                }).execute()

                await bot.highrise.chat(f"👑 @{user.username} ha actualizado el rango de @{target_username} a: {nuevo_rol.upper()}")
            except Exception as e:
                print(f"Error actualizando rol en Supabase: {e}")
                await bot.highrise.send_whisper(user.id, "❌ Error técnico al conectar con la base de datos.")
        else:
            await bot.highrise.send_whisper(user.id, f"❌ El usuario @{target_username} debe estar en la sala para cambiar su rango.")

    except Exception as e:
        print(f"Error en asignar_rango_manual: {e}")