import asyncio
import random
from highrise import BaseBot, User

# Variable global para controlar el estado del sorteo
tip_sala_activo = False

async def asignar_propina_maestra(bot: BaseBot, user: User, message: str):
    """
    Comando: tip @usuario [cantidad]
    Restricción: Solo _Armando_17_ puede ejecutarlo.
    Envía una cantidad específica de oro a un usuario.
    """
    if user.username.lower() != "_armando_17_":
        await bot.highrise.send_whisper(user.id, "⛔ No tienes permiso para mover el oro del bot.")
        return

    try:
        parts = message.split()
        if len(parts) < 3:
            await bot.highrise.send_whisper(user.id, "❌ Uso: tip @usuario [cantidad]")
            return

        target_username = parts[1].replace("@", "").lower()
        
        try:
            amount = int(parts[2])
            if amount <= 0: return
        except:
            await bot.highrise.send_whisper(user.id, "❌ Cantidad de oro inválida.")
            return

        # 1. Verificar billetera del bot
        bot_wallet = await bot.highrise.get_wallet()
        bot_amount = bot_wallet.content[0].amount

        # Diccionarios de Barras y Comisiones de Highrise
        bars_dictionary = {10000: "gold_bar_10k", 5000: "gold_bar_5000", 1000: "gold_bar_1k",
                           500: "gold_bar_500", 100: "gold_bar_100", 50: "gold_bar_50",
                           10: "gold_bar_10", 5: "gold_bar_5", 1: "gold_bar_1"}
        
        fees_dictionary = {10000: 1000, 5000: 500, 1000: 100, 500: 50, 
                           100: 10, 50: 5, 10: 1, 5: 1, 1: 1}

        # 2. Buscar al objetivo
        room_users = (await bot.highrise.get_room_users()).content
        target_user = next((u for u, p in room_users if u.username.lower() == target_username), None)

        if not target_user:
            await bot.highrise.send_whisper(user.id, f"❌ @{target_username} no está en la sala.")
            return

        # 3. Calcular barras y taxes
        temp_amount = amount
        tip_list = []
        total_necesario_con_fees = 0

        for bar in sorted(bars_dictionary.keys(), reverse=True):
            while temp_amount >= bar:
                tip_list.append(bars_dictionary[bar])
                total_necesario_con_fees += (bar + fees_dictionary[bar])
                temp_amount -= bar

        if total_necesario_con_fees > bot_amount:
            await bot.highrise.chat(f"⚠️ Fondos insuficientes. Necesito {total_necesario_con_fees}g (con taxes).")
            return

        # 4. Enviar tips
        for bar_item in tip_list:
            await bot.highrise.tip_user(target_user.id, bar_item)
        
        await bot.highrise.chat(f"💰 ¡Hecho! He enviado {amount}g a @{target_username} por orden de Armando. ✨")

    except Exception as e:
        print(f"Error en tip manual: {e}")

# --- SECCIÓN DE SORTEO AUTOMÁTICO (TIP SALA) ---

async def bucle_tips_automaticos(bot: BaseBot):
    """Lógica que corre cada 5 minutos enviando 1g a alguien al azar."""
    global tip_sala_activo
    
    while tip_sala_activo:
        try:
            # Espera 5 minutos (300 segundos)
            await asyncio.sleep(300)
            
            if not tip_sala_activo: break

            res = await bot.highrise.get_room_users()
            room_users = [u for u, p in res.content]

            # Candidatos: Nadie que sea Armando ni el bot (Steffi)
            candidatos = [u for u in room_users if u.username.lower() not in ["_armando_17_", "steffi"]]

            if len(candidatos) > 0:
                ganador = random.choice(candidatos)
                
                # Verificar si el bot tiene al menos 2g (1g de la barra + 1g del fee)
                wallet = await bot.highrise.get_wallet()
                if wallet.content[0].amount >= 2:
                    await bot.highrise.tip_user(ganador.id, "gold_bar_1")
                    await bot.highrise.chat(f"🎁 ¡SORTEO! He enviado 1g a @{ganador.username} por estar activo. ¡Suerte a la próxima! 🍀")
                else:
                    print("⚠️ Sorteo pausado: El bot se quedó sin oro.")
            
        except Exception as e:
            print(f"Error en sorteo automático: {e}")
            await asyncio.sleep(10)

async def manejar_control_tips(bot: BaseBot, user: User, message: str):
    """Activa o desactiva el sorteo de 1g cada 5 minutos."""
    global tip_sala_activo
    
    if user.username.lower() != "_armando_17_":
        return

    msg = message.lower().strip()

    if msg == "tip sala":
        if not tip_sala_activo:
            tip_sala_activo = True
            await bot.highrise.chat("✅ Sorteo de oro ACTIVADO. ¡1g al azar cada 5 minutos!")
            asyncio.create_task(bucle_tips_automaticos(bot))
        else:
            await bot.highrise.send_whisper(user.id, "⚠️ El sorteo ya está corriendo.")

    elif msg == "tip stop":
        if tip_sala_activo:
            tip_sala_activo = False
            await bot.highrise.chat("🛑 Sorteo de oro DESACTIVADO.")
        else:
            await bot.highrise.send_whisper(user.id, "⚠️ El sorteo ya estaba apagado.")