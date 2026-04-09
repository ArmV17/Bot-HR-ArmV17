from highrise import BaseBot, User
from funciones.db import supabase # Importación centralizada
import asyncio

async def emote_todos(self: BaseBot, user: User, message: str) -> None:
    """Comando: todos [numero o nombre]"""
    try:
        parts = message.lower().split()
        if len(parts) < 2:
            await self.highrise.send_whisper(user.id, "Usa: todos [1-92] o [nombre]")
            return
            
        busqueda = parts[1]

        # 1. Buscar el emote en Supabase
        res = supabase.table("emotes").select("*").or_(f"numero.eq.{busqueda},nombre.eq.{busqueda}").execute()

        if not res.data:
            await self.highrise.send_whisper(user.id, f"❌ El emote '{busqueda}' no existe.")
            return

        emote_data = res.data[0]
        emote_id = emote_data['nombre_clave']
        nombre_display = emote_data['nombre']

        await self.highrise.chat(f"📣 ¡Todos a bailar {nombre_display}! 💃🕺")

        # 2. Obtener usuarios y enviar emote con pausa de seguridad
        res_users = await self.highrise.get_room_users()
        for room_user, position in res_users.content:
            try:
                await self.highrise.send_emote(emote_id, room_user.id)
                await asyncio.sleep(0.2) # Evita que Highrise banee al bot por spam
            except:
                continue

    except Exception as e:
        print(f"⚠️ Error en comando todos: {e}")