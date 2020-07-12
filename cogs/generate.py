import discord
import json
import re
import asyncio
import datetime
import time
import itertools
import math
import locale

from discord.utils import get
from discord.ext import commands
from db import dbconnection as dbc

locale.setlocale(locale.LC_ALL, '')

with open('./config.json', 'r') as cjson:
    config = json.load(cjson)

class Generate(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.dbc = dbc.DBConnection()
        self.tankRoles = [
            "Druid",
            "Monk",
            "Demon Hunter",
            "Paladin",
            "Warrior",
            "Death Knight",
            "Leather",
            "Plate"
        ]
        self.healerRoles = [
            "Druid",
            "Monk",
            "Paladin",
            "Priest",
            "Shaman",
            "Cloth",
            "Leather",
            "Mail",
            "Plate"
        ]

    @commands.Cog.listener()
    async def on_ready(self):
        self.guild = self.client.get_guild(config["GUILD_ID"])
        self.completedChannel = self.client.get_channel(731479403862949928)
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
        if "boosts" not in reaction.message.channel.name: return
        if not reaction.message.embeds: return

        id = reaction.message.id
        channel = reaction.message.channel

        if self.getRole("M+ Banned") in user.roles:
            await channel.send(f"\U0001F6AB {user.mention}, you are currently Mythic+ banned and therefore not allowed to sign up. \U0001F6AB")
            await reaction.remove(user)
            return

        groupQuery = f"SELECT * FROM mythicplus.group WHERE id = '{id}'"
        group = self.dbc.select(groupQuery)

        if group is None: return
        author = group["advertiser"]
        author = author.split(" ", 1)[0]

        if group["created"]:
            if str(reaction.emoji) == str(self.doneEmoji) and user.mention == author:
                gold_pot = group["gold_pot"]
                if "k" in gold_pot:
                    gold_pot = gold_pot.replace('k', '')
                    gold_pot = str(gold_pot) + "000"

                party = re.findall("<@!.*?>", reaction.message.embeds[0].description)
                await self.ctx.invoke(self.client.get_command('completed'), gold_pot, group['payment_realm'], author, party[0], party[1], party[2], party[3])

            return

        additionalRolesQuery = f"SELECT `role` FROM mythicplus.group_additional_roles WHERE groupid = '{id}'"
        group["additional_roles"] = self.dbc.select(additionalRolesQuery, True)

        if str(reaction.emoji) == str(self.tankEmoji):
            data = {"user": user, "faction": group["faction"], "armor_type": group["armor_type"], "keystone_level": group["keystone_level"], "role": "Tank", "additional_roles": group["additional_roles"]}
            if not await self.checkRoles(channel, data):
                await reaction.remove(user)
                return

            role = "Tank"

        if str(reaction.emoji) == str(self.healerEmoji):
            data = {"user": user, "faction": group["faction"], "armor_type": group["armor_type"], "keystone_level": group["keystone_level"], "role": "Healer", "additional_roles": group["additional_roles"]}
            if not await self.checkRoles(channel, data):
                await reaction.remove(user)
                return

            role = "Healer"

        if str(reaction.emoji) == str(self.dpsEmoji):
            data = {"user": user, "faction": group["faction"], "armor_type": group["armor_type"], "keystone_level": group["keystone_level"], "role": "Damage", "additional_roles": group["additional_roles"]}
            if not await self.checkRoles(channel, data):
                await reaction.remove(user)
                return

            role = "Damage"

        if str(reaction.emoji) == str(self.tankEmoji) or str(reaction.emoji) == str(self.healerEmoji) or str(reaction.emoji) == str(self.dpsEmoji):
            query = f"""INSERT INTO mythicplus.booster (groupid, `user`, `role`)
                       SELECT '{id}', '{user.mention}', '{role}' FROM DUAL
                       WHERE NOT EXISTS (SELECT groupid, `user` FROM mythicplus.booster
                                WHERE groupid = '{id}' AND `user` = '{user.mention}')"""
            existsQuery = f"SELECT EXISTS(SELECT 1 FROM mythicplus.keystone WHERE groupid = '{id}' AND user = '{user.mention}') as 'result'"
            self.dbc.insert(query)
            existsInKeystone = self.dbc.select(existsQuery)

            if not existsInKeystone["result"]:
                query = f"""INSERT INTO mythicplus.keystone (groupid, `user`)
                           SELECT '{id}', '{user.mention}' FROM DUAL
                           WHERE NOT EXISTS (SELECT groupid, `user` FROM mythicplus.keystone
                                    WHERE groupid = '{id}' AND `user` = '{user.mention}')"""
                self.dbc.insert(query)

        if str(reaction.emoji) == str(self.keystoneEmoji):
            existsQuery = f"SELECT EXISTS(SELECT 1 FROM mythicplus.keystone WHERE groupid = '{id}' AND user = '{user.mention}') as 'result'"
            existsInKeystone = self.dbc.select(existsQuery)

            if existsInKeystone["result"]:
                query = f"""UPDATE mythicplus.keystone
                        SET has_keystone = 1
                        WHERE groupid = %s AND user = %s"""
                value = (id, user.mention)
                self.dbc.insert(query, value)
            else:
                await reaction.remove(user)
                await channel.send(f"{user.mention}, assign yourself a role before marking yourself as a keystone holder.")
                return

        if str(reaction.emoji) == str(self.tankEmoji) or str(reaction.emoji) == str(self.healerEmoji) or str(reaction.emoji) == str(self.dpsEmoji) or str(reaction.emoji) == str(self.keystoneEmoji):
            await self.updateGroup(reaction.message)

        if str(reaction.emoji) == str(self.teamEmoji):
            data = {"user": user, "faction": group["faction"], "armor_type": group["armor_type"], "keystone_level": group["keystone_level"], "role": "All", "team": True, "additional_roles": group["additional_roles"]}
            if not await self.checkRoles(channel, data):
                await reaction.remove(user)
                return

            existsInBoosterQuery = f"SELECT EXISTS(SELECT 1 FROM mythicplus.booster WHERE groupid = '{id}' AND user = '{user.mention}') as 'result'"
            existsInKeystoneQuery = f"SELECT EXISTS(SELECT 1 FROM mythicplus.keystone WHERE groupid = '{id}' AND user = '{user.mention}') as 'result'"
            existsInBooster = self.dbc.select(existsInBoosterQuery)
            existsInKeystone = self.dbc.select(existsInKeystoneQuery)

            if not existsInBooster["result"]:
                query = f"""INSERT INTO mythicplus.booster (groupid, `user`, `role`, is_teamleader)
                           VALUES ('{id}', '{user.mention}', 'All', '1')"""
                self.dbc.insert(query)
            else:
                query = f"""UPDATE mythicplus.booster
                        SET `role` = 'All', is_teamleader = 1
                        WHERE groupid = %s AND user = %s"""
                value = (id, user.mention)
                self.dbc.insert(query, value)

            if not existsInKeystone["result"]:
                query = f"""INSERT INTO mythicplus.keystone (groupid, `user`, has_keystone)
                           SELECT '{id}', '{user.mention}', 1 FROM DUAL
                           WHERE NOT EXISTS (SELECT groupid, `user` FROM mythicplus.keystone
                                    WHERE groupid = '{id}' AND `user` = '{user.mention}')"""
                self.dbc.insert(query)
            else:
                query = f"""UPDATE mythicplus.keystone
                        SET has_keystone = 1
                        WHERE groupid = %s AND user = %s"""
                value = (id, user.mention)
                self.dbc.insert(query, value)

            group = [user.mention, user.mention, user.mention, user.mention, user.mention]
            await self.createGroup(reaction.message, group, team=True)
            return

        if str(reaction.emoji) == str(self.cancelEmoji):
            if user.mention == author:
                await reaction.message.delete() #TODO: remove from database?
                await self.cancelGroup(reaction.message)

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        if self.client.user == user: return
        if "boosts" not in reaction.message.channel.name: return
        if not reaction.message.embeds: return
        id = reaction.message.id
        channel = reaction.message.channel

        query = f"SELECT * FROM mythicplus.group WHERE id = '{id}'"
        group = self.dbc.select(query)
        if group is None or group["created"]: return

        if str(reaction.emoji) == str(self.tankEmoji):
            role = "Tank"

        if str(reaction.emoji) == str(self.healerEmoji):
            role = "Healer"

        if str(reaction.emoji) == str(self.dpsEmoji):
            role = "Damage"

        if str(reaction.emoji) == str(self.tankEmoji) or str(reaction.emoji) == str(self.healerEmoji) or str(reaction.emoji) == str(self.dpsEmoji):
            existsQuery = f"SELECT EXISTS(SELECT 1 FROM mythicplus.booster WHERE groupid = '{id}' AND user = '{user.mention}' AND role = '{role}') as 'result'"
            existsInBooster = self.dbc.select(existsQuery)

            if existsInBooster["result"]:
                query = f"""DELETE FROM mythicplus.booster WHERE groupid = '{id}' AND user = '{user.mention}' AND role = '{role}'"""
                self.dbc.delete(query)

        if str(reaction.emoji) == str(self.keystoneEmoji):
            existsQuery = f"SELECT EXISTS(SELECT 1 FROM mythicplus.keystone WHERE groupid = '{id}' AND user = '{user.mention}') as 'result'"
            existsInKeystone = self.dbc.select(existsQuery)

            if existsInKeystone["result"]:
                query = f"""UPDATE mythicplus.keystone
                        SET has_keystone = 0
                        WHERE groupid = %s AND user = %s"""
                value = (id, user.mention)
                self.dbc.insert(query, value)

        if str(reaction.emoji) == str(self.tankEmoji) or str(reaction.emoji) == str(self.healerEmoji) or str(reaction.emoji) == str(self.dpsEmoji) or str(reaction.emoji) == str(self.keystoneEmoji):
            await self.updateGroup(reaction.message)

    @commands.command()
    @commands.has_any_role("Advertiser", "Management", "Council")
    async def generate(self, ctx):
        self.ctx = ctx
        msg = ctx.message.content[10:]
        result = [x.strip() for x in re.split(' ', msg)]
        channel = ctx.message.channel.name

        if "horde" in channel:
            faction = "Horde"
        elif "alliance" in channel:
            faction = "Alliance"

        if len(result) >= 6:
            keystone = result[2]
            keystoneLevel = int(keystone.partition("+")[2])
            mentions = ""
            result[5] = result[5].capitalize()
            armor = result[5]

            if result[5] != "Any":
                if not self.containsRoleMention(result[5]):
                    armor = self.getRole(result[5]).mention

            advertiserNote = ""
            additionalRoles = []
            if keystoneLevel < 18:
                for x in range(6, len(result)):
                    if self.containsRoleMention(result[x]):
                        mentions += result[x] + " "
                        additionalRoles.append(result[x])
                    else:
                        advertiserNote += result[x] + " "

            if not additionalRoles:
                if keystoneLevel < 18 and result[5] != "Any":
                    if result[5] == "Cloth" or result[5] == "Mail":
                        tankRole = self.getRole("Tank").mention
                        mentions += tankRole + " "

                    mentions += armor + " "
                else:
                    armor = "Any"

                    if keystoneLevel >= 18:
                        keystoneRole = self.getRole("Legendary").mention
                        mentions += keystoneRole + " "
                    else:
                        if keystoneLevel >= 15 and keystoneLevel < 18:
                            if faction == "Horde":
                                keystoneRole = self.getRole("Highkey Booster Horde").mention
                            elif faction == "Alliance":
                                keystoneRole = self.getRole("Highkey Booster Alliance").mention
                            mentions += keystoneRole + " "
                        elif keystoneLevel >= 10 and keystoneLevel <= 14:
                            keystoneRole = self.getRole("Mplus Booster").mention
                            mentions += keystoneRole + " "

                        tankRole = self.getRole("Tank").mention
                        healerRole = self.getRole("Healer").mention
                        damageRole = self.getRole("Damage").mention
                        mentions += tankRole + " " + healerRole + " " + damageRole + " "

            advertiser = f"{ctx.message.author.mention} ({result[0]})"
            if "k" in result[3]:
                goldPot = result[3].replace('k', '')
                goldPot = str(goldPot) + "000"
            else:
                goldPot = result[3]
            boosterCut = math.ceil((int(goldPot) / 100) * 17.8)

            embed = discord.Embed(title=f"Generating {result[2]} run!", description="Click on the reaction below the post with your assigned roles to join the group.\n" +
                                        "First come first served **but** the bot will **prioritise** a keyholder over those who do not have one.\n", color=0x5cf033)
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/632628531528073249/644669381451710495/TwilightDiscIocn.jpg")
            embed.add_field(name="Gold Pot", value=result[3], inline=True)
            embed.add_field(name="Booster Cut", value=f"{boosterCut:n}", inline=True)
            embed.add_field(name="Payment Realm", value=result[1], inline=True)
            embed.add_field(name="Keystone Level", value=result[2], inline=True)
            embed.add_field(name="Dungeon", value=result[4], inline=True)
            embed.add_field(name="Armor Type", value=armor, inline=True)
            embed.add_field(name="Advertiser", value=advertiser)

            if advertiserNote:
                embed.add_field(name="Advertiser Note", value=advertiserNote, inline=False)

            msg = await ctx.message.channel.send(content=mentions, embed=embed)
            embed.set_footer(text=f"Group id: {msg.id}.")
            await msg.edit(embed=embed)

            query = """INSERT INTO mythicplus.group (id, title, description, faction, payment_realm, gold_pot, booster_cut, keystone_level, dungeon, armor_type, advertiser, advertiser_note, footer)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            values = (msg.id, embed.title, embed.description, faction, result[1], result[3], boosterCut, result[2], result[4], armor, advertiser, advertiserNote, embed.footer.text)
            self.dbc.insert(query, values)

            if additionalRoles:
                query = "INSERT INTO mythicplus.group_additional_roles (groupid, role) VALUES "
                for additionalRole in additionalRoles:
                    query += f"('{msg.id}', '{additionalRole}'), "

                self.dbc.insert(query[:-2])

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

            # Done
            await msg.add_reaction(self.doneEmoji)

            await ctx.message.delete()

        else:
            # Needs more/less fields
            await ctx.message.channel.send(':x: The command you have entered is invalid. Please check if the command you entered is valid. :x:', delete_after=10.0)

    async def cancelGroup(self, message):
        id = message.id
        mentions = ""

        try:
            tank = self.dbc.selectPriorityBooster("Tank", id, 1)[0]["Tank"]
            mentions += tank + " "
        except:
            pass
        try:
            healer = self.dbc.selectPriorityBooster("Healer", id, 1)[0]["Healer"]
            mentions += healer + " "
        except:
            pass
        dps = self.dbc.selectPriorityBooster("Damage", id, 2)
        try:
            dpsOne = dps[0]["Damage"]
            mentions += dpsOne + " "
        except:
            pass
        try:
            dpsTwo = dps[1]["Damage"]
            mentions += dpsTwo
        except:
            pass

        if mentions:
            createdMessage = (f"{mentions}\n" +
                      f"Your group was cancelled by the advertiser.\n")
            await message.channel.send(createdMessage)

    async def updateGroup(self, message):
        id = message.id

        try:
            tank = self.dbc.selectPriorityBooster("Tank", id, 1)[0]["Tank"]
        except:
            tank = ""
        try:
            healer = self.dbc.selectPriorityBooster("Healer", id, 1)[0]["Healer"]
        except:
            healer = ""
        dps = self.dbc.selectPriorityBooster("Damage", id, 2)
        try:
            dpsOne = dps[0]["Damage"]
        except:
            dpsOne = ""
        try:
            dpsTwo = dps[1]["Damage"]
        except:
            dpsTwo = ""
        try:
            keystoneQuery = f"""SELECT `user`
                              FROM mythicplus.keystone K WHERE groupid = '{id}' AND has_keystone = 1 AND
                              EXISTS
                                (SELECT 1
                                  FROM mythicplus.booster B WHERE K.`user` = B.`user`) LIMIT 1"""
            keystone = self.dbc.select(keystoneQuery)
            keystoneHolder = keystone["user"]
        except:
            keystoneHolder = ""

        if tank and healer and dpsOne and dpsTwo and keystoneHolder:
            group = [tank, healer, dpsOne, dpsTwo, keystoneHolder]
            await self.createGroup(message, group)
            return

        embed = message.embeds[0]
        embed.description = f"""Click on the reaction below the post with your assigned roles to join the group. First come first serve.\n
                            {self.tankEmoji} {tank}\n{self.healerEmoji} {healer}\n{self.dpsEmoji} {dpsOne}\n{self.dpsEmoji} {dpsTwo}\n\n{self.keystoneEmoji} {keystoneHolder}"""
        await message.edit(embed=embed)

    async def createGroup(self, message, group, team=False):
        query = f"""UPDATE mythicplus.group
                SET created = 1
                WHERE id = {message.id}"""
        self.dbc.insert(query)

        embed = message.embeds[0]

        tank = group[0]
        healer = group[1]
        dpsOne = group[2]
        dpsTwo = group[3]
        keystoneHolder = group[4]

        query = f"SELECT keystone_level FROM mythicplus.group WHERE id = '{message.id}'"
        group = self.dbc.select(query)

        advertiser = re.findall('\(([^)]+)', embed.fields[6].value)[0]

        embed.title = f"Generated {group['keystone_level']} Group"
        embed.description = (f"{self.tankEmoji} {tank}\n{self.healerEmoji} {healer}\n{self.dpsEmoji} {dpsOne}\n{self.dpsEmoji} {dpsTwo}\n\n{self.keystoneEmoji} {keystoneHolder}\n" +
                             f"Please whisper `/w {advertiser} invite`")
        embed.set_footer(text=f"{embed.footer.text} Group created at: {datetime.datetime.now().strftime('%H:%M:%S')}")
        editedmsg = await message.edit(embed=embed)

        mentions = f"{self.teamEmoji} {tank}" if team else f"{self.tankEmoji} {tank} {self.healerEmoji} {healer} {self.dpsEmoji} {dpsOne} {self.dpsEmoji} {dpsTwo}"
        createdMessage = (f"{mentions}\nPlease whisper `/w {advertiser} invite`. See the message above for more details.\n" +
                  f"Group id: {message.id}")
        await message.channel.send(createdMessage)

    async def checkRoles(self, channel, data):
        isValid = False
        keystoneLevel = int(data["keystone_level"].partition("+")[2])

        if keystoneLevel >= 15:
            if data["faction"] == "Horde":
                factionRole = self.getRole("Highkey Booster Horde")
            elif data["faction"] == "Alliance":
                factionRole = self.getRole("Highkey Booster Alliance")
        else:
            factionRole = self.getRole("Mplus Booster")

        if keystoneLevel >= 18:
            keystoneRole = self.getRole("Legendary")
        if keystoneLevel <= 17:
            keystoneRole = self.getRole("Epic")
        if keystoneLevel <= 14:
            keystoneRole = self.getRole("Rare")

        userRoles = data["user"].roles

        if data["additional_roles"]:
            allRoles = ""

            for additionalRole in data["additional_roles"]:
                additionalRole = self.getRoleById(additionalRole["role"])
                allRoles += f"`{additionalRole}`, "
                isAllowedRole = False

                if str(additionalRole) not in self.tankRoles and data["role"] == "Tank":
                    isValid = True
                    isAllowedRole = True
                elif str(additionalRole) not in self.healerRoles and data["role"] == "Healer":
                    isValid = True
                    isAllowedRole = True
                if not isAllowedRole:
                    if additionalRole in userRoles:
                        isValid = True
                        break

            if not isValid:
                await channel.send(f"{data['user'].mention}, you do **NOT** have any of the required {allRoles[:-2]} role(s) to join this group.")
                return False


        if factionRole in userRoles:
            isValid = True
        else:
            await channel.send(f"{data['user'].mention}, you do **NOT** have the required `{factionRole}` role to join this group.")
            return False

        if keystoneRole in userRoles:
            isValid = True
        else:
            await channel.send(f"{data['user'].mention}, you do **NOT** have the required `{keystoneRole}` role to join this group.")
            return False

        if data["role"] != "Any" and data["role"] != "All":
            role = self.getRole(data["role"])
            if role in userRoles:
                isValid = True
            else:
                await channel.send(f"{data['user'].mention}, you do **NOT** have the required `{role}` role to join this group.")
                return False

        if data["armor_type"] != "Any":
            armorRole = self.getRoleById(data["armor_type"])
            isAllowedRole = False

            if str(armorRole) not in self.tankRoles and data["role"] == "Tank":
                isValid = True
                isAllowedRole = True
            elif str(armorRole) not in self.healerRoles and data["role"] == "Healer":
                isValid = True
                isAllowedRole = True
            if not isAllowedRole:
                if armorRole in userRoles:
                    isValid = True
                else:
                    await channel.send(f"{data['user'].mention}, you do **NOT** have the required `{armorRole}` role to join this group.")
                    return False

        if "team" in data:
            teamRole = self.getRole("M+ TEAM LEADER")
            if teamRole in userRoles:
                isValid = True
            else:
                await channel.send(f"{data['user'].mention}, you do **NOT** have the required `{teamRole}` role to join this group.")
                return False

        return isValid

    def getRole(self, role):
        return discord.utils.find(lambda r: r.name == role, self.guild.roles)

    def getRoleById(self, role):
        role = re.sub('[<@&>]', '', role)
        return discord.utils.find(lambda r: r.id == int(role), self.guild.roles)

    def containsRoleMention(self, string):
        return re.search('(?=.*<)(?=.*@)(?=.*&)(?=.*>)', string)

def setup(client):
    client.add_cog(Generate(client))
