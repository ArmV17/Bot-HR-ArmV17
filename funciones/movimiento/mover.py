import asyncio
from highrise import BaseBot, User, Position
from funciones.moderacion.comandos import obtener_rol
from funciones.movimiento.perimetro import supabase
from highrise import BaseBot, User, Position

# En mover.py
seguimiento_activo = {}

async def manejar_movimiento(bot, user, message):
    msg = message.lower().strip()
    if msg == "sigueme":
        seguimiento_activo[user.id] = True
        await bot.highrise.chat(f"Entendido @{user.username}, ¡te sigo!")
    elif msg == "detente":
        if user.id in seguimiento_activo:
            del seguimiento_activo[user.id]
            await bot.highrise.chat("Me detengo.")

async def procesar_paso_seguimiento(bot, user, position):
    if user.id in seguimiento_activo:
        # El bot camina a tu posición
        await bot.highrise.walk_to(Position(position.x - 0.8, position.y, position.z, "FrontRight"))
async def tp_entre_usuarios(bot: BaseBot, target_username: str, destination_username: str):
    """Lógica para @Usuario1 @Usuario2"""
    room_users = await bot.highrise.get_room_users()
    
    u1_id = next((u.id for u, p in room_users.content if u.username.lower() == target_username.lower()), None)
    pos2 = next((p for u, p in room_users.content if u.username.lower() == destination_username.lower()), None)

    if u1_id and pos2:
        await bot.highrise.teleport(u1_id, pos2)
        print(f"✅ Movido {target_username} hacia {destination_username}")

async def tp_a_coordenadas_directo(bot: BaseBot, target_username: str, x: float, y: float, z: float):
    """Lógica para @Usuario X Y Z"""
    room_users = await bot.highrise.get_room_users()
    target_u = next((u for u, p in room_users.content if u.username.lower() == target_username.lower()), None)

    if target_u:
        await bot.highrise.teleport(target_u.id, Position(x, y, z))
        print(f"✅ Movido {target_username} a coordenadas {x}, {y}, {z}")

async def obtener_room_id(destino: str):
    """Busca si el destino es un nombre de portal en la DB, si no, devuelve el texto original"""
    try:
        # Buscamos en la tabla sensores_tp si existe un nombre que coincida
        res = supabase.table("sensores_tp").select("room_id").eq("nombre", destino.lower()).execute()
        if res.data and res.data[0]['room_id']:
            return res.data[0]['room_id']
    except:
        pass
    return destino # Si no está en la DB, asumimos que ya es un Room ID

async def trasladar_toda_la_sala(bot, user, message):
    """Uso: !traslado [nombre_portal o room_id]"""
    parts = message.split()
    if len(parts) < 2: return

    # Buscamos el ID (en DB o directo)
    room_dest = await obtener_room_id(parts[1])
    
    room_users = await bot.highrise.get_room_users()
    contador = 0
    for u, p in room_users.content:
        if u.id != bot.id:
            await bot.highrise.move_user_to_room(u.id, room_dest)
            contador += 1
    await bot.highrise.chat(f"🏢 Traslado a '{parts[1]}' iniciado para {contador} usuarios.")

async def mover_lista_seleccionada(bot, user, message):
    """Uso: !enviar @user1 @user2 [nombre_portal o room_id]"""
    parts = message.split()
    if len(parts) < 3: return

    # El último es el destino
    destino_raw = parts[-1]
    room_dest = await obtener_room_id(destino_raw)
    
    targets = [p.replace("@", "").lower() for p in parts[1:-1]]
    room_users = await bot.highrise.get_room_users()
    
    for u, p in room_users.content:
        if u.username.lower() in targets:
            await bot.highrise.move_user_to_room(u.id, room_dest)