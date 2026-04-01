import asyncio
from highrise import BaseBot, User, Position
from funciones.moderacion.comandos import obtener_rol

# Control de seguimiento
seguimiento_activo = {} 

async def manejar_movimiento(bot: BaseBot, user: User, message: str):
    msg = message.lower().strip()
    
    # Seguridad: Solo Fundador o Admin
    rol = await obtener_rol(user.id)
    if rol not in ["fundador", "admin"]:
        return

    if msg == "sigueme":
        if user.id in seguimiento_activo:
            return
            
        seguimiento_activo[user.id] = True
        await bot.highrise.chat(f"Entendido, Te sigo @{user.username}")
        asyncio.create_task(seguir_usuario(bot, user))

    elif msg == "detente":
        if user.id in seguimiento_activo:
            del seguimiento_activo[user.id]
            await bot.highrise.chat("Me detengo aquí. 🛑")

async def seguir_usuario(bot: BaseBot, user: User):
    while user.id in seguimiento_activo:
        try:
            # 1. Obtener la lista de usuarios en tiempo real
            room_users = await bot.highrise.get_room_users()
            
            # 2. Buscar tu posición actual
            target_pos = None
            for u, pos in room_users.content:
                if u.id == user.id:
                    target_pos = pos
                    break
            
            # 3. Si te encontramos, calculamos la posición "AL LADO"
            if target_pos and isinstance(target_pos, Position):
                # AJUSTE DE COORDENADA:
                # Sumamos 0.6 a la X para que camine a tu derecha.
                # Si quieres que sea a la izquierda, usa -0.6
                posicion_al_lado = Position(
                    x = target_pos.x - 1, 
                    y = target_pos.y, 
                    z = target_pos.z, 
                    facing = target_pos.facing
                )
                
                # Ordenar al bot que camine a esa coordenada específica
                await bot.highrise.walk_to(posicion_al_lado)
            
            # 4. Esperar 1.2 segundos (Evita que el bot se trabe o te desconecten)
            await asyncio.sleep(1.2)
            
        except Exception as e:
            print(f"Error en movimiento: {e}")
            break