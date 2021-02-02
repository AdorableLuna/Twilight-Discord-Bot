import discord
import logging
import os
import json

from discord.ext import commands
from gsheet import *

log = logging.getLogger('discord')
log.setLevel(logging.ERROR)
handler = logging.FileHandler(filename='logs/discord.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', '%Y-%m-%d %H:%M:%S'))
log.addHandler(handler)

description = """
The Twilight bot that helps advertisers, boosters and management do their job.
"""

intents = discord.Intents.default()
intents.members = True

class Twilight(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix = '.', description = description,
                         intents=intents, activity=discord.Game(name="World of Warcraft"))
        self.config = self.__load_config()
        self.sheet = gsheet()
        self.__load_all_extensions()

    def __load_all_extensions(self):
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    self.load_extension(f'cogs.{filename[:-3]}')
                except Exception as e:
                    print(f'Failed to load extension {filename[:-3]}.', e)

    def __load_config(self):
        with open('./config.json', 'r') as cjson:
            config = json.load(cjson)

        return config

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.CommandInvokeError):
            if isinstance(error.original, discord.Forbidden):
                await ctx.send(f'{ctx.author.mention}, the message could not be delivered. This is usually because of a setting regarding direct messages. Please check the following Discord support link for more support.\n https://support.discord.com/hc/en-us/articles/360060145013')
                log.error(f"Command: {ctx.command.name} | {error}")
                return

        await ctx.send(f'{ctx.author.mention}, there was an error with your command. Please check if your command has the correct format, otherwise notify the staff.')
        log.error(f"Command: {ctx.command.name} | {error}")

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
