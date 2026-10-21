import asyncio
from highrise import BaseBot, User, Item
from funciones.db import obtener_rol 

categories = [
    "aura","bag","blush","body","dress","earrings","emote","eye","eyebrow",
    "fishing_rod","freckle","fullsuit","glasses","gloves","hair_back",
    "hair_front","handbag","hat","jacket","lashes","mole","mouth",
    "necklace","nose","rod","shirt","shoes","shorts","skirt","sock","tattoo","watch"
]

async def manejar_ropa(bot: BaseBot, user: User, message: str):
    msg = message.lower().strip()
    
    # --- SEGURIDAD: Solo el Fundador o Owner ---
    rol = await obtener_rol(user.id)
    if rol not in ["fundador", "owner"]:
        return

    if msg.startswith("!search ") or msg.startswith("!buscar "):
        await buscar_prendas(bot, user, message)
    elif msg.startswith("!buy "):
        await comprar_prenda(bot, user, message)
    elif msg.startswith("!equip "):
        await equipar_prenda(bot, user, message)
    elif msg.startswith("!remove "):
        await quitar_prenda(bot, user, message)
    elif msg.startswith("!skin "):
        await cambiar_piel(bot, user, message)
    elif msg.startswith("!hair "):
        await cambiar_color_pelo(bot, user, message)
    elif msg.startswith("!eye "):
        await cambiar_color_ojos(bot, user, message)
    elif msg.startswith("!lips "):
        await cambiar_color_labios(bot, user, message)
    elif msg == "!outfit" or msg == "!ropa":
        await mostrar_info_outfit(bot, user)

async def buscar_prendas(bot: BaseBot, user: User, message: str):
    parts = message.split(" ")
    if len(parts) < 2:
        await bot.highrise.send_whisper(user.id, "❌ Uso: !search [nombre de la prenda]")
        return

    termino = " ".join(parts[1:]).strip()

    try:
        await bot.highrise.send_whisper(user.id, f"🔍 Buscando prendas para '{termino}'...")
        items_encontrados = (await bot.webapi.get_items(item_name=termino)).items
        
        if not items_encontrados:
            await bot.highrise.send_whisper(user.id, f"❓ No encontré ninguna prenda con el nombre '{termino}'.")
            return

        resultados = items_encontrados[:5]
        await bot.highrise.send_whisper(user.id, f"📦 Encontré {len(items_encontrados)} resultados. Mostrando los primeros:")
        
        for item in resultados:
            await bot.highrise.send_whisper(user.id, f"• ID: {item.id}")
            
        await bot.highrise.send_whisper(user.id, "💡 Usa !buy [ID] para comprarlo o !equip [ID] para ponértelo.")

    except Exception as e:
        print(f"Error buscando prendas: {e}")
        await bot.highrise.send_whisper(user.id, "❌ Hubo un error al realizar la búsqueda.")

async def comprar_prenda(bot: BaseBot, user: User, message: str):
    parts = message.split(" ")
    if len(parts) < 2:
        await bot.highrise.send_whisper(user.id, "❌ Uso: !buy [ID de la prenda]")
        return

    entrada = " ".join(parts[1:]).strip()

    try:
        if "-" not in entrada:
            await bot.highrise.send_whisper(user.id, "⚠️ Por favor usa el ID exacto con guiones (ej: !buy shirt-...). Usa !search primero para verlo.")
            return

        await bot.highrise.send_whisper(user.id, f"💳 Comprando ítem: {entrada}...")
        res = await bot.highrise.buy_item(entrada)
        
        if res:
            await bot.highrise.send_whisper(user.id, f"✅ ¡Compra exitosa! Equipando...")
            await equipar_item_directo(bot, user, entrada)
        else:
            await bot.highrise.send_whisper(user.id, "❌ No se pudo completar la compra (fondos insuficientes o ítem no disponible).")

    except Exception as e:
        print(f"Error al comprar prenda: {e}")
        await bot.highrise.send_whisper(user.id, "❌ Hubo un error al intentar comprar la prenda.")

async def equipar_item_directo(bot: BaseBot, user: User, item_id: str):
    try:
        es_front = "hair_front" in item_id
        es_back = "hair_back" in item_id
        
        outfit_data = await bot.highrise.get_my_outfit()
        outfit = outfit_data.outfit
        
        if es_front:
            outfit = [i for i in outfit if "hair_front" not in i.id]
        elif es_back:
            outfit = [i for i in outfit if "hair_back" not in i.id]
        else:
            categoria_general = item_id.split("-")[0][0:4]
            outfit = [i for i in outfit if i.id.split("-")[0][0:4] != categoria_general]
        
        nuevo_item = Item(type="clothing", amount=1, id=item_id, account_bound=False, active_palette=0)
        outfit.append(nuevo_item)
        
        await bot.highrise.set_outfit(outfit)
        await bot.highrise.send_whisper(user.id, f"✨ ¡Listo! Equipado: {item_id}")
    except Exception as e:
        print(f"Error equipando ítem: {e}")

