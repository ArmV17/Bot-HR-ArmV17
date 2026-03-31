from highrise import BaseBot, User
import pytz
from datetime import datetime
from funciones.db import guardar_usuario_db # Importamos la DB
from funciones.db import supabase, registrar_moderacion

lista_negra_palabras = []

async def registrar_entrada(bot: BaseBot, user: User):
    # Guardamos en la nube (Supabase)
    guardar_usuario_db(user.id, user.username)
    
    # Mensaje de log
    print(f"Seguridad: Registrado {user.username} con ID {user.id}")

async def cargar_palabras():
    global lista_negra_palabras
    response = supabase.table("palabras_prohibidas").select("palabra").execute()
    lista_negra_palabras = [item['palabra'].lower() for item in response.data]

async def verificar_automod(bot, user, message, rol_ejecutor):
    # Inmunidad para rangos altos
    if rol_ejecutor in ["admin", "fundador"]:
        return False

    # 1. Normalización total para detección (ignora Mayúsculas/Minúsculas)
    msg_limpio = message.lower()
    
    # Traemos palabras prohibidas
    response = supabase.table("palabras_prohibidas").select("palabra").execute()
    palabras = [p['palabra'].lower() for p in response.data]

    palabra_detectada = None
    for p in palabras:
        if p in msg_limpio:
            palabra_detectada = p
            break

    if palabra_detectada:
        # Consultar historial de este usuario específico
        res = supabase.table("advertencias_automod").select("contador").eq("id_jugador", user.id).execute()
        
        faltas_actuales = res.data[0]['contador'] if res.data else 0
        nuevas_faltas = faltas_actuales + 1

        # Horario de México (Saltillo)
        zona_mx = pytz.timezone('America/Mexico_City')
        fecha_mx = datetime.now(zona_mx).strftime("%d/%m/%Y %I:%M %p")

        if nuevas_faltas < 3:
            # --- ADVERTENCIA PRIVADA (SUSURRO) ---
            await bot.highrise.send_whisper(user.id, f"⚠️ ¡ADVERTENCIA {nuevas_faltas}/3!")
            await bot.highrise.send_whisper(user.id, f"Detectado uso de palabra prohibida.")
            await bot.highrise.send_whisper(user.id, "Si llegas a 3 faltas serás BANEADO PERMANENTEMENTE.")
            
            # Guardar con USERNAME incluido
            supabase.table("advertencias_automod").upsert({
                "id_jugador": user.id,
                "username": user.username, # Guardamos el nombre para tu control
                "contador": nuevas_faltas,
                "ultima_falta": palabra_detectada,
                "actualizado_el": fecha_mx
            }).execute()
            
            print(f"⚠️ Falta {nuevas_faltas} para {user.username} (ID: {user.id})")
            return False

        else:
            # --- BANEO PERMANENTE AL LLEGAR A LA 3ra FALTA ---
            try:
                await bot.highrise.moderate_room(user.id, "ban", 52560000)
                
                registrar_moderacion(
                    ejecutor="SISTEMA AUTO-MOD",
                    objetivo=user.username,
                    accion="BAN PERMANENTE",
                    razon=f"Acumulación de 3 advertencias. Última palabra: '{palabra_detectada}'"
                )
                
                # Borramos las advertencias porque el baneo ya es definitivo
                supabase.table("advertencias_automod").delete().eq("id_jugador", user.id).execute()
                
                await bot.highrise.chat(f"🚫 @{user.username} ha sido baneado permanentemente tras ignorar 3 advertencias de Auto-Mod.")
                return True
            except Exception as e:
                print(f"Error al ejecutar ban: {e}")
                
    return False