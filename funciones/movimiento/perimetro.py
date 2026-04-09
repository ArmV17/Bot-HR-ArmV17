import os
import asyncio
from highrise import BaseBot, User, Position
from funciones.db import supabase

async def verificar_proximidad_tp(bot: BaseBot, user: User, destination: Position):
    """
    Se ejecuta cada vez que un usuario da un paso.
    Filtra los sensores para que solo se activen los de la sala actual.
    """
    # 1. Obtenemos en qué sala está parado ESTE bot
    sala_actual = os.getenv("ROOM_ID")

    try:
        # 2. FILTRO CRÍTICO: Buscar sensores cuyo ORIGEN sea esta sala
        res = supabase.table("sensores_tp").select("*").eq("origin_room_id", sala_actual).execute()
        
        # Si no hay sensores en esta sala, no hacemos nada
        if not res.data: 
            return

        # 3. Revisamos si las coordenadas del paso coinciden con algún sensor
        for sensor in res.data:
            # Margen de error al pisar (para no tener que pisar el píxel exacto)
            margen_x = 1.0
            margen_y = 1.5
            margen_z = 1.0
            
            if (abs(destination.x - sensor['sensor_x']) <= margen_x and
                abs(destination.y - sensor['sensor_y']) <= margen_y and
                abs(destination.z - sensor['sensor_z']) <= margen_z):
                
                # CASO A: Es un portal (Tiene un room_id de destino)
                if sensor.get('room_id') and sensor['room_id'].strip() != "":
                    await bot.highrise.move_user_to_room(user.id, sensor['room_id'])
                    
                # CASO B: Es un sensor local (Tiene destino X, Y, Z en esta misma sala)
                elif sensor.get('destino_x') is not None:
                    await bot.highrise.teleport(user.id, Position(sensor['destino_x'], sensor['destino_y'], sensor['destino_z']))
                
                break # Rompemos el ciclo para no activar múltiples sensores a la vez
                
    except Exception as e:
        # Silenciamos el error con pass o lo imprimimos para depurar
        # print(f"Error en perimetro: {e}")
        pass