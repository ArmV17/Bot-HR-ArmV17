import asyncio
from highrise import BaseBot, User, Position
from funciones.db import supabase, obtener_rol

async def guardar_lugar(bot: BaseBot, user: User, message: str):
    parts = message.split()
    if len(parts) < 2: return

    rol = await obtener_rol(user.id)
    if rol not in ["fundador", "owner"]: return

    nombre_lugar = parts[1].lower()
    es_privado = True if len(parts) > 2 and parts[2].lower() == "privado" else False

    try:
        res = await bot.highrise.get_room_users()
        pos = next((p for u, p in res.content if u.id == user.id), None)
        if pos:
            data = {"nombre": nombre_lugar, "x": pos.x, "y": pos.y, "z": pos.z, "facing": pos.facing, "privado": es_privado}
            supabase.table("lugares").upsert(data, on_conflict="nombre").execute()
            await bot.highrise.chat(f"✅ Lugar '{nombre_lugar}' guardado.")
    except Exception as e: print(f"Error: {e}")

async def eliminar_lugar(bot: BaseBot, user: User, message: str):
    parts = message.split()
    if len(parts) < 2: return
    rol = await obtener_rol(user.id)
    if rol not in ["fundador", "owner"]: return

    nombre = parts[1].lower().strip()
    try:
        supabase.table("lugares").delete().eq("nombre", nombre).execute()
        await bot.highrise.chat(f"🗑️ Lugar '{nombre}' eliminado.")
    except: pass

async def viajar_a_nombre_directo(bot: BaseBot, user: User, message: str):
    nombre = message.lower().strip()
    try:
        res = supabase.table("lugares").select("*").eq("nombre", nombre).execute()
        if res.data:
            lugar = res.data[0]
            if lugar.get('privado'):
                rol = await obtener_rol(user.id)
                if rol not in ["fundador", "admin", "owner"]:
                    await bot.highrise.send_whisper(user.id, "🚫 Privado.")
                    return
            await bot.highrise.teleport(user.id, Position(lugar['x'], lugar['y'], lugar['z'], lugar.get('facing', 'FrontRight')))
            return True
    except: pass
    return False

# Lógica de Sensores
pasos_sensor = {}
async def marcar_proximidad(bot: BaseBot, user: User, message: str):
    parts = message.split()
    if len(parts) < 2: return
    nombre = parts[1].lower()
    res = await bot.highrise.get_room_users()
    pos = next((p for u, p in res.content if u.id == user.id), None)
    
    if not pos: return
    if user.id not in pasos_sensor:
        pasos_sensor[user.id] = {"sensor": pos}
        await bot.highrise.chat(f"📍 Sensor '{nombre}' marcado. Ve al DESTINO y repite el comando.")
    else:
        s = pasos_sensor[user.id]["sensor"]
        data = {"nombre": nombre, "sensor_x": s.x, "sensor_y": s.y, "sensor_z": s.z, "destino_x": pos.x, "destino_y": pos.y, "destino_z": pos.z}
        supabase.table("sensores_tp").upsert(data, on_conflict="nombre").execute()
        del pasos_sensor[user.id]
        await bot.highrise.chat(f"✅ Sensor '{nombre}' activado.")

async def crear_portal_externo(bot: BaseBot, user: User, message: str):
    parts = message.split()
    if len(parts) < 3: return
    nombre, sala = parts[1].lower(), parts[2]
    res = await bot.highrise.get_room_users()
    pos = next((p for u, p in res.content if u.id == user.id), None)
    if pos:
        data = {"nombre": nombre, "sensor_x": pos.x, "sensor_y": pos.y, "sensor_z": pos.z, "room_id": sala}
        supabase.table("sensores_tp").upsert(data, on_conflict="nombre").execute()
        await bot.highrise.chat(f"🌀 Portal a '{nombre}' creado.")