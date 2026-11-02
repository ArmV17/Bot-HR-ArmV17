import os
import time
import subprocess
import yt_dlp

ZENO_SERVER = os.getenv("ZENO_SERVER", "stream.zeno.fm")
ZENO_PORT = os.getenv("ZENO_PORT", "80")
ZENO_PASSWORD = os.getenv("ZENO_PASSWORD", "")
ZENO_MOUNT = os.getenv("ZENO_MOUNT", "d12hw8zdlduvv")

def reproducir_stream():
    print("📻 Servicio de Streaming iniciado...")
    while True:
        try:
            if os.path.exists("queue.txt"):
                with open("queue.txt", "r", encoding="utf-8") as f:
                    lines = [line.strip() for line in f.readlines() if line.strip()]
                
                if lines:
                    current_line = lines[0]
                    restantes = lines[1:]

                    with open("queue.txt", "w", encoding="utf-8") as f:
                        for r in restantes:
                            f.write(r + "\n")

                    parts = current_line.split("|")
                    if len(parts) >= 2:
                        titulo = parts[0]
                        url = parts[1]
                        print(f"▶️ Procesando de la cola: {titulo} ({url})")

                        ydl_opts = {
                            'format': 'bestaudio/best',
                            'noplaylist': True,
                        }
                        
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            info = ydl.extract_info(url, download=False)
                            audio_url = info.get('url')

                        if audio_url:
                            print(f"🎵 Transmitiendo al aire: {titulo}")
                            
                            # Garantiza que el punto de montaje comience con barra diagonal
                            mount_path = ZENO_MOUNT if ZENO_MOUNT.startswith('/') else f"/{ZENO_MOUNT}"
                            target_url = f"icecast://source:{ZENO_PASSWORD}@{ZENO_SERVER}:{ZENO_PORT}{mount_path}"
                            
                            ffmpeg_cmd = [
                                'ffmpeg', '-re', '-i', audio_url,
                                '-f', 'mp3', '-ab', '128k',
                                target_url
                            ]

                            subprocess.run(ffmpeg_cmd)
        except Exception as e:
            print(f"⚠️ Error en el bucle del streamer: {e}")
        
        time.sleep(2)

if __name__ == "__main__":
    reproducir_stream()
    