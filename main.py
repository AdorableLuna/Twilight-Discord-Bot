import os
import json

from discord.ext import commands
from gsheet import *

description = """
The Twilight bot that helps advertisers, boosters and management do their job.
"""

class Twilight(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix = '.', description = description)
        self.config = self.__load_config()
        self.sheet = gsheet()
        self.__load_all_extensions()

    def __load_all_extensions(self):
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    self.load_extension(f'cogs.{filename[:-3]}')
                except Exception as e:
                    print(f'Failed to load extension {filename[:-3]}.')

    def __load_config(self):
        with open('./config.json', 'r') as cjson:
            config = json.load(cjson)

        return config

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')

    async def on_message(self, message):
        if message.author.bot:
            return

        await self.process_commands(message)

    async def close(self):
        await super().close()

    def run(self, client):
        super().run(self.config["TOKEN"], reconnect = True)

client = Twilight()
client.run(client)
