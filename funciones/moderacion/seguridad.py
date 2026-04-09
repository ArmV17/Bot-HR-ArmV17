from highrise import BaseBot, User
import pytz
from datetime import datetime
from funciones.db import supabase, registrar_moderacion, guardar_usuario_db

async def registrar_entrada(bot: BaseBot, user: User):
    try:
        guardar_usuario_db(user.id, user.username)
        print(f"🛡️ Seguridad: Registrado {user.username}")
    except: pass

async def verificar_automod(bot, user, message, rol_ejecutor):
    if rol_ejecutor in ["admin", "fundador", "owner"]: return False

    msg_limpio = message.lower()
    
    try:
        # Obtenemos palabras prohibidas (puedes cachear esto luego para más velocidad)
        res_palabras = supabase.table("palabras_prohibidas").select("palabra").execute()
        palabras = [p['palabra'].lower() for p in res_palabras.data]

        palabra_detectada = next((p for p in palabras if p in msg_limpio), None)

        if palabra_detectada:
            res_adv = supabase.table("advertencias_automod").select("contador").eq("id_jugador", user.id).execute()
            faltas = res_adv.data[0]['contador'] if res_adv.data else 0
            nuevas_faltas = faltas + 1

            zona_mx = pytz.timezone('America/Mexico_City')
            fecha_mx = datetime.now(zona_mx).strftime("%d/%m/%Y %I:%M %p")

            if nuevas_faltas < 3:
                await bot.highrise.send_whisper(user.id, f"⚠️ ¡ADVERTENCIA {nuevas_faltas}/3!")
                supabase.table("advertencias_automod").upsert({
                    "id_jugador": user.id,
                    "username": user.username,
                    "contador": nuevas_faltas,
                    "ultima_falta": palabra_detectada,
                    "actualizado_el": fecha_mx
                }).execute()
                return False
            else:
                await bot.highrise.moderate_room(user.id, "ban", 52560000)
                registrar_moderacion("SISTEMA AUTO-MOD", user.username, "BAN PERMANENTE")
                supabase.table("advertencias_automod").delete().eq("id_jugador", user.id).execute()
                await bot.highrise.chat(f"🚫 @{user.username} baneado por Auto-Mod (3/3).")
                return True
    except Exception as e:
        print(f"⚠️ Error en AutoMod: {e}")
    return False