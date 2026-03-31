import os
import pytz
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL", "").strip().replace('"', '').replace("'", "")
key = os.getenv("SUPABASE_KEY", "").strip().replace('"', '').replace("'", "")

try:
    supabase: Client = create_client(url, key)
except Exception as e:
    print(f"❌ Error Supabase: {e}")

def guardar_usuario_db(user_id: str, username: str):
    try:
        zona_mx = pytz.timezone('America/Mexico_City')
        fecha_login = datetime.now(zona_mx).strftime("%d/%m/%Y %I:%M %p")
        data = {"id_jugador": str(user_id), "username": str(username), "ultima_conexion": fecha_login}
        supabase.table("usuarios").upsert(data).execute()
    except Exception as e:
        print(f"❌ Error DB Usuarios: {e}")

def registrar_moderacion(ejecutor: str, objetivo: str, accion: str, razon: str = "N/A"):
    try:
        zona_mx = pytz.timezone('America/Mexico_City')
        fecha_mx = datetime.now(zona_mx).strftime("%d/%m/%Y %I:%M %p")
        data = {"ejecutor_username": str(ejecutor), "objetivo_username": str(objetivo), "accion": str(accion), "razon": str(razon), "creado_el": fecha_mx}
        supabase.table("historial_moderacion").insert(data).execute()
    except Exception as e:
        print(f"❌ Error Historial: {e}")

# ESTA ES LA FUNCIÓN QUE TE ESTÁ DANDO EL ERROR DE IMPORTACIÓN
def guardar_log_chat(username: str, mensaje: str, canal: str):
    try:
        zona_mx = pytz.timezone('America/Mexico_City')
        fecha_mx = datetime.now(zona_mx).strftime("%d/%m/%Y %I:%M %p")
        data = {"username": str(username), "mensaje": str(mensaje), "canal": str(canal), "fecha_hora": fecha_mx}
        supabase.table("log_chat").insert(data).execute()
    except Exception as e:
        print(f"❌ Error Log Chat: {e}")

def limpiar_tabla_chat():
    try:
        supabase.table("log_chat").delete().neq("id", 0).execute()
        return True
    except Exception as e:
        print(f"❌ Error Limpiar: {e}")
        return False