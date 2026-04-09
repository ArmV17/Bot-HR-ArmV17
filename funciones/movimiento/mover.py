import asyncio
from highrise import BaseBot, User, Position
from funciones.db import supabase # Conexión centralizada

seguimiento_activo = {}

async def manejar_movimiento(bot, user, message):
    msg = message.lower().strip()
    if msg == "sigueme":
        seguimiento_activo[user.id] = True
        await bot.highrise.chat(f"Entendido @{user.username}, ¡te sigo! 🏃‍♂️")
    elif msg == "detente":
        if user.id in seguimiento_activo:
            del seguimiento_activo[user.id]
            await bot.highrise.chat("Me detengo. ✅")

async def procesar_paso_seguimiento(bot, user, position):
    if user.id in seguimiento_activo:
        try:
            # El bot camina a tu posición con un pequeño margen
            await bot.highrise.walk_to(Position(position.x - 0.8, position.y, position.z, "FrontRight"))
        except: pass

async def tp_entre_usuarios(bot: BaseBot, target_username: str, destination_username: str):
    res = await bot.highrise.get_room_users()
    u1_id = next((u.id for u, p in res.content if u.username.lower() == target_username.lower()), None)
    pos2 = next((p for u, p in res.content if u.username.lower() == destination_username.lower()), None)

    if u1_id and pos2:
        await bot.highrise.teleport(u1_id, pos2)

async def tp_a_coordenadas_directo(bot: BaseBot, target_username: str, x: float, y: float, z: float):
    res = await bot.highrise.get_room_users()
    target_u = next((u for u, p in res.content if u.username.lower() == target_username.lower()), None)
    if target_u:
        await bot.highrise.teleport(target_u.id, Position(x, y, z))

async def obtener_room_id(destino: str):
    try:
        res = supabase.table("sensores_tp").select("room_id").eq("nombre", destino.lower()).execute()
        if res.data and res.data[0]['room_id']:
            return res.data[0]['room_id']
    except: pass
    return destino

async def trasladar_toda_la_sala(bot, user, message):
    parts = message.split()
    if len(parts) < 2: return
    room_dest = await obtener_room_id(parts[1])
    res = await bot.highrise.get_room_users()
    contador = 0
    for u, p in res.content:
        if u.username.lower() != "steffi": # Evitar que el bot se auto-traslade
            await bot.highrise.move_user_to_room(u.id, room_dest)
            contador += 1
            await asyncio.sleep(0.2) # Pausa de seguridad
    await bot.highrise.chat(f"🏢 Traslado a '{parts[1]}' iniciado ({contador} usuarios).")

async def mover_lista_seleccionada(bot, user, message):
    parts = message.split()
    if len(parts) < 3: return
    room_dest = await obtener_room_id(parts[-1])
    targets = [p.replace("@", "").lower() for p in parts[1:-1]]
    res = await bot.highrise.get_room_users()
    for u, p in res.content:
        if u.username.lower() in targets:
            await bot.highrise.move_user_to_room(u.id, room_dest)
            await asyncio.sleep(0.2)