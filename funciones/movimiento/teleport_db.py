import os
import asyncio
from supabase import create_client, Client
from highrise import BaseBot, User, Position
from dotenv import load_dotenv

load_dotenv()
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Importamos obtener_rol para la seguridad
from funciones.moderacion.comandos import obtener_rol

async def guardar_lugar(bot: BaseBot, user: User, message: str):
    """Uso: !guardar [nombre] [publico/privado]"""
    parts = message.split()
    if len(parts) < 2:
        await bot.highrise.send_whisper(user.id, "❌ Uso: !guardar [nombre] [privado/publico]")
        return

    rol = await obtener_rol(user.id)
    if rol != "fundador":
        await bot.highrise.send_whisper(user.id, "Solo el fundador puede guardar lugares.")
        return

    nombre_lugar = parts[1].lower()
    # Si escribes 'privado' al final, será privado. Si no, será público.
    es_privado = True if len(parts) > 2 and parts[2].lower() == "privado" else False

    try:
        response = await bot.highrise.get_room_users()
        mi_pos = next((pos for u, pos in response.content if u.id == user.id), None)
        
        if not mi_pos or not isinstance(mi_pos, Position): return

        data = {
            "nombre": nombre_lugar,
            "x": mi_pos.x, "y": mi_pos.y, "z": mi_pos.z, "facing": mi_pos.facing,
            "privado": es_privado
        }

        supabase.table("lugares").upsert(data, on_conflict="nombre").execute()
        tipo = "🔒 PRIVADO" if es_privado else "🌐 PÚBLICO"
        await bot.highrise.chat(f"✅ Lugar '{nombre_lugar}' guardado como {tipo}.")

    except Exception as e:
        print(f"Error al guardar: {e}")

async def eliminar_lugar(bot: BaseBot, user: User, message: str):
    """Elimina un lugar de la base de datos. Uso: !eliminar [nombre]"""
    parts = message.split()
    if len(parts) < 2:
        await bot.highrise.send_whisper(user.id, "❌ Uso: !eliminar [nombre_lugar]")
        return

    # Seguridad: Solo el Fundador puede borrar lugares oficiales
    from funciones.moderacion.comandos import obtener_rol
    rol = await obtener_rol(user.id)
    if rol != "fundador":
        await bot.highrise.send_whisper(user.id, "Solo el fundador puede eliminar lugares.")
        return

    nombre_lugar = parts[1].lower().strip()

    try:
        # Intentamos eliminar de la tabla
        result = supabase.table("lugares").delete().eq("nombre", nombre_lugar).execute()
        
        # Verificamos si realmente se eliminó algo (si la lista de data no está vacía)
        if result.data:
            await bot.highrise.chat(f"🗑️ El lugar '{nombre_lugar}' ha sido eliminado.")
        else:
            await bot.highrise.send_whisper(user.id, f"❓ No encontré ningún lugar llamado '{nombre_lugar}'.")

    except Exception as e:
        print(f"⚠️ Error al eliminar lugar: {e}")
        await bot.highrise.send_whisper(user.id, "Hubo un error al intentar borrar el lugar.")

async def viajar_a_nombre_directo(bot: BaseBot, user: User, message: str):
    """Busca el lugar y verifica permisos antes de teletransportar"""
    nombre_lugar = message.lower().strip()

    try:
        query = supabase.table("lugares").select("*").eq("nombre", nombre_lugar).execute()
        
        if query.data:
            lugar = query.data[0]
            es_privado = lugar.get('privado', False)

            # --- VERIFICACIÓN DE SEGURIDAD ---
            if es_privado:
                rol = await obtener_rol(user.id)
                if rol not in ["fundador", "admin"]:
                    await bot.highrise.send_whisper(user.id, "🚫 Este lugar es privado (Solo Admins).")
                    return

            # Si es público o el usuario tiene permiso, teletransportar
            await bot.highrise.teleport(user.id, Position(
                float(lugar['x']), float(lugar['y']), float(lugar['z']), 
                lugar.get('facing', 'FrontRight')
            ))
            await bot.highrise.send_whisper(user.id, f"🚀 Viajando a: {nombre_lugar.capitalize()}")

    except Exception as e:
        print(f"Error en viaje: {e}")

pasos_sensor = {}

async def marcar_proximidad(bot: BaseBot, user: User, message: str):
    """Uso: !sensor [nombre]"""
    parts = message.split()
    if len(parts) < 2:
        await bot.highrise.send_whisper(user.id, "❌ Uso: !sensor [nombre]")
        return

    nombre = parts[1].lower()
    res = await bot.highrise.get_room_users()
    pos = next((p for u, p in res.content if u.id == user.id), None)
    
    if not pos: return

    if user.id not in pasos_sensor:
        # PASO 1: Guardar ubicación del sensor
        pasos_sensor[user.id] = {"sensor": pos}
        await bot.highrise.chat(f"📍 Sensor de '{nombre}' marcado. Ahora ve al DESTINO y repite !sensor {nombre}")
    else:
        # PASO 2: Guardar destino y subir a DB
        s = pasos_sensor[user.id]["sensor"]
        data = {
            "nombre": nombre,
            "sensor_x": s.x, "sensor_y": s.y, "sensor_z": s.z,
            "destino_x": pos.x, "destino_y": pos.y, "destino_z": pos.z
        }
        
        from funciones.movimiento.perimetro import supabase
        supabase.table("sensores_tp").upsert(data, on_conflict="nombre").execute()
        del pasos_sensor[user.id]
        await bot.highrise.chat(f"✅ ¡Sensor '{nombre}' activado! Al pararte ahí, viajarás automáticamente.")

async def crear_portal_externo(bot: BaseBot, user: User, message: str):
    """Uso: !portal [nombre] [room_id]"""
    parts = message.split()
    if len(parts) < 3:
        await bot.highrise.send_whisper(user.id, "❌ Uso: !portal [nombre] [room_id]")
        return

    nombre = parts[1].lower()
    sala_destino = parts[2] # El ID de la sala externa

    res = await bot.highrise.get_room_users()
    pos = next((p for u, p in res.content if u.id == user.id), None)
    if not pos: return

    data = {
        "nombre": nombre,
        "sensor_x": pos.x, "sensor_y": pos.y, "sensor_z": pos.z,
        "room_id": sala_destino # Guardamos el ID de la sala
    }
    
    from funciones.movimiento.perimetro import supabase
    supabase.table("sensores_tp").upsert(data, on_conflict="nombre").execute()
    await bot.highrise.chat(f"🌀 ¡Portal a otra sala creado! Nombre: {nombre}. ¡Pisa aquí para viajar!")