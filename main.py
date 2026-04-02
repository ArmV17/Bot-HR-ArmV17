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

# --- IMPORTACIONES DE MOVIMIENTO (PROXIMIDAD Y TRASLADOS) ---
from funciones.movimiento.mover import (
    manejar_movimiento, 
    tp_entre_usuarios, 
    tp_a_coordenadas_directo,
    trasladar_toda_la_sala, # Función inteligente (Nombre o ID)
    mover_lista_seleccionada # Función inteligente (Nombre o ID)
)
from funciones.movimiento.perimetro import verificar_proximidad_tp
from funciones.movimiento.teleport_db import (
    viajar_a_nombre_directo,
    guardar_lugar,
    eliminar_lugar,
    marcar_proximidad,
    crear_portal_externo
)

load_dotenv()

class MyBot(BaseBot):
    async def on_start(self, session_metadata):
        print("🚀 Bot V23: Universidad UTC - Sistema de Traslado Híbrido Activo.")
        print("💡 Ahora puedes usar !traslado [nombre_portal] o [room_id]")

    async def on_user_join(self, user: User, position: Position):
        await registrar_entrada(self, user)

    async def on_user_move(self, user: User, destination: Position):
        # Sensores de proximidad (Elevadores y Portales)
        await verificar_proximidad_tp(self, user, destination)

    async def on_chat(self, user: User, message: str):
        guardar_log_chat(user.username, message, "publico")

        # Obtener Rol y Seguridad
        rol = await obtener_rol(user.id)
        if await verificar_automod(self, user, message, rol): return 

        # --- 1. COMANDOS CON EXCLAMACIÓN (!) ---
        if message.startswith("!"):
            # Ropa: SOLO FUNDADOR
            if message.startswith("!outfit") or message.startswith("!ropa"):
                if rol in ["fundador", "owner"]:
                    await manejar_ropa(self, user, message)
                else:
                    await self.highrise.send_whisper(user.id, "❌ Solo el Fundador puede cambiar mi ropa.")
                return

            # Moderación y Movimiento Base
            await manejar_moderacion(self, user, message)
            await manejar_movimiento(self, user, message)
            
            # --- SECCIÓN EXCLUSIVA FUNDADOR (Infraestructura y Traslados) ---
            if rol in ["fundador", "owner"]:
                # Sensores y Portales
                if message.startswith("!sensor"): await marcar_proximidad(self, user, message)
                elif message.startswith("!portal"): await crear_portal_externo(self, user, message)
                
                # Lugares Públicos
                elif message.startswith("!guardar"): await guardar_lugar(self, user, message)
                elif message.startswith("!eliminar"): await eliminar_lugar(self, user, message)
                
                # TRASLADOS INTELIGENTES (ID o Nombre de Portal)
                elif message.startswith("!traslado"):
                    await trasladar_toda_la_sala(self, user, message)
                elif message.startswith("!enviar"):
                    await mover_lista_seleccionada(self, user, message)
            
            # Alerta de Permisos para Admins/Mods
            elif any(message.startswith(cmd) for cmd in ["!sensor", "!portal", "!guardar", "!eliminar", "!traslado", "!enviar"]):
                await self.highrise.send_whisper(user.id, "❌ Permiso denegado. Función exclusiva del Fundador.")
            
            return 

        # --- 2. TELETRANSPORTE DIRECTO (@) - STAFF ---
        if message.startswith("@"):
            if rol in ["admin", "fundador", "owner", "moderador"]:
                parts = message.split()
                # @User1 @User2
                if len(parts) == 2 and parts[1].startswith("@"):
                    await tp_entre_usuarios(self, parts[0].replace("@",""), parts[1].replace("@",""))
                
                # @User X Y Z
                elif len(parts) == 4:
                    try:
                        u_target = parts[0].replace("@","")
                        x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                        await tp_a_coordenadas_directo(self, u_target, x, y, z)
                    except: pass
            return

        # --- 3. VIAJE POR NOMBRE DIRECTO (Público) ---
        await viajar_a_nombre_directo(self, user, message)

    async def on_whisper(self, user: User, message: str):
        guardar_log_chat(user.username, message, "susurro")
        await manejar_moderacion(self, user, message)
        
        # Consultar Posición (Para el Fundador)
        if message.lower() == "!pos":
            res = await self.highrise.get_room_users()
            pos = next((p for u, p in res.content if u.id == user.id), None)
            if pos:
                await self.highrise.send_whisper(user.id, f"📍 Posición UTC: {pos.x} {pos.y} {pos.z}")

if __name__ == "__main__":
    room_id = os.getenv("ROOM_ID")
    api_token = os.getenv("BOT_TOKEN")

    if not room_id or not api_token:
        print("❌ ERROR: Revisa el archivo .env")
    else:
        definitions = [BotDefinition(MyBot(), room_id, api_token)]
        asyncio.run(main(definitions))