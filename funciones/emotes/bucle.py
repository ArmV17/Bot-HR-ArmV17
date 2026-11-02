import asyncio
import time
from highrise import BaseBot, User, Position
from funciones.db import supabase # Importación centralizada
from funciones.moderacion.comandos import obtener_rol

# Diccionario global para rastrear las tareas activas
tareas_emotes = {}

async def procesar_emote_directo(bot: BaseBot, user: User, message: str) -> bool:
    """Busca si el mensaje es un número o nombre de emote en la DB."""
    msg = message.lower().strip()

    # --- COMANDO DE PRUEBA (MUESTRA EL TIEMPO Y PRUEBA) ---
    if msg.startswith("!test "):
        rol = await obtener_rol(user.id)
        if rol not in ["admin", "fundador", "owner"]:
            return True

        parts = message.strip().split()
        if len(parts) >= 2:
            emote_id = parts[1].strip()
            
            # Consultamos la duración directamente en Supabase por su nombre_clave o número
            duracion_encontrada = 8.0 # Valor por defecto si no existe
            nombre_real = emote_id

            try:
                res_db = supabase.table("emotes").select("nombre_clave, duracion").or_(f"nombre_clave.eq.{emote_id},numero.eq.{emote_id}").execute()
                if res_db.data:
                    emote_info = res_db.data[0]
                    nombre_real = emote_info.get("nombre_clave", emote_id)
                    if emote_info.get("duracion"):
                        duracion_encontrada = float(emote_info["duracion"])
            except Exception as e:
                print(f"⚠️ Error consultando duración en DB: {e}")

            # Si además pasaron un segundo parámetro manual (ej: !test emote-id 8.24), usamos ese para sobreescribir la prueba
            if len(parts) >= 3:
                try:
                    duracion_encontrada = float(parts[2])
                except ValueError:
                    pass

            await probar_y_medir_emote(bot, user, nombre_real, duracion_encontrada)
        return True

    busqueda = msg
    
    try:
        # Consulta asíncrona a Supabase
        res = supabase.table("emotes").select("*").or_(f"numero.eq.{busqueda},nombre.eq.{busqueda}").execute()

        if res.data:
            emote_data = res.data[0]
            
            # Cancelar bucle anterior si el usuario ya estaba bailando
            if user.id in tareas_emotes:
                tareas_emotes[user.id].cancel()

            # Iniciar el nuevo bucle
            tareas_emotes[user.id] = asyncio.create_task(
                ejecutar_loop_infinito(bot, user.id, emote_data['nombre_clave'], emote_data['duracion'])
            )
            
            await bot.highrise.send_whisper(user.id, f"✨ Repitiendo: {emote_data['nombre']}. Di 'stop' para parar.")
            return True 
            
    except Exception as e:
        print(f"⚠️ Error buscando emote: {e}")
        
    return False

async def probar_y_medir_emote(bot: BaseBot, user: User, emote_id: str, duracion: float):
    """Ejecuta el emote y te informa en susurro el tiempo que se está usando."""
    try:
        await bot.highrise.send_whisper(
            user.id, 
            f"⏱️ Probando emote: `{emote_id}`\n⏳ Duración configurada: **{duracion}s**"
        )
        
        # Ejecutar el emote en el bot
        await bot.highrise.send_emote(emote_id, user.id)
        
        # Esperar el tiempo exacto
        await asyncio.sleep(duracion)
        
        await bot.highrise.send_whisper(
            user.id, 
            f"✅ Fin de prueba para `{emote_id}` ({duracion}s).\n💡 Si necesitas ajustarlo, escribe: `!test {emote_id} [nuevo_tiempo]`"
        )
    except Exception as e:
        print(f"⚠️ Error al probar emote: {e}")
        await bot.highrise.send_whisper(user.id, f"❌ Error al probar el emote. Revisa si el ID es correcto.")

async def ejecutar_loop_infinito(bot, user_id, emote_id, duracion):
    """Mantiene el emote activo hasta ser cancelado."""
    try:
        while True:
            await bot.highrise.send_emote(emote_id, user_id)
            await asyncio.sleep(duracion)
    except asyncio.CancelledError:
        pass

async def detener_bucle_por_movimiento(user_id):
    """Cancela el baile si el usuario camina."""
    if user_id in tareas_emotes:
        tareas_emotes[user_id].cancel()
        del tareas_emotes[user_id]

async def manejar_comando_stop(bot: BaseBot, user: User):
    """Detiene el bucle manualmente."""
    if user.id in tareas_emotes:
        await detener_bucle_por_movimiento(user.id)
        await bot.highrise.chat(f"✅ Bucle detenido para @{user.username}")
    else:
        await bot.highrise.send_whisper(user.id, "No tienes ningún bucle activo.")

async def hechizar_usuario(bot: BaseBot, user: User, message: str) -> None:
    """Comando simplificado: hechizar @usuario [número del emote]"""
    try:
        rol = await obtener_rol(user.id)
        
        if rol not in ["admin", "fundador", "owner"]:
            return 

        parts = message.lower().split()
        if len(parts) < 3: 
            await bot.highrise.send_whisper(user.id, "Uso correcto: `hechizar @usuario [número]`")
            return

        target_username = parts[1].replace("@", "").strip().lower()
        busqueda = parts[2].strip()

        # BUSCAR EL EMOTE EN SUPABASE (por número o nombre clave)
        res = supabase.table("emotes").select("*").or_(f"numero.eq.{busqueda},nombre_clave.eq.{busqueda}").execute()
        if not res.data: 
            await bot.highrise.send_whisper(user.id, f"❌ No encontré el emote con el identificador '{busqueda}' en la base de datos.")
            return
            
        emote_data = res.data[0]
        
        # BUSCAR AL OBJETIVO EN LA SALA
        res_users = await bot.highrise.get_room_users()
        target_user = None
        for u, p in res_users.content:
            if u.username.lower() == target_username:
                target_user = u
                break

        if target_user:
            if target_user.id in tareas_emotes:
                tareas_emotes[target_user.id].cancel()

            tareas_emotes[target_user.id] = asyncio.create_task(
                ejecutar_loop_infinito(bot, target_user.id, emote_data['nombre_clave'], emote_data['duracion'])
            )
            await bot.highrise.chat(f"🪄 ¡@{user.username} ha hechizado a @{target_user.username} con {emote_data['nombre']}!")
        else:
            await bot.highrise.send_whisper(user.id, f"❌ No encontré al usuario @{target_username} en la sala.")
            
    except Exception as e:
        print(f"⚠️ Error en hechizar: {e}")
        