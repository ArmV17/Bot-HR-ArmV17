import asyncio
from highrise import BaseBot, User, Item
from funciones.db import obtener_rol 

categories = [
    "aura","bag","blush","body","dress","earrings","emote","eye","eyebrow",
    "fishing_rod","freckle","fullsuit","glasses","gloves","hair_back",
    "hair_front","handbag","hat","jacket","lashes","mole","mouth",
    "necklace","nose","rod","shirt","shoes","shorts","skirt","sock","tattoo","watch"
]

# Control de los bucles automáticos de color
tarea_color_auto = None
color_auto_activo = False

async def manejar_ropa(bot: BaseBot, user: User, message: str):
    global tarea_color_auto, color_auto_activo
    msg = message.lower().strip()

    # --- SEGURIDAD: Solo el Fundador o Owner ---
    rol = await obtener_rol(user.id)
    if rol not in ["fundador", "owner"]:
        return

    # Comando para detener cualquier bucle automático de color
    if msg in ["stop", "sc"]:
        if color_auto_activo:
            color_auto_activo = False
            if tarea_color_auto and not tarea_color_auto.done():
                tarea_color_auto.cancel()
            await bot.highrise.send_whisper(user.id, "🛑 Prueba automática de color detenida.")
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

        if objetivo in ["all", "todo"]:
            nuevo_outfit = [item for item in outfit if "body-" in item.id.lower()]
            await bot.highrise.set_outfit(nuevo_outfit)
            await bot.highrise.send_whisper(user.id, "🧹 ¡Se ha quitado toda la ropa y accesorios!")
            return

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

# --- LÓGICA GENERAL PARA BUCLES O CAMBIOS MANUALES DE COLOR ---
async def procesar_comando_color(bot: BaseBot, user: User, message: str, tipo: str):
    global tarea_color_auto, color_auto_activo
    parts = message.split(" ")
    if len(parts) < 2: return

    inicio = 0
    fin = 90
    es_bucle = False

    if len(parts) == 2:
        param = parts[1].lower().strip()
        if param in ["auto", "loop"]:
            es_bucle = True
        elif param.isdigit():
            await aplicar_palette(bot, user, tipo, int(param))
            return
    elif len(parts) == 3:
        if parts[1].isdigit() and parts[2].isdigit():
            inicio = int(parts[1])
            fin = int(parts[2])
            es_bucle = True

    if es_bucle:
        if color_auto_activo:
            await bot.highrise.send_whisper(user.id, "⚠️ Ya hay una prueba de color activa. Usa 'stop' o 'sc' para detenerla.")
            return

        color_auto_activo = True
        nombres_tipo = {"skin": "piel", "hair": "cabello", "eye": "ojos", "lips": "labios"}
        etiqueta = nombres_tipo.get(tipo, tipo)

        await bot.highrise.send_whisper(user.id, f"🔄 Probando colores de {etiqueta} del {inicio} al {fin}. Escribe 'stop' o 'sc' para detener.")

        async def bucle_colores():
            global color_auto_activo
            for color_id in range(inicio, fin + 1):
                if not color_auto_activo:
                    break

                await aplicar_palette(bot, user, tipo, color_id)
                await asyncio.sleep(2)

            color_auto_activo = False

        tarea_color_auto = asyncio.create_task(bucle_colores())

async def aplicar_palette(bot: BaseBot, user: User, tipo: str, color_id: int):
    try:
        outfit = (await bot.highrise.get_my_outfit()).outfit

        if tipo == "skin":
            body_item = next((item for item in outfit if "body-" in item.id.lower()), None)
            if body_item:
                body_item.active_palette = color_id
            else:
                nuevo_cuerpo = Item(type="clothing", amount=1, id="body-m-starteritems2019body", account_bound=False, active_palette=color_id)
                outfit.append(nuevo_cuerpo)
            texto = f"🎨 Piel actual: {color_id}"

        elif tipo == "hair":
            for item in outfit:
                if "hair_front" in item.id.lower() or "hair_back" in item.id.lower():
                    item.active_palette = color_id
            texto = f"💇‍♂️ Cabello actual: {color_id}"

        elif tipo == "eye":
            for item in outfit:
                if "eye-" in item.id.lower():
                    item.active_palette = color_id
            texto = f"👁️ Ojos actuales: {color_id}"

        elif tipo == "lips":
            for item in outfit:
                if "mouth-" in item.id.lower():
                    item.active_palette = color_id
            texto = f"💋 Labios actuales: {color_id}"

        await bot.highrise.set_outfit(outfit)
        await bot.highrise.send_whisper(user.id, texto)
    except Exception as e:
        print(f"Error aplicando color {tipo} ({color_id}): {e}")

# --- COMANDOS ESPECÍFICOS ---
async def cambiar_piel(bot: BaseBot, user: User, message: str):
    await procesar_comando_color(bot, user, message, "skin")

async def cambiar_color_pelo(bot: BaseBot, user: User, message: str):
    await procesar_comando_color(bot, user, message, "hair")

async def cambiar_color_ojos(bot: BaseBot, user: User, message: str):
    await procesar_comando_color(bot, user, message, "eye")

async def cambiar_color_labios(bot: BaseBot, user: User, message: str):
    await procesar_comando_color(bot, user, message, "lips")

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
