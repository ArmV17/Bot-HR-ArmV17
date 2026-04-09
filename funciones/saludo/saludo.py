from highrise import BaseBot, User

async def manejar_bienvenida(bot: BaseBot, user: User):
    try:
        await bot.highrise.chat(f"🌟 ¡Bienvenid@ {user.username}! 🌟\n(Comandos en mi Biografía)")
        await bot.highrise.react("heart", user.id)
    except Exception as e:
        print(f"⚠️ No se pudo dar la bienvenida completa a {user.username}: {e}")

async def manejar_despedida(bot: BaseBot, user: User):
    """Despide al usuario cuando sale de la sala."""
    try:
        await bot.highrise.chat(f"👋 {user.username}, gracias por acompañarnos.")
    except Exception as e:
        print(f"⚠️ Error al despedir a {user.username}: {e}")