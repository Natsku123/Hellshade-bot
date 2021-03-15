import signal
import discord
from discord.ext import commands

from core.cogs.games import Games
from core.cogs.utility import Utility
from core.cogs.roles import Roles

from core.config import settings, logger


def main():

    logger.info("Starting Bot...")

    description = '''
    Rewrite of the original Hellshade-bot and Hellshade-bot 2
    '''

    # Intents for experience tracking etc.
    intents = discord.Intents.all()

    bot = commands.Bot(
        command_prefix=commands.when_mentioned_or('!', '/'),
        description=description,
        owner_id=settings.BOT_OWNER,
        intents=intents
    )

    bot.add_cog(Utility(bot, settings.ADMINS))
    bot.add_cog(Games(bot))
    bot.add_cog(Roles(bot))

    @bot.event
    async def on_ready():
        logger.info(f"\nLogged in as:\n{bot.user} (ID: {bot.user.id})")

    def handle_sigterm(sig, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, handle_sigterm)

    bot.run(settings.BOT_TOKEN)


if __name__ == '__main__':
    main()
