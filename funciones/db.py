import os
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
        data = {
            "id_jugador": user_id, 
            "username": username
        }
        # Intentamos una operación simple
        supabase.table("usuarios").upsert(data).execute()
        print(f"✅ DB: Sincronizado correctamente con Supabase.")
    except Exception as e:
        print(f"❌ ERROR DE RED/DB: {e}")