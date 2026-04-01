import asyncio
from highrise import BaseBot, User, Item
from funciones.moderacion.comandos import obtener_rol

categories = [
    "aura","bag","blush","body","dress","earrings","emote","eye","eyebrow",
    "fishing_rod","freckle","fullsuit","glasses","gloves","hair_back",
    "hair_front","handbag","hat","jacket","lashes","mole","mouth",
    "necklace","nose","rod","shirt","shoes","shorts","skirt","sock","tattoo","watch"
]

async def manejar_ropa(bot: BaseBot, user: User, message: str):
    msg = message.lower()
    
    # --- SEGURIDAD: Solo el Fundador ---
    rol = await obtener_rol(user.id)
    if rol != "fundador":
        return

    if msg.startswith("!equip "):
        await equipar_prenda(bot, user, message)
    elif msg.startswith("!remove "):
        await quitar_prenda(bot, user, message)

    if msg.startswith("!skin "):
        await cambiar_piel(bot, user, message)

    if msg.startswith("!hair "):
        await cambiar_color_pelo(bot, user, message)
    elif msg.startswith("!eye "):
        await cambiar_color_ojos(bot, user, message)

    if msg.startswith("!lips "):
        await cambiar_color_labios(bot, user, message)

async def equipar_prenda(bot: BaseBot, user: User, message: str):
    parts = message.split(" ")
    if len(parts) < 2:
        await bot.highrise.send_whisper(user.id, "❌ Uso: !equip [nombre o ID]")
        return

    entrada = " ".join(parts[1:]).strip()
    
    try:
        # --- 1. Obtener el ID del ítem ---
        if "-" in entrada:
            item_id = entrada # Si escribes el ID completo (ej: hair_back-...)
        else:
            items_encontrados = (await bot.webapi.get_items(item_name=entrada)).items
            if not items_encontrados:
                await bot.highrise.send_whisper(user.id, f"❓ No encontré '{entrada}'.")
                return
            item_id = items_encontrados[0].item_id

        # --- 2. Lógica de Categoría ---
        # Determinamos qué categoría es viendo el inicio del ID
        es_front = "hair_front" in item_id
        es_back = "hair_back" in item_id
        
        # --- 3. Preparar el Outfit ---
        outfit_data = await bot.highrise.get_my_outfit()
        outfit = outfit_data.outfit
        
        # FILTRO INTELIGENTE:
        # Si vas a poner un front, quitamos solo el front viejo.
        # Si vas a poner un back, quitamos solo el back viejo.
        if es_front:
            outfit = [i for i in outfit if "hair_front" not in i.id]
        elif es_back:
            outfit = [i for i in outfit if "hair_back" not in i.id]
        else:
            # Para camisas, pantalones, etc., quitamos la categoría completa
            categoria_general = item_id.split("-")[0][0:4]
            outfit = [i for i in outfit if i.id.split("-")[0][0:4] != categoria_general]
        
        # --- 4. Añadir el ítem seleccionado ---
        nuevo_item = Item(type="clothing", amount=1, id=item_id, account_bound=False, active_palette=0)
        outfit.append(nuevo_item)
        
        # --- 5. Aplicar cambios ---
        asyncio.create_task(bot.highrise.set_outfit(outfit))
        await bot.highrise.send_whisper(user.id, f"✅ Equipado individualmente: {item_id}")
        
    except Exception as e:
        print(f"Error en equipar individual: {e}")

async def quitar_prenda(bot: BaseBot, user: User, message: str):
    parts = message.split(" ")
    if len(parts) != 2: return
    
    # Lo que tú escribas (ej: shorts)
    objetivo = parts[1].lower()
    
    try:
        outfit = (await bot.highrise.get_my_outfit()).outfit
        
        # Guardamos cuántos items había antes
        inicial = len(outfit)
        
        # FILTRO INTELIGENTE:
        if objetivo in ["shorts", "pants", "skirt", "piernas"]:
            palabras_clave = ["shorts", "pants", "skirt", "pants"]
            nuevo_outfit = [item for item in outfit if not any(pc in item.id.lower() for pc in palabras_clave)]
        else:
            # Para otras cosas (hat, hair, etc) seguimos igual
            nuevo_outfit = [item for item in outfit if objetivo not in item.id.lower()]
        
        if len(nuevo_outfit) == inicial:
            await bot.highrise.send_whisper(user.id, f"⚠️ No encontré nada en la categoría '{objetivo}' para quitar.")
        else:
            asyncio.create_task(bot.highrise.set_outfit(nuevo_outfit))
            await bot.highrise.send_whisper(user.id, f"🧥 Se quitó la prenda de las piernas.")
            
    except Exception as e:
        print(f"Error al quitar: {e}")

