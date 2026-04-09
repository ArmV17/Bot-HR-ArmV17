import asyncio
import os
from highrise import BaseBot, User, Position
from funciones.db import supabase

# Nota: No definimos ROOM_ID_ACTUAL de forma global para evitar errores 
# de sincronización con load_dotenv(). Lo leemos dentro de las funciones.

seguimiento_activo = {}

async def manejar_movimiento(bot, user, message):
    """Activa o desactiva el seguimiento del bot hacia un usuario."""
    msg = message.lower().strip()
    if msg == "sigueme":
        seguimiento_activo[user.id] = True
        await bot.highrise.chat(f"Entendido @{user.username}, ¡te sigo! 🏃‍♂️")
    elif msg == "detente":
        if user.id in seguimiento_activo:
            del seguimiento_activo[user.id]
            await bot.highrise.chat("Me detengo. ✅")

async def procesar_paso_seguimiento(bot, user, position):
    """Lógica para que el bot camine hacia la posición del usuario en tiempo real."""
    if user.id in seguimiento_activo:
        try:
            # Caminar a una distancia prudente para no encimarse
            await bot.highrise.walk_to(Position(position.x - 0.8, position.y, position.z, "FrontRight"))
        except: 
            pass

async def tp_entre_usuarios(bot: BaseBot, target_username: str, destination_username: str):
    """Teletransporta a un usuario hacia la posición de otro en la misma sala."""
    res = await bot.highrise.get_room_users()
    u1_id = next((u.id for u, p in res.content if u.username.lower() == target_username.lower()), None)
    pos2 = next((p for u, p in res.content if u.username.lower() == destination_username.lower()), None)

    if u1_id and pos2:
        await bot.highrise.teleport(u1_id, pos2)

async def tp_a_coordenadas_directo(bot: BaseBot, target_username: str, x: float, y: float, z: float):
    """Teletransporta a un usuario a coordenadas exactas."""
    res = await bot.highrise.get_room_users()
    target_u = next((u for u, p in res.content if u.username.lower() == target_username.lower()), None)
    if target_u:
        await bot.highrise.teleport(target_u.id, Position(x, y, z))

async def obtener_room_id(destino: str):
    """
    Busca el ID de la sala destino en la base de datos.
    Filtra estrictamente por la sala de origen actual para evitar colisiones.
    """
    room_id_actual = os.getenv("ROOM_ID")
    try:
        # Solo recupera el ID si el portal fue creado en esta instancia (origin_room_id)
        res = supabase.table("sensores_tp")\
            .select("room_id")\
            .eq("nombre", destino.lower())\
            .eq("origin_room_id", room_id_actual)\
            .execute()
        
        if res.data and res.data[0]['room_id']:
            return res.data[0]['room_id']
    except Exception as e:
        print(f"Error en obtener_room_id: {e}")
    
    # Si no es un portal registrado, asume que el destino es un ID de sala directo
    return destino

async def trasladar_toda_la_sala(bot, user, message):
    """Mueve a todos los usuarios de la sala actual hacia otra sala."""
    parts = message.split()
    if len(parts) < 2: return
    
    room_dest = await obtener_room_id(parts[1])
    res = await bot.highrise.get_room_users()
    contador = 0
    
    # Obtenemos el nombre del bot para no auto-trasladarse y perder conexión
    my_id = bot.user.id if hasattr(bot, 'user') else None

    for u, p in res.content:
        if u.id != my_id:
            try:
                await bot.highrise.move_user_to_room(u.id, room_dest)
                contador += 1
                # Pausa de 0.4s para evitar el baneo por Rate Limit (Aseguramiento de Calidad)
                await asyncio.sleep(0.4) 
            except:
                continue
                
    await bot.highrise.chat(f"🏢 Traslado a '{parts[1]}' iniciado ({contador} usuarios).")

async def mover_lista_seleccionada(bot, user, message):
    """Mueve solo a los usuarios mencionados en el comando (!enviar @user1 @user2 sala)."""
    parts = message.split()
    if len(parts) < 3: return
    
    room_dest = await obtener_room_id(parts[-1])
    targets = [p.replace("@", "").lower() for p in parts[1:-1]]
    res = await bot.highrise.get_room_users()
    
    for u, p in res.content:
        if u.username.lower() in targets:
            try:
                await bot.highrise.move_user_to_room(u.id, room_dest)
                await asyncio.sleep(0.4)
            except:
                continue