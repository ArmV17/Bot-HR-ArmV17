from highrise import BaseBot, User, Position

async def manejar_bienvenida(bot: BaseBot, user: User):
    """Saluda al usuario y lanza una reacción de corazón"""
    # El mensaje que pediste
    await bot.highrise.chat(f"🌟 ¡Bienvenid@ {user.username}! 🌟\n(Comandos en mi Biografía)")
    # Reacción de corazón
    await bot.highrise.react("heart", user.id)

async def manejar_despedida(bot: BaseBot, user: User):
    """Despide al usuario cuando sale de la sala"""
    await bot.highrise.chat(f"👋 {user.username}, gracias por acompañarnos.")