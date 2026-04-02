from highrise import BaseBot, User
from funciones.movimiento.perimetro import supabase

async def emote_todos(self: BaseBot, user: User, message: str) -> None:
    """Comando: todos [numero o nombre]"""
    try:
        # Extraemos lo que escribió después de la palabra 'todos'
        parts = message.lower().split()
        if len(parts) < 2:
            await self.highrise.send_whisper(user.id, "Usa: todos [1-92] o [nombre]")
            return
            
        busqueda = parts[1]

        # 1. Buscar el emote en Supabase
        res = supabase.table("emotes").select("*").or_(f"numero.eq.{busqueda},nombre.eq.{busqueda}").execute()

        if not res.data:
            await self.highrise.send_whisper(user.id, f"❌ El emote '{busqueda}' no existe en la DB.")
            return

        emote_data = res.data[0]
        emote_id = emote_data['nombre_clave']
        nombre_display = emote_data['nombre']

        # 2. Anunciar la acción
        await self.highrise.chat(f"📣 ¡Todos a bailar {nombre_display}! 💃🕺")

        # 3. Obtener usuarios y enviar emote a cada uno
        room_users = (await self.highrise.get_room_users()).content
        for room_user, position in room_users:
            try:
                await self.highrise.send_emote(emote_id, room_user.id)
            except:
                # Si falla con alguien (ej: no tiene el emote si es VIP), pasamos al siguiente
                continue

    except Exception as e:
        print(f"Error en comando todos: {e}")