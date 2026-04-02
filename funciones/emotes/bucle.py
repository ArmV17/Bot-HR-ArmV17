import asyncio
from highrise import BaseBot, User, Position
from funciones.movimiento.perimetro import supabase

# Diccionario global para rastrear las tareas activas
tareas_emotes = {}

async def procesar_emote_directo(bot: BaseBot, user: User, message: str) -> bool:
    """
    Busca si el mensaje es un número o nombre de emote.
    Devuelve True si encontró y activó uno, False si no.
    """
    busqueda = message.lower().strip()
    
    try:
        # Buscamos en Supabase si el mensaje coincide con 'numero' o 'nombre'
        res = supabase.table("emotes").select("*").or_(f"numero.eq.{busqueda},nombre.eq.{busqueda}").execute()

        if res.data:
            emote_data = res.data[0]
            
            # Cancelar bucle anterior si existe
            if user.id in tareas_emotes:
                tareas_emotes[user.id].cancel()

            # Iniciar el nuevo bucle
            tareas_emotes[user.id] = asyncio.create_task(
                ejecutar_loop_infinito(bot, user.id, emote_data['nombre_clave'], emote_data['duracion'])
            )
            
            # Susurro para no saturar el chat público con confirmaciones
            await bot.highrise.send_whisper(user.id, f"✨ Repitiendo: {emote_data['nombre']}. Camina o di 'stop' para parar.")
            return True # Indica que sí era un comando de emote
            
    except Exception as e:
        print(f"Error buscando emote: {e}")
        
    return False # No era un emote, sigue con el flujo normal

async def ejecutar_loop_infinito(bot, user_id, emote_id, duracion):
    """Mantiene el emote activo hasta ser cancelado"""
    try:
        while True:
            await bot.highrise.send_emote(emote_id, user_id)
            await asyncio.sleep(duracion)
    except asyncio.CancelledError:
        pass

async def detener_bucle_por_movimiento(user_id):
    """Cancela la tarea si existe"""
    if user_id in tareas_emotes:
        tareas_emotes[user_id].cancel()
        del tareas_emotes[user_id]

async def manejar_comando_stop(bot: BaseBot, user: User):
    """Detecta: 'stop'"""
    if user.id in tareas_emotes:
        await detener_bucle_por_movimiento(user.id)
        await bot.highrise.chat(f"✅ Bucle detenido para @{user.username}")
    else:
        await bot.highrise.send_whisper(user.id, "No tienes ningún bucle activo.")

async def hechizar_usuario(bot: BaseBot, user: User, message: str) -> None:
    """
    Comando: hechizar @usuario [numero/nombre]
    """
    try:
        from funciones.moderacion.comandos import obtener_rol
        rol = await obtener_rol(user.id)
        
        if rol not in ["admin", "fundador", "owner"]:
            return 

        parts = message.lower().split()
        # Estructura: hechizar (0) @usuario (1) emote (2)
        if len(parts) < 3: return

        target_username = parts[1].replace("@", "")
        busqueda = parts[2].strip()

        # BUSCAR EL EMOTE
        res = supabase.table("emotes").select("*").or_(f"numero.eq.{busqueda},nombre.eq.{busqueda}").execute()
        if not res.data: return

        emote_data = res.data[0]
        
        # BUSCAR AL OBJETIVO
        room_users = (await bot.highrise.get_room_users()).content
        target_user = next((u for u, p in room_users if u.username.lower() == target_username), None)

        if target_user:
            if target_user.id in tareas_emotes:
                tareas_emotes[target_user.id].cancel()

            tareas_emotes[target_user.id] = asyncio.create_task(
                ejecutar_loop_infinito(bot, target_user.id, emote_data['nombre_clave'], emote_data['duracion'])
            )
            # Mensaje mágico en el chat
            await bot.highrise.chat(f"🪄 ¡@{user.username} ha hechizado a @{target_user.username} para bailar {emote_data['nombre']}!")
            
    except Exception as e:
        print(f"Error en hechizar: {e}")