import discord
import json
import re

from discord.utils import get
from discord.ext import commands

with open('./config.json', 'r') as cjson:
    config = json.load(cjson)

class Generate(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.tanks = []
        self.healers = []
        self.dps = []

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if self.client.user == user:
            return

        if str(reaction.emoji) == '<:tank:714930608266018859>':
            print("tank")
            self.tanks.append(user)

        if str(reaction.emoji) == '<:healer:714930600267612181>':
            print("healer")
            self.healers.append(user)

        if str(reaction.emoji) == '<:dps:714930578461425724>':
            print("dps")
            self.dps.append(user)

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        if self.client.user == user:
            return

        if str(reaction.emoji) == '<:tank:714930608266018859>':
            self.tanks.remove(user)

        if str(reaction.emoji) == '<:healer:714930600267612181>':
            self.healers.remove(user)

        if str(reaction.emoji) == '<:dps:714930578461425724>':
            self.dps.remove(user)

    @commands.command()
    async def generate(self, ctx):
        msg = ctx.message.content[10:]
        result = [x.strip() for x in re.split(' ', msg)]

        count = 5
        advertiserNote = ""
        for x in range(5, len(result)):
            advertiserNote += result[count] + " "
            count += 1

        # change numbers
        if len(result) == 5 or len(result) > 6:
            embed=discord.Embed(title=f"Generating Mythic {result[1]} run!", description="Click on the reaction below the post with your assigned roles for a chance to join the group.", color=0x5cf033)
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/632628531528073249/644669381451710495/TwilightDiscIocn.jpg")
            embed.add_field(name="Faction", value=result[0], inline=False)
            embed.add_field(name="Keystone Level", value=result[1], inline=False)
            embed.add_field(name="Gold Pot", value=result[2], inline=False)
            embed.add_field(name="Dungeon", value=result[3], inline=False)
            embed.add_field(name="Armor Type", value=result[4], inline=False)

            if advertiserNote:
                embed.add_field(name="Advertiser Note", value=advertiserNote, inline=False)
            
            group = await ctx.message.channel.send(embed=embed)

            # Tank
            await group.add_reaction(self.client.get_emoji(714930608266018859))

            # Healer
            await group.add_reaction(self.client.get_emoji(714930600267612181))

            # DPS
            await group.add_reaction(self.client.get_emoji(714930578461425724))

def setup(client):
    client.add_cog(Generate(client))
