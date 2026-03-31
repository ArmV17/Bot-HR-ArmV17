from highrise import BaseBot, User
from funciones.db import supabase, registrar_moderacion

async def obtener_rol(user_id: str):
    """Consulta el tier del usuario en la base de datos."""
    try:
        response = supabase.table("usuarios").select("rol").eq("id_jugador", user_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]['rol'].lower()
    except Exception as e:
        print(f"Error consultando rol: {e}")
    return "usuario"

async def manejar_moderacion(bot: BaseBot, user: User, message: str):
    msg = message.lower()
    if not msg.startswith("!"): return

    # Traemos el nivel del que escribe el comando
    rol_ejecutor = await obtener_rol(user.id)

    # --- COMANDOS DE MODERACIÓN (Admin y Fundador) ---
    if msg.startswith("!kick @") or msg.startswith("!mute @") or msg.startswith("!ban @") or msg.startswith("!unmute @"):
        
        # Validación de rango mínimo
        if rol_ejecutor not in ["admin", "fundador"]:
            await bot.highrise.send_whisper(user.id, "❌ No tienes el Tier suficiente (Admin/Fundador).")
            return

        # Lógica para extraer el nombre del objetivo
        partes = msg.split()
        target_username = partes[1].replace("@", "")
        
        # Buscamos al objetivo en la sala
        room_users = await bot.highrise.get_room_users()
        target_user = next((u[0] for u in room_users.content if u[0].username.lower() == target_username.lower()), None)

        if target_user:
            # SEGURIDAD EXTRA: Traemos el rol de la víctima
            rol_objetivo = await obtener_rol(target_user.id)

            # Un Admin NO puede tocar a un Fundador
            if rol_ejecutor == "admin" and rol_objetivo == "fundador":
                await bot.highrise.send_whisper(user.id, "⚠️ No puedes moderar al Fundador.")
                return

            # Ejecutar acciones
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

    if msg.startswith("!add_word ") and rol_ejecutor == "fundador":
        # Forzamos que la palabra se guarde en minúsculas (.lower())
        nueva_palabra = msg.replace("!add_word ", "").strip().lower()
        
        try:
            supabase.table("palabras_prohibidas").insert({
                "palabra": nueva_palabra, 
                "creado_por": user.username
            }).execute()
            
            await bot.highrise.send_whisper(user.id, f"✅ Palabra '{nueva_palabra}' añadida. El bot la detectará sin importar si la escriben en Mayúsculas o Minúsculas.")
        except:
            await bot.highrise.send_whisper(user.id, "❌ Error: Esa palabra ya está en la lista negra.")
    
    if msg == "!clear_logs" and rol_ejecutor == "fundador":
        from funciones.db import limpiar_tabla_chat
        exito = limpiar_tabla_chat()
        
        if exito:
            await bot.highrise.send_whisper(user.id, "♻️ La tabla de logs de chat ha sido vaciada correctamente.")
        else:
            await bot.highrise.send_whisper(user.id, "❌ Hubo un error al intentar limpiar la tabla.")

async def ejecutar_accion(bot, ejecutor, target_user, accion, tiempo=None):
    try:
        if accion == "kick":
            await bot.highrise.moderate_room(target_user.id, "kick")
        elif accion == "mute":
            await bot.highrise.moderate_room(target_user.id, "mute", tiempo)
        elif accion == "ban":
            await bot.highrise.moderate_room(target_user.id, "ban", tiempo)

        # Registro en DB con tu horario de México
        registrar_moderacion(ejecutor.username, target_user.username, accion)
        await bot.highrise.send_whisper(ejecutor.id, f"✅ {accion.upper()} exitoso contra @{target_user.username}")

    except Exception as e:
        await bot.highrise.send_whisper(ejecutor.id, f"❌ Error de Highrise: {e}")