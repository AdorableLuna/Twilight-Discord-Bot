import os
import json

from discord.ext import commands

with open('./config.json', 'r') as cjson:
    config = json.load(cjson)

client = commands.Bot(command_prefix = '.')

@client.event
async def on_ready():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            client.load_extension(f'cogs.{filename[:-3]}')
            
    print(f'{client.user} has connected to Discord!')

client.run(config["TOKEN"])
