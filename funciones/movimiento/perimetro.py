import os
import math
from supabase import create_client, Client
from highrise import BaseBot, User, Position
from dotenv import load_dotenv

load_dotenv()
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

async def verificar_proximidad_tp(bot: BaseBot, user: User, position: Position):
    try:
        res = supabase.table("sensores_tp").select("*").execute()
        
        for punto in res.data:
            distancia = math.sqrt((position.x - punto['sensor_x'])**2 + (position.z - punto['sensor_z'])**2)

            # Si el usuario pisa el sensor
            if distancia < 0.8 and abs(position.y - punto['sensor_y']) < 0.5:
                
                # CASO A: PORTAL A OTRA SALA
                if punto['room_id']:
                    print(f"🌀 Enviando a {user.username} a la sala externa: {punto['room_id']}")
                    await bot.highrise.move_user_to_room(user.id, punto['room_id'])
                    return True
                
                # CASO B: ELEVADOR EN LA MISMA SALA
                else:
                    print(f"✨ Elevador '{punto['nombre']}' activado por {user.username}")
                    await bot.highrise.teleport(
                        user.id, 
                        Position(punto['destino_x'], punto['destino_y'], punto['destino_z'], "FrontRight")
                    )
                    return True
    except Exception as e:
        print(f"❌ Error en sensor/portal: {e}")
    return False