import os
from datetime import datetime
import pytz  # Librería para manejar la zona horaria de México
from supabase import create_client, Client
from dotenv import load_dotenv

# Cargamos el .env
load_dotenv()

# Limpiamos posibles espacios o comillas de las variables
url = os.getenv("SUPABASE_URL", "").strip().replace('"', '').replace("'", "")
key = os.getenv("SUPABASE_KEY", "").strip().replace('"', '').replace("'", "")

if not url or not key:
    print("❌ ERROR: Faltan las llaves en el .env")
    exit()

try:
    # Intentamos crear el cliente
    supabase: Client = create_client(url, key)
except Exception as e:
    print(f"❌ Error al configurar el cliente de Supabase: {e}")

def guardar_usuario_db(user_id: str, username: str):
    try:
        # 1. Obtener la hora de México
        zona_mx = pytz.timezone('America/Mexico_City')
        ahora_mx = datetime.now(zona_mx)
        fecha_login = ahora_mx.strftime("%d/%m/%Y %I:%M %p")

        data = {
            "id_jugador": str(user_id), 
            "username": str(username),
            "ultima_conexion": fecha_login  # Enviamos el texto formateado
        }
        
        # .upsert actualizará la 'ultima_conexion' cada vez que el usuario entre
        supabase.table("usuarios").upsert(data).execute()
        print(f"✅ DB: {username} sincronizado a las {fecha_login}")
        
    except Exception as e:
        print(f"❌ ERROR DE RED/DB (Usuarios): {e}")

def registrar_moderacion(ejecutor: str, objetivo: str, accion: str, razon: str = "N/A"):
    try:
        # 1. Obtener la hora actual de México (Saltillo/CDMX)
        zona_mx = pytz.timezone('America/Mexico_City')
        ahora_mx = datetime.now(zona_mx)

        # 2. Formatear: Día/Mes/Año Hora:Minutos AM/PM
        # %I es hora 01-12, %p es AM/PM
        fecha_formateada = ahora_mx.strftime("%d/%m/%Y %I:%M %p")

        data = {
            "ejecutor_username": str(ejecutor),
            "objetivo_username": str(objetivo),
            "accion": str(accion),
            "razon": str(razon),
            "creado_el": str(fecha_formateada) # Forzamos que sea String
        }
        
        supabase.table("historial_moderacion").insert(data).execute()
        print(f"📝 Historial: {accion} registrado a las {fecha_formateada}")
        
    except Exception as e:
        print(f"❌ Error al guardar historial: {e}")