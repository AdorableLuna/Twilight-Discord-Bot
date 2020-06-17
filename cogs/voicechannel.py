import discord
import json

from discord import ChannelType
from discord.utils import get
from discord.ext import commands

with open('./config.json', 'r') as cjson:
    config = json.load(cjson)

class Voicechannel(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        self.guild = self.client.get_guild(config["GUILD_ID"])

    @commands.command(aliases=['vc'])
    async def voicechannel(self, ctx):
        channels = (c for c in self.guild.channels if c.type==ChannelType.voice)
        for channel in channels:
            if len(channel.members) == 0:
                link = await channel.create_invite(max_age = 300)
                msg = f"One empty voice channel as requested: **{channel.name}**\n{link}"
                await ctx.message.channel.send(msg)
                return

def setup(client):
    client.add_cog(Voicechannel(client))
