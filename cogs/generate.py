import discord
import json
import re
import asyncio

from collections import deque
import itertools

from discord.utils import get
from discord.ext import commands

with open('./config.json', 'r') as cjson:
    config = json.load(cjson)

class Generate(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.tanks = deque()
        self.healers = deque()
        self.dps = deque()

        self.tankHasKey = False
        self.healerHasKey = False
        self.dpsOneHasKey = False
        self.dpsTwoHasKey = False

    @commands.Cog.listener()
    async def on_ready(self):
        self.tankEmoji = self.client.get_emoji(714930608266018859)
        self.healerEmoji = self.client.get_emoji(714930600267612181)
        self.dpsEmoji = self.client.get_emoji(714930578461425724)
        self.keystoneEmoji = self.client.get_emoji(715918950092898346)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if not checkRoles(self, user, reaction.emoji):
            return

        if self.client.user == user:
            return

        if str(reaction.emoji) == str(self.tankEmoji):
            self.tanks.append(user)

        if str(reaction.emoji) == str(self.healerEmoji):
            self.healers.append(user)

        if str(reaction.emoji) == str(self.dpsEmoji):
            self.dps.append(user)

        if str(reaction.emoji) == str(self.keystoneEmoji):
            if not self.tankHasKey and user in self.tanks:
                self.tanks.appendleft(user)
                self.tankHasKey = True

            if not self.healerHasKey and user in self.healers:
                self.healers.appendleft(user)
                self.healerHasKey = True

            if user in self.dps:
                if not self.dpsOneHasKey:
                    self.dps.appendleft(user)
                    self.dpsOneHasKey = True
                if not self.dpsTwoHasKey:
                    self.dps.appendleft(user)
                    self.dpsTwoHasKey = True

        if str(reaction.emoji) == str("\U0001F1F9"):
            self.waitTimer.cancel()
            self.team = user

        if str(reaction.emoji) == str("\U0000274C"):
            if user == self.author:
                self.cancelled = True
                self.waitTimer.cancel()
                await self.msg.delete()

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        if self.client.user == user:
            return

        if str(reaction.emoji) == str(self.tankEmoji):
            self.tanks.remove(user)

        if str(reaction.emoji) == str(self.healerEmoji):
            self.healers.remove(user)

        if str(reaction.emoji) == str(self.dpsEmoji):
            self.dps.remove(user)

    @commands.command()
    async def generate(self, ctx):
        # Clear the lists - TODO: Move to own function
        self.tanks.clear()
        self.healers.clear()
        self.dps.clear()
        self.team = ""
        self.author = ctx.message.author
        self.cancelled = False
        self.tankHasKey = False
        self.healerHasKey = False
        self.dpsOneHasKey = False
        self.dpsTwoHasKey = False

        msg = ctx.message.content[10:]
        result = [x.strip() for x in re.split(' ', msg)]

        count = 6
        advertiserNote = ""
        for x in range(6, len(result)):
            advertiserNote += result[count] + " "
            count += 1

        # TODO: change numbers
        if len(result) >= 6:
            self.keystone = result[2]
            self.armor = result[5]

            embed = discord.Embed(title=f"Generating Mythic +{result[2]} run!", description="Click on the reaction below the post with your assigned roles to join the group. First come first serve.\n" +
                                "The group will be determined in x minutes.", color=0x5cf033)
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/632628531528073249/644669381451710495/TwilightDiscIocn.jpg")
            embed.add_field(name="Faction", value=result[1], inline=True)
            embed.add_field(name="Payment Realm", value=result[0], inline=True)
            embed.add_field(name="Gold Pot", value=result[3], inline=True)
            embed.add_field(name="Keystone Level", value=result[2], inline=True)
            embed.add_field(name="Dungeon", value=result[4], inline=True)
            embed.add_field(name="Armor Type", value=result[5], inline=True)

            if advertiserNote:
                embed.add_field(name="Advertiser Note", value=advertiserNote, inline=False)

            self.msg = await ctx.message.channel.send(embed=embed)

            # Tank
            await self.msg.add_reaction(self.tankEmoji)

            # Healer
            await self.msg.add_reaction(self.healerEmoji)

            # DPS
            await self.msg.add_reaction(self.dpsEmoji)

            # Keystone
            await self.msg.add_reaction(self.keystoneEmoji)

            # Team
            await self.msg.add_reaction("\U0001F1F9")

            # Cancel
            await self.msg.add_reaction("\U0000274C")

            # Done - TODO: Add logic
            await self.msg.add_reaction("\U00002705")

            # TODO: change timer duration
            self.waitTimer = asyncio.create_task(asyncio.sleep(10))
            try:
                await self.waitTimer
            except asyncio.CancelledError:
                if self.cancelled:
                    return
                else:
                    pass

            await createGroup(self, ctx, self.msg, embed, result[2])

        else:
            # Needs more/less fields
            await ctx.message.channel.send(':x: The command you have entered is invalid. Please check the correct formatting in the pins. :x:', delete_after=10.0)

def checkRoles(self, user, emoji):
    guild = self.client.get_guild(config["GUILD_ID"])
    isValid = False

    if int(self.keystone) >= 18:
        keystoneRole = discord.utils.find(lambda r: r.name == 'Legendary', guild.roles)
    if int(self.keystone) <= 17:
        keystoneRole = discord.utils.find(lambda r: r.name == 'Epic', guild.roles)
    if int(self.keystone) <= 14:
        keystoneRole = discord.utils.find(lambda r: r.name == 'Rare', guild.roles)

    userRoles = user.roles

    if keystoneRole in userRoles:
        isValid = True

    if self.armor != "Any":
        armorRole = discord.utils.find(lambda r: r.name == self.armor, guild.roles)

        if armorRole in userRoles:
            isValid = True
        else:
            isValid = False

    if str(emoji) == str("\U0001F1F9"):
        teamRole = discord.utils.find(lambda r: r.name == 'Mythic+ Team', guild.roles)
        if teamRole in userRoles:
            isValid = True
        else:
            isValid = False

    return isValid

async def createGroup(self, ctx, msg, embed, keystone):
    if self.team:
        tank = healer = self.team
        dps = [self.team, self.team]
        keystoneHolder = self.team
    else:
        try:
            tank = self.tanks[0]
        except:
            await ctx.message.channel.send(':x: There is not a tank (that meets the criteria) to fill the group. :x:', delete_after=15.0)
            return

        try:
            healer = self.healers[0]
        except:
            await ctx.message.channel.send(':x: There is not a healer (that meets the criteria) to fill the group. :x:', delete_after=15.0)
            return

        dps = list(itertools.islice(self.dps, 0, 2))
        if len(dps) != 2:
            await ctx.message.channel.send(':x: There are not enough DPS (that meet the criteria) to fill the group. :x:', delete_after=15.0)
            # return

    if not self.team and not self.dpsTwoHasKey and not self.dpsOneHasKey and not self.healerHasKey and not self.tankHasKey:
        await ctx.message.channel.send(':x: There is no one who has the specific key to complete this run. :x:', delete_after=15.0)
        return

    if self.dpsTwoHasKey:
        keystoneHolder = dps[1]
    if self.dpsOneHasKey:
        keystoneHolder = dps[0]
    if self.healerHasKey:
        keystoneHolder = healer
    if self.tankHasKey:
        keystoneHolder = tank

    # Mention the group members - TODO: Change to dps
    tank.mention
    healer.mention
    tank.mention
    healer.mention

                        #change to dps[0]    change to dps[1]
    # group = discord.Embed(title="Mythic+ group made!", description=
    #                     f"{self.tankEmoji} {tank.mention}\n" +
    #                     f"{self.healerEmoji} {healer.mention}\n" +
    #                     f"{self.dpsEmoji} {tank.mention}\n" +
    #                     f"{self.dpsEmoji} {healer.mention}\n\n" +
    #                     "You are in this boosting run.\nSee this bot's post above for the details.", color=0x5cf033)

    embed.title = f"Mythic +{keystone} Group"
    embed.description = f"{self.tankEmoji} {tank.mention}\n{self.healerEmoji} {healer.mention}\n{self.dpsEmoji} {tank.mention}\n{self.dpsEmoji} {healer.mention}"
    embed.add_field(name="Keystone Holder", value=keystoneHolder.mention, inline=True)

    await msg.edit(embed=embed)
    # await ctx.message.channel.send(embed=group)

def setup(client):
    client.add_cog(Generate(client))
