import os
import asyncio
import logging
from dotenv import load_dotenv
from flask import Flask
from threading import Thread
from highrise import BaseBot, User, Position
from highrise.__main__ import BotDefinition, main

# --- 1. SILENCIAR TERMINAL (Flask y Warnings) ---
# Esto elimina los mensajes de "Serving Flask" y "Running on http"
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# --- SEGURIDAD, RANGOS Y ECONOMÍA ---
from funciones.saludo.saludo import manejar_bienvenida, manejar_despedida
from funciones.moderacion.seguridad import registrar_entrada, verificar_automod
from funciones.moderacion.comandos import obtener_rol, manejar_moderacion
from funciones.moderacion.rango import asignar_rango_manual
from funciones.economia.tips import asignar_propina_maestra, manejar_control_tips
from funciones.moderacion.multi_bot import rentar_bot, apagar_bot_actual

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
    viajar_a_nombre_directo, marcar_proximidad, 
    crear_portal_externo, guardar_lugar, eliminar_lugar, eliminar_sensor
)

from funciones.db import guardar_log_chat
from funciones.ropa.ropa import manejar_ropa

load_dotenv()

# --- CONFIGURACIÓN KEEP ALIVE ---
app = Flask('')
@app.route('/')
def home(): return "Online"

def run():
    # Silenciamos el banner de Flask al arrancar
    app.run(host='0.0.0.0', port=7860, debug=False, use_reloader=False)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

class MyBot(BaseBot):
    def __init__(self):
        super().__init__()
        self.room_users = set()

    async def on_start(self, session_metadata):
        # ... tu código actual ...
        print("✅ Bot en Linea")
        
        # Lógica de Autodestrucción por Renta
        tiempo_renta = os.getenv("TIEMPO_RENTA")
        if tiempo_renta:
            segundos = int(tiempo_renta)
            print(f"🕒 Este bot se apagará en {segundos} segundos.")
            
            async def temporizador_salida():
                await asyncio.sleep(segundos)
                print("⏰ Tiempo de renta agotado. Cerrando...")
                os._exit(0) # El bot se apaga. 
            
            asyncio.create_task(temporizador_salida())

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
        
        if msg_clean.startswith("rango @"):
            await asignar_rango_manual(self, user, message)
            return
        if msg_clean.startswith("tip @"):
            await asignar_propina_maestra(self, user, message)
            return
        if msg_clean in ["tip sala", "tip stop"]:
            await manejar_control_tips(self, user, message)
            return

        rol = await obtener_rol(user.id)
        if await verificar_automod(self, user, message, rol): return 

        if message.startswith("!"):
            if message.startswith("!outfit") or message.startswith("!ropa"):
                if rol in ["fundador", "owner"]: await manejar_ropa(self, user, message)
                return
            await manejar_moderacion(self, user, message)
            if rol in ["moderador", "admin", "fundador", "owner"]:
                await manejar_movimiento(self, user, message)
            if rol in ["fundador", "owner"]:
                if any(message.startswith(c) for c in ["!sensor", "!portal", "!guardar", "!eliminar", "!traslado", "!enviar", "!borrar_sensor"]):
                    
                    if message.startswith("!borrar_sensor"): 
                        await eliminar_sensor(self, user, message)
                    
                    elif message.startswith("!sensor"): await marcar_proximidad(self, user, message)
                    elif message.startswith("!portal"): await crear_portal_externo(self, user, message)
                    elif message.startswith("!guardar"): await guardar_lugar(self, user, message)
                    elif message.startswith("!eliminar"): await eliminar_lugar(self, user, message)
                    elif message.startswith("!traslado"): await trasladar_toda_la_sala(self, user, message)
                    elif message.startswith("!enviar"): await mover_lista_seleccionada(self, user, message)
            return 

        if rol in ["admin", "fundador", "owner"]:
            if msg_clean in ["sigueme", "detente"]:
                await manejar_movimiento(self, user, message)
                return
            if msg_clean.startswith("todos "):
                await emote_todos(self, user, message)
                return
            if msg_clean.startswith("hechizar @"):
                await hechizar_usuario(self, user, message)
                return
            if msg_clean == "stop":
                await manejar_comando_stop(self, user)
                return
            
            parts = msg_clean.split()
            if msg_clean.startswith("tp @") and len(parts) >= 3:
                if len(parts) == 3: await tp_entre_usuarios(self, parts[1].replace("@",""), parts[2].replace("@",""))
                elif len(parts) == 5:
                    try: await tp_a_coordenadas_directo(self, parts[1].replace("@",""), float(parts[2]), float(parts[3]), float(parts[4]))
                    except: pass
                return

        if await procesar_emote_directo(self, user, msg_clean): 
            return
            
        if await viajar_a_nombre_directo(self, user, message): 
            return

    async def on_whisper(self, user: User, message: str):
        msg = message.lower().strip()
        
        # Comando para rentar o activar (usamos la misma función)
        if msg.startswith("rentar ") or msg.startswith("activar "):
            await rentar_bot(self, user, message)
            return

        # Comando para apagar el bot actual
        if msg == "apagar":
            await apagar_bot_actual(self, user)
            return

        # Tu comando de posición
        if msg == "!pos":
            res = await self.highrise.get_room_users()
            pos = next((p for u, pos in res.content if u.id == user.id), None)
            if pos: 
                await self.highrise.send_whisper(user.id, f"📍 Pos: {pos.x} {pos.y} {pos.z}")

if __name__ == "__main__":
    room_id = os.getenv("ROOM_ID")
    api_token = os.getenv("BOT_TOKEN")
    
    if room_id and api_token:
        keep_alive() 
        definitions = [BotDefinition(MyBot(), room_id, api_token)]
        
        # Bucle de reconexión silencioso
        while True:
            try:
                asyncio.run(main(definitions))
            except Exception:
                import time
                time.sleep(5)
    else:
        print("❌ Error: Faltan las variables de entorno en el archivo .env")