async def equipar_prenda(bot: BaseBot, user: User, message: str):
    parts = message.split(" ")
    if len(parts) < 2:
        await bot.highrise.send_whisper(user.id, "❌ Uso: !equip [ID]")
        return
    entrada = " ".join(parts[1:]).strip()
    await equipar_item_directo(bot, user, entrada)

async def quitar_prenda(bot: BaseBot, user: User, message: str):
    parts = message.split(" ")
    if len(parts) < 2: return
    objetivo = parts[1].lower()
    
    try:
        outfit_data = await bot.highrise.get_my_outfit()
        outfit = outfit_data.outfit
        
        # --- NUEVO: Si escriben !remove all o !remove todo ---
        if objetivo in ["all", "todo"]:
            # Dejamos únicamente el cuerpo base (para que el bot no desaparezca o crashee)
            nuevo_outfit = [item for item in outfit if "body-" in item.id.lower()]
            await bot.highrise.set_outfit(nuevo_outfit)
            await bot.highrise.send_whisper(user.id, "🧹 ¡Se ha quitado toda la ropa y accesorios!")
            return

        # Lógica normal para quitar categorías específicas
        if objetivo in ["shorts", "pants", "skirt", "piernas"]:
            palabras_clave = ["shorts", "pants", "skirt"]
            nuevo_outfit = [item for item in outfit if not any(pc in item.id.lower() for pc in palabras_clave)]
        else:
            nuevo_outfit = [item for item in outfit if objetivo not in item.id.lower()]
        
        if len(nuevo_outfit) != len(outfit):
            await bot.highrise.set_outfit(nuevo_outfit)
            await bot.highrise.send_whisper(user.id, f"🧥 Se quitó la categoría: {objetivo}")
        else:
            await bot.highrise.send_whisper(user.id, f"❓ No encontré nada puesto con la categoría: {objetivo}")
            
    except Exception as e:
        print(f"Error al quitar: {e}")
        await bot.highrise.send_whisper(user.id, "❌ Hubo un error al quitar la prenda.")

async def cambiar_piel(bot: BaseBot, user: User, message: str):
    parts = message.split(" ")
    if len(parts) != 2: return
    try:
        color_id = int(parts[1])
        outfit = (await bot.highrise.get_my_outfit()).outfit
        body_item = next((item for item in outfit if "body-" in item.id.lower()), None)
        
        if body_item:
            body_item.active_palette = color_id
        else:
            nuevo_cuerpo = Item(type="clothing", amount=1, id="body-m-starteritems2019body", account_bound=False, active_palette=color_id)
            outfit.append(nuevo_cuerpo)
        
        await bot.highrise.set_outfit(outfit)
        await bot.highrise.send_whisper(user.id, f"🎨 Piel: {color_id}")
    except: pass

async def cambiar_color_pelo(bot: BaseBot, user: User, message: str):
    parts = message.split(" ")
    if len(parts) != 2: return
    try:
        color_id = int(parts[1])
        outfit = (await bot.highrise.get_my_outfit()).outfit
        for item in outfit:
            if "hair_front" in item.id.lower() or "hair_back" in item.id.lower():
                item.active_palette = color_id
        await bot.highrise.set_outfit(outfit)
    except: pass

async def cambiar_color_ojos(bot: BaseBot, user: User, message: str):
    parts = message.split(" ")
    if len(parts) != 2: return
    try:
        color_id = int(parts[1])
        outfit = (await bot.highrise.get_my_outfit()).outfit
        for item in outfit:
            if "eye-" in item.id.lower():
                item.active_palette = color_id
        await bot.highrise.set_outfit(outfit)
    except: pass

async def cambiar_color_labios(bot: BaseBot, user: User, message: str):
    parts = message.split(" ")
    if len(parts) != 2: return
    try:
        color_id = int(parts[1])
        outfit = (await bot.highrise.get_my_outfit()).outfit
        for item in outfit:
            if "mouth-" in item.id.lower():
                item.active_palette = color_id
        await bot.highrise.set_outfit(outfit)
    except: pass

async def mostrar_info_outfit(bot: BaseBot, user: User):
    try:
        outfit_data = await bot.highrise.get_my_outfit()
        outfit = outfit_data.outfit
        
        await bot.highrise.send_whisper(user.id, f"👕 El bot lleva {len(outfit)} elementos puestos:")
        for item in outfit:
            await bot.highrise.send_whisper(user.id, f"• {item.id}")
            
    except Exception as e:
        print(f"Error al consultar outfit detallado: {e}")
        await bot.highrise.send_whisper(user.id, "❌ Hubo un error al consultar el outfit del bot.")
        