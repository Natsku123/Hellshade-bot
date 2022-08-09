import signal
import nextcord
from nextcord.ext import commands
#from discord_ui import UI

from core.cogs.core import Core
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
    intents = nextcord.Intents.all()

    bot = commands.Bot(
        command_prefix=commands.when_mentioned_or('!', '?'),
        description=description,
        owner_id=settings.BOT_OWNER,
        intents=intents
    )

    #ui = UI(bot)

    bot.add_cog(Core(bot))
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
