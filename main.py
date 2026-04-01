import os
import asyncio
from dotenv import load_dotenv
from highrise import BaseBot, User, Position
from highrise.__main__ import BotDefinition, main

# --- IMPORTACIONES DE MODERACIÓN Y BASE ---
from funciones.moderacion.seguridad import registrar_entrada, verificar_automod
from funciones.moderacion.comandos import manejar_moderacion, obtener_rol
from funciones.db import guardar_log_chat
from funciones.ropa.ropa import manejar_ropa
from funciones.movimiento.mover import manejar_movimiento

# --- IMPORTACIONES DE TELETRANPORTE (PROXIMIDAD Y PORTALES) ---
from funciones.movimiento.perimetro import verificar_proximidad_tp
from funciones.movimiento.teleport_db import (
    viajar_a_nombre_directo, 
    guardar_lugar, 
    eliminar_lugar,
    marcar_proximidad,
    crear_portal_externo  # <--- Agregado para salas externas
)

load_dotenv()

class MyBot(BaseBot):
    async def on_start(self, session_metadata):
        print("Bot V18: Sistema de Universidad UTC Activo (Portales + Elevadores).")

    # Evento: Alguien entra a la sala
    async def on_user_join(self, user: User, position: Position):
        await registrar_entrada(self, user)

    # Evento: Movimiento (Detección de Proximidad para Elevadores y Portales)
    async def on_user_move(self, user: User, destination: Position):
        # Esta función revisa si el avatar pisó un sensor interno o un portal externo
        await verificar_proximidad_tp(self, user, destination)

    # Evento: Chat Público
    async def on_chat(self, user: User, message: str):
        # 1. Guardar Log
        guardar_log_chat(user.username, message, "publico")

        # 2. Seguridad y AutoMod
        rol = await obtener_rol(user.id)
        fue_baneado = await verificar_automod(self, user, message, rol)
        if fue_baneado: return 

        # 3. COMANDOS CON EXCLAMACIÓN (!)
        if message.startswith("!"):
            # Comandos generales
            await manejar_moderacion(self, user, message)
            await manejar_ropa(self, user, message)
            await manejar_movimiento(self, user, message)
            
            # Gestión de Lugares fijos
            if message.startswith("!guardar"):
                await guardar_lugar(self, user, message)
            
            elif message.startswith("!eliminar"):
                await eliminar_lugar(self, user, message)
            
            # Gestión de Elevadores Internos
            elif message.startswith("!sensor"):
                await marcar_proximidad(self, user, message)
            
            # Gestión de Portales a OTRAS SALAS
            elif message.startswith("!portal"):
                await crear_portal_externo(self, user, message)
                
            return 

        # 4. VIAJE POR NOMBRE DIRECTO (Sin !)
        await viajar_a_nombre_directo(self, user, message)

    # Evento: Susurros
    async def on_whisper(self, user: User, message: str):
        guardar_log_chat(user.username, message, "susurro")
        await manejar_moderacion(self, user, message)
        
        if message.lower() == "!mi_id":
            await self.highrise.send_whisper(user.id, f"Tu ID es: {user.id}")

if __name__ == "__main__":
    room_id = os.getenv("ROOM_ID")
    api_token = os.getenv("BOT_TOKEN")

    if not room_id or not api_token:
        print("❌ ERROR: No se encontraron ROOM_ID o BOT_TOKEN")
    else:
        definitions = [BotDefinition(MyBot(), room_id, api_token)]
        asyncio.run(main(definitions))