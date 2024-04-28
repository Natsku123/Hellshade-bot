from nextcord.ext import commands, tasks
from datetime import datetime

from core.database.utils import get_create
from core.database import Session, session_lock
from core.database.crud.servers import server as crud_server
from core.database.schemas.servers import CreateServer, UpdateServer

from core.config import logger


class Core(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot

        self.heartbeat.start()

    @tasks.loop(hours=1)
    async def heartbeat(self):
        await self.__bot.wait_until_ready()
        logger.info("Heartbeat.")

        async with session_lock:
            with Session() as session:
                for guild in self.__bot.guilds:
                    server = get_create(
                        session, crud_server, obj_in=CreateServer(**{
                            "discord_id": str(guild.id),
                            "name": guild.name,
                            "server_exp": 0,
                            "channel": None
                        })
                    )

                    # Update last seen
                    now = datetime.now()

                    crud_server.update(
                        session, db_obj=server, obj_in=UpdateServer(**{
                            "last_seen": now
                        })
                    )
