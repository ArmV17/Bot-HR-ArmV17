import os
import yt_dlp
from highrise import BaseBot, User
from funciones.moderacion.comandos import obtener_rol

# Ruta segura para los créditos dentro de la carpeta actual o raíz
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDITS_FILE = os.path.join(BASE_DIR, "music_credits.txt")

def verificar_y_gastar_credito(username: str) -> bool:
    """Verifica si el usuario tiene créditos de propina disponibles y gasta uno"""
    if not os.path.exists(CREDITS_FILE):
        return False
    
    with open(CREDITS_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    usuario_encontrado = False
    nuevas_lineas = []
    
    for line in lines:
        parts = line.strip().split(":")
        if len(parts) == 2:
            u_name, credits = parts[0], int(parts[1])
            if u_name.lower() == username.lower() and not usuario_encontrado:
                if credits > 0:
                    usuario_encontrado = True
                    credits -= 1
                    if credits > 0:
                        nuevas_lineas.append(f"{u_name}:{credits}\n")
                else:
                    nuevas_lineas.append(line)
            else:
                nuevas_lineas.append(line)
                
    with open(CREDITS_FILE, "w", encoding="utf-8") as f:
        f.writelines(nuevas_lineas)
        
    return usuario_encontrado

def agregar_credito_usuario(username: str):
    """Agrega un crédito de canción cuando el usuario dona 10g"""
    lineas = []
    if os.path.exists(CREDITS_FILE):
        with open(CREDITS_FILE, "r", encoding="utf-8") as f:
            lineas = f.readlines()
            
    usuario_encontrado = False
    nuevas_lineas = []
    
    for line in lineas:
        parts = line.strip().split(":")
        if len(parts) == 2:
            u_name, credits = parts[0], int(parts[1])
            if u_name.lower() == username.lower():
                usuario_encontrado = True
                credits += 1
                nuevas_lineas.append(f"{u_name}:{credits}\n")
            else:
                nuevas_lineas.append(line)
        else:
            nuevas_lineas.append(line)
            
    if not usuario_encontrado:
        nuevas_lineas.append(f"{username}:1\n")
        
    with open(CREDITS_FILE, "w", encoding="utf-8") as f:
        f.writelines(nuevas_lineas)

async def manejar_comando_musica(bot: BaseBot, user: User, message: str):
    """Procesa comandos de música permitiendo acceso libre a administradores/dueños o usuarios con créditos"""
    try:
        rol_usuario = await obtener_rol(user.id)
        if not rol_usuario:
            rol_usuario = ""
        
        rol_limpio = str(rol_usuario).lower().strip()
        roles_permitidos = ["owner", "fundador", "admin", "moderator", "moderador"]
        es_admin_o_dueno = rol_limpio in roles_permitidos
        
        if not es_admin_o_dueno:
            tiene_credito = verificar_y_gastar_credito(user.username)
            if not tiene_credito:
                await bot.highrise.send_whisper(
                    user.id, 
                    "❌ Para pedir una canción debes ser administrador o donar **10g** al bot."
                )
                return

        parts = message.strip().split(" ", 1)
        if len(parts) < 2:
            await bot.highrise.send_whisper(user.id, "Uso correcto: `!play [nombre de la canción]`")
            if not es_admin_o_dueno:
                agregar_credito_usuario(user.username)
            return

        query = parts[1].strip()
        await bot.highrise.send_whisper(user.id, f"🔍 Buscando: '{query}'...")

        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'default_search': 'ytsearch',
            'max_downloads': 1,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:
                info = info['entries'][0]
            
            song_title = info.get('title', 'Canción sin título')
            song_url = info.get('webpage_url') or info.get('url', '')

            with open("queue.txt", "a", encoding="utf-8") as f:
                f.write(f"{song_title}|{song_url}\n")

            await bot.highrise.chat(f"🎵 ¡Canción agregada a la cola por @{user.username}: {song_title}!")

    except Exception as e:
        print(f"⚠️ Error al procesar música: {e}")
        await bot.highrise.send_whisper(user.id, "❌ Ocurrió un error al buscar la canción.")

async def manejar_musica_por_propina(bot: BaseBot, sender: User, amount: int):
    """Registra la propina de 10g y le otorga un turno de canción al usuario"""
    try:
        if amount >= 10:
            agregar_credito_usuario(sender.username)
            await bot.highrise.send_whisper(
                sender.id, 
                f"✨ ¡Gracias por tus {amount}g! Tienes un turno de música disponible. Escribe `!play [canción]` para reproducirla."
            )
    except Exception as e:
        print(f"⚠️ Error al procesar propina musical: {e}")
        