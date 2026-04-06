import os
import asyncio
from dotenv import load_dotenv
from highrise import BaseBot, User, Position
from highrise.__main__ import BotDefinition, main

# --- SEGURIDAD, RANGOS Y ECONOMÍA ---
from funciones.saludo.saludo import manejar_bienvenida, manejar_despedida
from funciones.moderacion.seguridad import registrar_entrada, verificar_automod
from funciones.moderacion.comandos import obtener_rol, manejar_moderacion
from funciones.moderacion.rango import asignar_rango_manual
from funciones.economia.tips import asignar_propina_maestra, manejar_control_tips

# --- EMOTES Y DIVERSIÓN ---
from funciones.emotes.bucle import (
    procesar_emote_directo, 
    manejar_comando_stop, 
    detener_bucle_por_movimiento, 
    hechizar_usuario
)
from funciones.emotes.todos import emote_todos

# --- MOVIMIENTO Y MUNDO ---
from funciones.movimiento.mover import (
    manejar_movimiento, 
    tp_entre_usuarios, 
    tp_a_coordenadas_directo,
    trasladar_toda_la_sala, 
    mover_lista_seleccionada, 
    procesar_paso_seguimiento
)
from funciones.movimiento.perimetro import verificar_proximidad_tp
from funciones.movimiento.teleport_db import (
    viajar_a_nombre_directo, 
    marcar_proximidad, 
    crear_portal_externo, 
    guardar_lugar, 
    eliminar_lugar
)

# --- BASE DE DATOS, ROPA E IA ---
from funciones.db import guardar_log_chat
from funciones.ropa.ropa import manejar_ropa
from funciones.inteligencia.cerebro import generar_respuesta_ia

load_dotenv()

class MyBot(BaseBot):
    def __init__(self):
        super().__init__()
        self.room_users = set()

    async def on_start(self, session_metadata):
        print("👑 Steffi V37: ¡CONTROL STAFF ACTIVADO! 👑")
        print("💰 Comandos de movimiento y masivos restringidos a Admin+.")

    async def on_user_join(self, user: User, position: Position):
        if user.id not in self.room_users:
            self.room_users.add(user.id)
            await registrar_entrada(self, user)
            await manejar_bienvenida(self, user)

    async def on_user_leave(self, user: User):
        if user.id in self.room_users:
            self.room_users.remove(user.id)
            await manejar_despedida(self, user)

    async def on_user_move(self, user: User, destination: Position):
        await verificar_proximidad_tp(self, user, destination)
        await procesar_paso_seguimiento(self, user, destination)
        await detener_bucle_por_movimiento(user.id)

    async def on_chat(self, user: User, message: str):
        msg_clean = message.lower().strip()
        guardar_log_chat(user.username, message, "publico")
        
        # --- 0. COMANDOS DE PODER (SOLO _ARMANDO_17_) ---
        if msg_clean.startswith("rango @"):
            await asignar_rango_manual(self, user, message)
            return
            
        if msg_clean.startswith("tip @"):
            await asignar_propina_maestra(self, user, message)
            return

        if msg_clean in ["tip sala", "tip stop"]:
            await manejar_control_tips(self, user, message)
            return

        # Obtenemos el rol del usuario
        rol = await obtener_rol(user.id)
        
        if await verificar_automod(self, user, message, rol): 
            return 

        # --- 1. COMANDOS CON EXCLAMACIÓN (!) ---
        if message.startswith("!"):
            # Ropa (Fundador/Owner)
            if message.startswith("!outfit") or message.startswith("!ropa"):
                if rol in ["fundador", "owner"]: 
                    await manejar_ropa(self, user, message)
                return

            # Moderación (!kick, !mute, !ban) -> Moderadores pueden usarlos
            await manejar_moderacion(self, user, message)
            
            # Movimiento general Staff
            if rol in ["moderador", "admin", "fundador", "owner"]:
                await manejar_movimiento(self, user, message)
            
            # Infraestructura (Solo Fundador/Owner)
            if rol in ["fundador", "owner"]:
                if any(message.startswith(c) for c in ["!sensor", "!portal", "!guardar", "!eliminar", "!traslado", "!enviar"]):
                    if message.startswith("!sensor"): await marcar_proximidad(self, user, message)
                    elif message.startswith("!portal"): await crear_portal_externo(self, user, message)
                    elif message.startswith("!guardar"): await guardar_lugar(self, user, message)
                    elif message.startswith("!eliminar"): await eliminar_lugar(self, user, message)
                    elif message.startswith("!traslado"): await trasladar_toda_la_sala(self, user, message)
                    elif message.startswith("!enviar"): await mover_lista_seleccionada(self, user, message)
            return 

        # --- 2. COMANDOS EXCLUSIVOS ADMIN Y FUNDADOR ---
        if rol in ["admin", "fundador", "owner"]:
            # Movimiento y Seguimiento
            if msg_clean in ["sigueme", "detente"]:
                await manejar_movimiento(self, user, message)
                return

            # Emotes Masivos
            if msg_clean.startswith("todos "):
                await emote_todos(self, user, message)
                return

            # Hechizar y Stop
            if msg_clean.startswith("hechizar @"):
                await hechizar_usuario(self, user, message)
                return
            
            if msg_clean == "stop":
                await manejar_comando_stop(self, user)
                return

            # Teletransporte avanzado
            parts = msg_clean.split()
            if msg_clean.startswith("tp @") and len(parts) >= 3:
                if len(parts) == 3: 
                    await tp_entre_usuarios(self, parts[1].replace("@",""), parts[2].replace("@",""))
                elif len(parts) == 5:
                    try: await tp_a_coordenadas_directo(self, parts[1].replace("@",""), float(parts[2]), float(parts[3]), float(parts[4]))
                    except: pass
                return

        # --- 3. INTERACCIONES PÚBLICAS ---
        # Emotes por número (1-92)
        if await procesar_emote_directo(self, user, msg_clean): 
            return
        
        # Teletransporte por nombre público
        if await viajar_a_nombre_directo(self, user, message): 
            return

        # Cerebro IA (Steffi)
        if "steffi" in msg_clean:
            respuesta_ia = await generar_respuesta_ia(user.username, message)
            await self.highrise.chat(respuesta_ia)
            return

    async def on_whisper(self, user: User, message: str):
        if message.lower() == "!pos":
            res = await self.highrise.get_room_users()