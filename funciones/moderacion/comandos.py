from highrise import BaseBot, User
from funciones.db import supabase, registrar_moderacion

async def obtener_rol(user_id: str):
    """Consulta el tier del usuario con protección contra Lag."""
    try:
        # Timeout implícito al usar execute()
        response = supabase.table("usuarios").select("rol").eq("id_jugador", user_id).execute()
        if response.data:
            return response.data[0]['rol'].lower()
    except Exception as e:
        print(f"⚠️ Error consultando rol (Supabase): {e}")
    return "usuario"

async def manejar_moderacion(bot: BaseBot, user: User, message: str):
    msg = message.lower().strip()
    if not msg.startswith("!"): return

    rol_ejecutor = await obtener_rol(user.id)

    # --- COMANDOS DE MODERACIÓN ---
    comandos_mod = ["!kick @", "!mute @", "!ban @", "!unmute @"]
    if any(msg.startswith(c) for c in comandos_mod):
        
        if rol_ejecutor not in ["admin", "fundador", "owner"]:
            await bot.highrise.send_whisper(user.id, "❌ No tienes el Tier suficiente.")
            return

        partes = msg.split()
        if len(partes) < 2: return
        target_username = partes[1].replace("@", "")
        
        room_users = await bot.highrise.get_room_users()
        target_user = next((u for u, p in room_users.content if u.username.lower() == target_username.lower()), None)

        if target_user:
            rol_objetivo = await obtener_rol(target_user.id)

            if rol_ejecutor == "admin" and rol_objetivo in ["fundador", "owner"]:
                await bot.highrise.send_whisper(user.id, "⚠️ No puedes moderar a un superior.")
                return

            if msg.startswith("!kick"):
                await ejecutar_accion(bot, user, target_user, "kick")
            elif msg.startswith("!mute"):
                segundos = int(partes[2]) if len(partes) > 2 else 600
                await ejecutar_accion(bot, user, target_user, "mute", segundos)
            elif msg.startswith("!ban"):
                await ejecutar_accion(bot, user, target_user, "ban", 86400)
            elif msg.startswith("!unmute"):
                await ejecutar_accion(bot, user, target_user, "mute", 1)
        else:
            await bot.highrise.send_whisper(user.id, f"❓ No encontré a @{target_username}")

    # --- COMANDOS DE PALABRAS ---
    if msg.startswith("!add_word ") and rol_ejecutor in ["fundador", "owner"]:
        nueva_palabra = msg.replace("!add_word ", "").strip().lower()
        try:
            supabase.table("palabras_prohibidas").insert({"palabra": nueva_palabra, "creado_por": user.username}).execute()
            await bot.highrise.send_whisper(user.id, f"✅ Palabra '{nueva_palabra}' añadida.")
        except:
            await bot.highrise.send_whisper(user.id, "❌ Esa palabra ya está en la lista.")

async def ejecutar_accion(bot, ejecutor, target_user, accion, tiempo=None):
    try:
        await bot.highrise.moderate_room(target_user.id, accion, tiempo)
        registrar_moderacion(ejecutor.username, target_user.username, accion)
        await bot.highrise.send_whisper(ejecutor.id, f"✅ {accion.upper()} exitoso contra @{target_user.username}")
    except Exception as e:
        await bot.highrise.send_whisper(ejecutor.id, f"❌ Error: {e}")