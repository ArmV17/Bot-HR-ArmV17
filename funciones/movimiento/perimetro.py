import math
from highrise import BaseBot, User, Position
from funciones.db import supabase # Conexión centralizada

async def verificar_proximidad_tp(bot: BaseBot, user: User, position: Position):
    try:
        # Nota: En producción sería mejor cachear esto, pero aquí lo mantenemos simple
        res = supabase.table("sensores_tp").select("*").execute()
        
        for punto in res.data:
            distancia = math.sqrt((position.x - punto['sensor_x'])**2 + (position.z - punto['sensor_z'])**2)

            if distancia < 0.8 and abs(position.y - punto['sensor_y']) < 0.5:
                if punto.get('room_id'):
                    await bot.highrise.move_user_to_room(user.id, punto['room_id'])
                    return True
                else:
                    await bot.highrise.teleport(user.id, Position(punto['destino_x'], punto['destino_y'], punto['destino_z'], "FrontRight"))
                    return True
    except Exception as e:
        print(f"⚠️ Error en sensores: {e}")
    return False