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

    if msg.startswith("!equip "):
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

async def equipar_prenda(bot: BaseBot, user: User, message: str):
    parts = message.split(" ")
    if len(parts) < 2:
        await bot.highrise.send_whisper(user.id, "❌ Uso: !equip [nombre o ID]")
        return

    entrada = " ".join(parts[1:]).strip()
    
    try:
        # 1. Obtener el ID del ítem
        if "-" in entrada:
            item_id = entrada 
        else:
            items_encontrados = (await bot.webapi.get_items(item_name=entrada)).items
            if not items_encontrados:
                await bot.highrise.send_whisper(user.id, f"❓ No encontré '{entrada}'.")
                return
            item_id = items_encontrados[0].item_id

        # 2. Lógica de Categoría
        es_front = "hair_front" in item_id
        es_back = "hair_back" in item_id
        
        outfit_data = await bot.highrise.get_my_outfit()
        outfit = outfit_data.outfit
        
        # Filtro para no encimar ropa
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
        await bot.highrise.send_whisper(user.id, f"✅ Equipado: {item_id}")
        
    except Exception as e:
        print(f"Error en equipar: {e}")

async def quitar_prenda(bot: BaseBot, user: User, message: str):
    parts = message.split(" ")
    if len(parts) != 2: return
    objetivo = parts[1].lower()
    
    try:
        outfit = (await bot.highrise.get_my_outfit()).outfit
        inicial = len(outfit)
        
        if objetivo in ["shorts", "pants", "skirt", "piernas"]:
            palabras_clave = ["shorts", "pants", "skirt"]
            nuevo_outfit = [item for item in outfit if not any(pc in item.id.lower() for pc in palabras_clave)]
        else:
            nuevo_outfit = [item for item in outfit if objetivo not in item.id.lower()]
        
        if len(nuevo_outfit) != inicial:
            await bot.highrise.set_outfit(nuevo_outfit)
            await bot.highrise.send_whisper(user.id, f"🧥 Se quitó la categoría: {objetivo}")
    except Exception as e:
        print(f"Error al quitar: {e}")

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