import datetime
import signal
import sys

import nextcord
from nextcord.ext import commands
# from discord_ui import UI

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

    # ui = UI(bot)

    bot.add_cog(Core(bot))
    bot.add_cog(Utility(bot, settings.ADMINS))
    bot.add_cog(Games(bot))
    bot.add_cog(Roles(bot))

    @bot.event
    async def on_ready():
        logger.info(f"\nLogged in as:\n{bot.user} (ID: {bot.user.id})")

    async def on_application_command_error(interaction: nextcord.Interaction,
                                           exception: Exception):
        """
        Handle error in Application commands
        :param interaction: Interaction
        :param exception: Exception
        :return:
        """
        # sys.stderr.write(str(exception.with_traceback(sys.exc_info()[2])))
        embed = nextcord.Embed()
        embed.set_author(
            name=bot.user.name,
            url=settings.URL,
            icon_url=bot.user.avatar.url,
        )
        embed.title = "Error running the command!"
        embed.description = f"{exception}"
        embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
        embed.colour = nextcord.Colour.red()
        await interaction.send(embed=embed, ephemeral=True)

    # Replace with a new command error handler
    bot.on_application_command_error = on_application_command_error

    def handle_sigterm(sig, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, handle_sigterm)

    bot.run(settings.BOT_TOKEN)


if __name__ == '__main__':
    main()