async def cambiar_piel(bot: BaseBot, user: User, message: str):
    parts = message.split(" ")
    if len(parts) != 2:
        await bot.highrise.send_whisper(user.id, "❌ Uso: !skin [0-95]")
        return
    
    try:
        color_id = int(parts[1])
        outfit_data = await bot.highrise.get_my_outfit()
        outfit = outfit_data.outfit
        
        # Buscamos si ya tiene un objeto 'body'
        body_item = next((item for item in outfit if "body-f" in item.id.lower() or "body-m" in item.id.lower()), None)
        
        if body_item:
            # Si existe, solo le cambiamos el color
            body_item.active_palette = color_id
        else:
            # Si NO existe (esta es la razón por la que no te funcionaba), lo creamos de cero
            # Usamos el cuerpo masculino básico 'body-m-starteritems2019body'
            nuevo_cuerpo = Item(
                type="clothing", 
                amount=1, 
                id="body-m-starteritems2019body", 
                account_bound=False, 
                active_palette=color_id
            )
            outfit.append(nuevo_cuerpo)
        
        # Aplicamos el cambio al instante
        asyncio.create_task(bot.highrise.set_outfit(outfit))
        await bot.highrise.send_whisper(user.id, f"🎨 Piel cambiada al tono: {color_id}")
        
    except ValueError:
        await bot.highrise.send_whisper(user.id, "❌ El ID debe ser un número (ej: !skin 5)")
    except Exception as e:
        print(f"Error crítico en skin: {e}")

async def cambiar_color_pelo(bot: BaseBot, user: User, message: str):
    parts = message.split(" ")
    if len(parts) != 2:
        await bot.highrise.send_whisper(user.id, "❌ Uso: !hair_color [ID 0-100]")
        return
    
    try:
        color_id = int(parts[1])
        outfit_data = await bot.highrise.get_my_outfit()
        outfit = outfit_data.outfit
        
        encontrado = False
        for item in outfit:
            # Cambiamos el color tanto al frente como atrás del pelo
            if "hair_front" in item.id.lower() or "hair_back" in item.id.lower():
                item.active_palette = color_id
                encontrado = True
        
        if encontrado:
            asyncio.create_task(bot.highrise.set_outfit(outfit))
            await bot.highrise.send_whisper(user.id, f"💇‍♂️ Color de cabello cambiado al ID: {color_id}")
        else:
            await bot.highrise.send_whisper(user.id, "⚠️ El bot no tiene cabello equipado.")
            
    except Exception as e:
        print(f"Error en hair_color: {e}")

async def cambiar_color_ojos(bot: BaseBot, user: User, message: str):
    parts = message.split(" ")
    if len(parts) != 2:
        await bot.highrise.send_whisper(user.id, "❌ Uso: !eye_color [ID 0-100]")
        return
    
    try:
        color_id = int(parts[1])
        outfit_data = await bot.highrise.get_my_outfit()
        outfit = outfit_data.outfit
        
        encontrado = False
        for item in outfit:
            if "eye-" in item.id.lower():
                item.active_palette = color_id
                encontrado = True
        
        if encontrado:
            asyncio.create_task(bot.highrise.set_outfit(outfit))
            await bot.highrise.send_whisper(user.id, f"👀 Color de ojos cambiado al ID: {color_id}")
        else:
            # Si no tiene ojos equipados, le ponemos los básicos para poder pintarlos
            ojos_base = Item(type="clothing", amount=1, id="eye-n_basic2018creepyeyes", account_bound=False, active_palette=color_id)
            outfit.append(ojos_base)
            asyncio.create_task(bot.highrise.set_outfit(outfit))
            await bot.highrise.send_whisper(user.id, f"👀 Se equiparon ojos base con el color ID: {color_id}")
            
    except Exception as e:
        print(f"Error en eye_color: {e}")

async def cambiar_color_labios(bot: BaseBot, user: User, message: str):
    parts = message.split(" ")
    if len(parts) != 2:
        await bot.highrise.send_whisper(user.id, "❌ Uso: !lips_color [ID 0-100]")
        return
    
    try:
        color_id = int(parts[1])
        outfit_data = await bot.highrise.get_my_outfit()
        outfit = outfit_data.outfit
        
        encontrado = False
        for item in outfit:
            # Buscamos el ítem de la boca
            if "mouth-" in item.id.lower():
                item.active_palette = color_id
                encontrado = True
        
        if encontrado:
            asyncio.create_task(bot.highrise.set_outfit(outfit))
            await bot.highrise.send_whisper(user.id, f"💄 Color de labios cambiado al ID: {color_id}")
        else:
            # Si no tiene una boca equipada que podamos pintar, le ponemos una base
            boca_base = Item(
                type="clothing", 
                amount=1, 
                id="mouth-n_basic2018pouty", # Una boca estándar que acepta color
                account_bound=False, 
                active_palette=color_id
            )
            outfit.append(boca_base)
            asyncio.create_task(bot.highrise.set_outfit(outfit))
            await bot.highrise.send_whisper(user.id, f"💄 Se equipó una boca base con el color ID: {color_id}")
            
    except Exception as e:
        print(f"Error en lips_color: {e}")