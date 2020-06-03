import discord
import json
import re
import asyncio
import datetime
import time
import itertools

from discord.utils import get
from discord.ext import commands

from .lib import config

with open('./config.json', 'r') as cjson:
    botConfig = json.load(cjson)

class Generate(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.config = config.Config('mythicplus.json')
        self.duration = datetime.timedelta(seconds=20)

    @commands.Cog.listener()
    async def on_ready(self):
        self.guild = self.client.get_guild(botConfig["GUILD_ID"])
        self.tankEmoji = self.client.get_emoji(714930608266018859)
        self.healerEmoji = self.client.get_emoji(714930600267612181)
        self.dpsEmoji = self.client.get_emoji(714930578461425724)
        self.keystoneEmoji = self.client.get_emoji(715918950092898346)
        self.teamEmoji = "\U0001F1F9"
        self.cancelEmoji = "\U0000274C"
        self.doneEmoji = "\U00002705"

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if self.client.user == user: return

        if str(reaction.emoji) == str(self.teamEmoji):
            embed = reaction.message.embeds[0]
            keystone = re.findall(r'\d+', embed.title)[0]
            faction = embed.fields[0].value
            armor = embed.fields[5].value

            # If the group was already edited (team), then return
            if "created" in embed.footer.text: return

            if armor != "Any":
                armor = re.sub('[<@&>]', '', armor)
                if int(armor) not in [y.id for y in user.roles]: return
            if not self.checkRoles(user, faction, "Any", keystone): return

            tank = healer = user
            dps = [user, user]
            keystoneHolder = user
            group = [tank, healer, dps]

            await self.createGroup(reaction.message, group, keystone, keystoneHolder)

        if str(reaction.emoji) == str(self.cancelEmoji):
            author = reaction.message.embeds[0].fields[6].value
            author = author.split(" ", 1)[0]

            if user.mention == author:
                await reaction.message.delete()

    @commands.command()
    async def generate(self, ctx):
        msg = ctx.message.content[10:]
        duration = ctx.message.created_at + self.duration
        countdown = float(duration.timestamp()) - datetime.datetime.utcnow().timestamp()
        countdown = time.strftime('%H:%M:%S', time.gmtime(countdown))
        result = [x.strip() for x in re.split(' ', msg)]

        count = 7
        advertiserNote = ""
        for x in range(7, len(result)):
            advertiserNote += result[count] + " "
            count += 1

        # TODO: change numbers
        if len(result) >= 7:
            keystone = result[3]
            mentions = ""

            if int(keystone) >= 15:
                if result[2] == "Horde":
                    keystoneRole = self.getRole("Highkey Booster Horde").mention
                elif result[2] == "Alliance":
                    keystoneRole = self.getRole("Highkey Booster Alliance").mention
                mentions += keystoneRole + " "
            elif int(keystone) >= 10 and int(keystone) <= 14:
                keystoneRole = self.getRole("Mplus Booster").mention
                mentions += keystoneRole + " "

            tankRole = self.getRole("Tank").mention
            healerRole = self.getRole("Healer").mention
            damageRole = self.getRole("Damage").mention
            mentions += tankRole + " " + healerRole + " " + damageRole + " "

            if(result[6] != "Any"):
                armor = self.getRole(result[6]).mention
                mentions += armor
            else:
                armor = "Any"

            embed = discord.Embed(title=f"Generating Mythic +{result[3]} run!", description="Click on the reaction below the post with your assigned roles to join the group. First come first serve.\n" +
                                f"The group will be created within {countdown}.", color=0x5cf033)
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/632628531528073249/644669381451710495/TwilightDiscIocn.jpg")
            embed.add_field(name="Faction", value=result[2], inline=True)
            embed.add_field(name="Payment Realm", value=result[1], inline=True)
            embed.add_field(name="Gold Pot", value=result[4], inline=True)
            embed.add_field(name="Keystone Level", value=result[3], inline=True)
            embed.add_field(name="Dungeon", value=result[5], inline=True)
            embed.add_field(name="Armor Type", value=armor, inline=True)
            embed.add_field(name="Advertiser", value=f"{ctx.message.author.mention} ({result[0]})")

            if advertiserNote:
                embed.add_field(name="Advertiser Note", value=advertiserNote, inline=False)

            msg = await ctx.message.channel.send(content=mentions, embed=embed)

            # Tank
            await msg.add_reaction(self.tankEmoji)

            # Healer
            await msg.add_reaction(self.healerEmoji)

            # DPS
            await msg.add_reaction(self.dpsEmoji)

            # Keystones
            await msg.add_reaction(self.keystoneEmoji)

            # Team
            await msg.add_reaction(self.teamEmoji)

            # Cancel
            await msg.add_reaction(self.cancelEmoji)

            # Done - TODO: Add logic
            await msg.add_reaction(self.doneEmoji)

            await self.config.put(duration.timestamp(), msg.id)

            embed.set_footer(text=f"Group id: {msg.id}.")

            msg = await msg.edit(embed=embed)

            await self.prepareGroup(ctx.message.channel, result[2], result[6], keystone)

        else:
            # Needs more/less fields
            await ctx.message.channel.send(':x: The command you have entered is invalid. Please check the correct formatting in the pins. :x:', delete_after=10.0)

    async def prepareGroup(self, channel, faction, armor, keystone):
        # channels / emoji aren't loaded before being ready
        await self.client.wait_until_ready()

        while self.config:
            oldest = min(self.config.all())
            message_id = self.config.get(oldest)
            await self.config.remove(oldest)

            timeToSleep = float(oldest) - datetime.datetime.utcnow().timestamp()
            await asyncio.sleep(timeToSleep)

            try:
                message = await channel.fetch_message(message_id)

                # If the group was already edited (team), then return
                if ("created" in message.embeds[0].footer.text): return

                tanksEmoji = self.getEmoji(message, self.tankEmoji)
                healersEmoji = self.getEmoji(message, self.healerEmoji)
                dpsEmoji = self.getEmoji(message, self.dpsEmoji)
                keystoneEmoji = self.getEmoji(message, self.keystoneEmoji)

                tanks = await self.getReactedUsers(tanksEmoji, faction, armor, keystone, "Tank")
                healers = await self.getReactedUsers(healersEmoji, faction, armor, keystone, "Healer")
                dps = await self.getReactedUsers(dpsEmoji, faction, armor, keystone, "Damage")

                keystones = await self.getReactedUsers(keystoneEmoji, faction, armor, keystone)

                tankHasKey = False
                healerHasKey = False
                dpsOneHasKey = False
                dpsTwoHasKey = False

                try:
                    for user in tanks:
                        if user in keystones and not tankHasKey:
                            tanks.remove(user)
                            tanks.insert(0, user)
                            tankHasKey = True

                    tank = tanks[0]

                    # remove for testing
                    if tank in healers:
                        healers.remove(tank)
                    if tank in dps:
                        dps.remove(tank)
                except:
                    await channel.send(f':x: There is not a tank (that meets the criteria) to fill the group. Group id: {message_id} :x:', delete_after=15.0)
                    return

                try:
                    for user in healers:
                        if user in keystones and not healerHasKey:
                            healers.remove(user)
                            healers.insert(0, user)
                            healerHasKey = True

                    healer = healers[0]

                    # remove for testing
                    if healer in tank:
                        tank.remove(healer)
                    if healer in dps:
                        dps.remove(healer)
                except:
                    await channel.send(f':x: There is not a healer (that meets the criteria) to fill the group. Group id: {message_id} :x:', delete_after=15.0)
                    return

                for user in dps:
                    if user in keystones:
                        if not dpsOneHasKey:
                            dps.remove(user)
                            dps.insert(0, user)
                            dpsOneHasKey = True
                        if not dpsTwoHasKey:
                            dps.remove(user)
                            dps.insert(1, user)
                            dpsTwoHasKey = True

                dps = list(itertools.islice(dps, 0, 2))
                if len(dps) != 2:
                    await channel.send(f':x: There are not enough DPS (that meet the criteria) to fill the group. Group id: {message_id} :x:', delete_after=15.0)
                    # return

                group = [tank, healer, dps]

                if dpsTwoHasKey:
                    keystoneHolder = dps[0] # TODO: change to [1]
                elif dpsOneHasKey:
                    keystoneHolder = dps[0]
                elif healerHasKey:
                    keystoneHolder = healer
                elif tankHasKey:
                    keystoneHolder = tank
                else:
                    await channel.send(f':x: There is no one who has the specific key to complete this run. Group id: {message_id} :x:', delete_after=15.0)
                    return

                await self.createGroup(message, group, keystone, keystoneHolder)

            except discord.NotFound:
                # Incase the message was deleted by someone, then skip
                continue

    async def createGroup(self, msg, group, keystone, keystoneHolder):
        tank = group[0]
        healer = group[1]
        dps = group[2]

        embed = msg.embeds[0]

        advertiser = re.findall('\(([^)]+)', embed.fields[6].value)[0]

        embed.title = f"Generated Mythic +{keystone} Group"
        embed.description = (f"{self.tankEmoji} {tank.mention}\n{self.healerEmoji} {healer.mention}\n{self.dpsEmoji} {tank.mention}\n{self.dpsEmoji} {healer.mention}\n{self.keystoneEmoji} {keystoneHolder.mention}\n\n" +
                             f"Please whisper `/w {advertiser} invite`")
        embed.set_footer(text=f"{embed.footer.text} Group created at: {datetime.datetime.now().strftime('%H:%M:%S')}")
        editedmsg = await msg.edit(embed=embed)

        # Mention the group members - TODO: add dps
        message = (f"{self.tankEmoji} {tank.mention} {self.healerEmoji} {healer.mention} {self.dpsEmoji} {tank.mention} {self.dpsEmoji} {healer.mention}\n" +
                  f"Please whisper `/w {advertiser} invite`. See the message above for more details.\n" +
                  f"Group id: {msg.id}")
        await msg.channel.send(message)

    def checkRoles(self, user, faction, armor, keystone, role = "Any"):
        isValid = False

        if int(keystone) >= 15:
            if faction == "Horde":
                factionRole = self.getRole("Highkey Booster Horde")
            elif faction == "Alliance":
                factionRole = self.getRole("Highkey Booster Alliance")
        else:
            factionRole = self.getRole("Mplus Booster")

        if int(keystone) >= 18:
            keystoneRole = self.getRole("Legendary")
        if int(keystone) <= 17:
            keystoneRole = self.getRole("Epic")
        if int(keystone) <= 14:
            keystoneRole = self.getRole("Rare")

        userRoles = user.roles

        if factionRole in userRoles:
            isValid = True
        else:
            return False

        if keystoneRole in userRoles:
            isValid = True
        else:
            return False

        if role != "Any":
            role = self.getRole(role)
            if role in userRoles:
                isValid = True
            else:
                return False

        if armor != "Any":
            armorRole = self.getRole(armor)

            if armorRole in userRoles:
                isValid = True
            else:
                return False

        return isValid

    def getRole(self, role):
        return discord.utils.find(lambda r: r.name == role, self.guild.roles)

    def getEmoji(self, message, targetEmoji):
        return next(x for x in message.reactions if getattr(x.emoji, 'id', None) == targetEmoji.id)

    async def getReactedUsers(self, targetEmoji, faction, armor, keystone, role = "Any"):
        return await targetEmoji.users().filter(lambda user: not user.bot and self.checkRoles(user, faction, armor, keystone, role)).flatten()

def setup(client):
    client.add_cog(Generate(client))
