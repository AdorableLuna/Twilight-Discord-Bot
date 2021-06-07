import discord
import re
import datetime
import time
import itertools
import math
import locale
import json
import chat_exporter
import io

from cogs.maincog import Maincog
from discord.utils import get
from discord.ext import commands
from db import dbconnection as dbc

locale.setlocale(locale.LC_ALL, '')

class Mythicplus(Maincog):

    def __init__(self, client):
        Maincog.__init__(self, client)
        self.dbc = dbc.DBConnection()
        self.teamEmoji = "\U0001F1F9"
        self.cancelEmoji = "\U0000274C"
        self.doneEmoji = "\U00002705"
        self.trashEmoji = "\U0001F5D1"
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
        self.legendaryKeystoneLevel = 16
        self.epicKeystoneLevel = 14
        self.rareKeystoneLevel = 14
        self.mplusCategory = 843473846400843797

        with open('taxes.json', 'r') as taxesFile:
            self.taxes = json.load(taxesFile)
            taxesFile.close()

        self.client.loop.create_task(self.on_ready_init())

    async def on_ready_init(self):
        await self.client.wait_until_ready()
        self.completedChannel = self.client.get_channel(731479403862949928)
        self.bookingLogsChannel = self.client.get_channel(844928358684819490)
        self.tankEmoji = self.client.get_emoji(714930608266018859)
        self.healerEmoji = self.client.get_emoji(714930600267612181)
        self.dpsEmoji = self.client.get_emoji(714930578461425724)
        self.keystoneEmoji = self.client.get_emoji(715918950092898346)

    def check_if_active_boost_channel(self, channel_name):
        reg = re.compile("(horde|alliance)-\w*-\w*-\w*-(boost)")
        return re.match(reg, channel_name)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if self.checkIfUserIsItself(payload.member): return
        user = payload.member
        channel = self.client.get_channel(payload.channel_id)
        if not channel: return
        if isinstance(channel, discord.DMChannel): return
        if not self.check_if_active_boost_channel(channel.name): return

        if str(payload.emoji) == str(self.trashEmoji):
            messages = await channel.history().flatten()
            group_id = messages[-1].id

            groupQuery = f"SELECT `advertiser` FROM mythicplus.group WHERE id = '{group_id}'"
            author = self.dbc.select(groupQuery)
            author = author["advertiser"].split(" ", 1)[0]

            if user.mention == author:
                await self.createTranscript(channel, user)
                await channel.delete()
            return

        message = await channel.fetch_message(payload.message_id)

        if not message.embeds: return
        id = message.id
        guild = self.client.get_guild(payload.guild_id)

        if self.helper.getRole(guild, "M+ Banned") in user.roles:
            await channel.send(f"\U0001F6AB {user.mention}, you are currently Mythic+ banned and therefore not allowed to sign up. \U0001F6AB")
            await message.remove_reaction(payload.emoji, user)
            return

        groupQuery = f"SELECT * FROM mythicplus.group WHERE id = '{id}'"
        group = self.dbc.select(groupQuery)

        if group is None: return
        author = group["advertiser"]
        author = author.split(" ", 1)[0]

        if group["created"] and not group["completed"]:
            if str(payload.emoji) == str(self.doneEmoji) and user.mention == author:
                realmFaction = group['payment_realm'].rsplit("-", 1)

                # If faction is specified, then overwrite the default channel faction
                if(len(realmFaction) == 2):
                    if "horde" in realmFaction[1].lower():
                        paymentFaction = "H"
                    elif "h" in realmFaction[1].lower():
                        paymentFaction = "H"
                    elif "alliance" in realmFaction[1].lower():
                        paymentFaction = "A"
                    elif "a" in realmFaction[1].lower():
                        paymentFaction = "A"

                # Otherwise, just use default channel faction
                else:
                    if "horde" in channel.name:
                        paymentFaction = "H"
                    elif "alliance" in channel.name:
                        paymentFaction = "A"

                paymentRealm = realmFaction[0]

                gold_pot = group["gold_pot"]
                if "k" in gold_pot:
                    gold_pot = gold_pot.replace('k', '')
                    gold_pot = str(gold_pot) + "000"

                usernameRegex = "<@.*?>"
                nicknameRegex = "<@!.*?>"
                party = re.compile("(%s|%s)" % (usernameRegex, nicknameRegex)).findall(message.embeds[0].description)

                ctx = await self.client.get_context(message)
                ctx.author = get(ctx.guild.members, mention=author)
                result = await ctx.invoke(self.client.get_command('completed'), 'M+', group['faction'], gold_pot, f"{paymentRealm}-{paymentFaction}", author, party[0], party[1], party[2], party[3], party[4])

                if result[0]:
                    await channel.send(f"{self.doneEmoji} Succesfully added the Mythic+ run to the sheets!\n"
                                       f"Group id: {id}\n"
                                       f"{result[1].jump_url}")
                    await message.clear_reaction(self.doneEmoji)

                    msg = await channel.send(f"{author}, click the {self.trashEmoji} to delete this channel.")
                    await msg.add_reaction(self.trashEmoji)
                else:
                    await result[1].delete()
                    await channel.send(f"{self.cancelEmoji} Something went wrong when trying to add the Mythic+ run to the sheets. Please add it manually in {self.completedChannel.mention}\n"
                                       f"Group id: {id}")

                query = f"""UPDATE mythicplus.group
                       SET completed = 1
                       WHERE id = {id}"""
                self.dbc.insert(query)

            return

        additionalRolesQuery = f"SELECT `role` FROM mythicplus.group_additional_roles WHERE groupid = '{id}'"
        group["additional_roles"] = self.dbc.select(additionalRolesQuery, True)

        if str(payload.emoji) == str(self.tankEmoji):
            data = {"user": user, "faction": group["faction"], "armor_type": group["armor_type"], "keystone_level": group["keystone_level"], "role": "Tank", "additional_roles": group["additional_roles"]}
            if not await self.checkRoles(guild, channel, data):
                await message.remove_reaction(payload.emoji, user)
                return

            role = "Tank"

        if str(payload.emoji) == str(self.healerEmoji):
            data = {"user": user, "faction": group["faction"], "armor_type": group["armor_type"], "keystone_level": group["keystone_level"], "role": "Healer", "additional_roles": group["additional_roles"]}
            if not await self.checkRoles(guild, channel, data):
                await message.remove_reaction(payload.emoji, user)
                return

            role = "Healer"

        if str(payload.emoji) == str(self.dpsEmoji):
            data = {"user": user, "faction": group["faction"], "armor_type": group["armor_type"], "keystone_level": group["keystone_level"], "role": "Damage", "additional_roles": group["additional_roles"]}
            if not await self.checkRoles(guild, channel, data):
                await message.remove_reaction(payload.emoji, user)
                return

            role = "Damage"

        if str(payload.emoji) == str(self.tankEmoji) or str(payload.emoji) == str(self.healerEmoji) or str(payload.emoji) == str(self.dpsEmoji):
            query = f"""INSERT INTO mythicplus.booster (groupid, `user`, `role`)
                       VALUES ('{id}', '{user.mention}', '{role}')"""
            self.dbc.insert(query)

        if str(payload.emoji) == str(self.keystoneEmoji):
            existsQuery = f"SELECT EXISTS(SELECT 1 FROM mythicplus.booster WHERE groupid = '{id}' AND user = '{user.mention}') as 'result'"
            existsInBooster = self.dbc.select(existsQuery)
            if existsInBooster["result"]:
                query = f"""INSERT INTO mythicplus.keystone (groupid, `user`, `has_keystone`)
                            SELECT '{id}', '{user.mention}', 1 FROM DUAL
                            WHERE NOT EXISTS (SELECT groupid, `user` FROM mythicplus.keystone
                                    WHERE groupid = '{id}' AND `user` = '{user.mention}')"""
                self.dbc.insert(query)
            else:
                await message.remove_reaction(payload.emoji, user)
                await channel.send(f"{user.mention}, assign yourself a role before marking yourself as a keystone holder.")
                return

        if str(payload.emoji) == str(self.tankEmoji) or str(payload.emoji) == str(self.healerEmoji) or str(payload.emoji) == str(self.dpsEmoji) or str(payload.emoji) == str(self.keystoneEmoji):
            await self.updateGroup(message)

        if str(payload.emoji) == str(self.teamEmoji):
            data = {"user": user, "faction": group["faction"], "armor_type": group["armor_type"], "keystone_level": group["keystone_level"], "role": "All", "team": True, "additional_roles": group["additional_roles"]}
            if not await self.checkRoles(guild, channel, data):
                await message.remove_reaction(payload.emoji, user)
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

            author = self.helper.getMemberByMention(guild, author)
            group = [user.mention, user.mention, user.mention, user.mention, user.mention, author]
            await self.createGroup(message, group, team=True)
            return

        if str(payload.emoji) == str(self.cancelEmoji):
            if user.mention == author:
                if group["created"]:
                    await user.send(content="Don't forget to post the completed run.", embed=message.embeds[0])
                else:
                    await self.cancelGroup(guild, message)
                    await self.createTranscript(channel, user)

                await message.channel.delete()

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        channel = self.client.get_channel(payload.channel_id)
        if not channel: return
        if isinstance(channel, discord.DMChannel): return #from completed
        guild = self.client.get_guild(payload.guild_id)
        user = guild.get_member(payload.user_id)
        if self.checkIfUserIsItself(user): return

        if not self.check_if_active_boost_channel(channel.name): return
        message = await channel.fetch_message(payload.message_id)

        if not message.embeds: return
        id = message.id

        query = f"SELECT * FROM mythicplus.group WHERE id = '{id}'"
        group = self.dbc.select(query)
        if group is None or group["created"]: return

        if str(payload.emoji) == str(self.tankEmoji):
            role = "Tank"

        if str(payload.emoji) == str(self.healerEmoji):
            role = "Healer"

        if str(payload.emoji) == str(self.dpsEmoji):
            role = "Damage"

        if str(payload.emoji) == str(self.tankEmoji) or str(payload.emoji) == str(self.healerEmoji) or str(payload.emoji) == str(self.dpsEmoji):
            query = f"""DELETE FROM mythicplus.booster WHERE groupid = '{id}' AND user = '{user.mention}' AND role = '{role}'"""
            self.dbc.delete(query)

        if str(payload.emoji) == str(self.keystoneEmoji):
            query = f"""DELETE FROM mythicplus.keystone WHERE groupid = '{id}' AND user = '{user.mention}'"""
            self.dbc.delete(query)

        if str(payload.emoji) == str(self.tankEmoji) or str(payload.emoji) == str(self.healerEmoji) or str(payload.emoji) == str(self.dpsEmoji) or str(payload.emoji) == str(self.keystoneEmoji):
            await self.updateGroup(message)

    @commands.check(lambda ctx: False)
    @commands.command()
    @commands.has_any_role("Trainee Advertiser", "Advertiser", "Management", "Council")
    async def generate_mythic_plus(self, ctx):
        channel = ctx.message.channel.name

        msg = ctx.message.content[10:]
        result = [x.strip() for x in msg.split()]

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
                if not self.helper.containsRoleMention(result[5]):
                    armor = self.helper.getRole(ctx.guild, result[5]).mention

            advertiserNote = ""
            additionalRoles = []
            if keystoneLevel < self.legendaryKeystoneLevel:
                for x in range(6, len(result)):
                    if self.helper.containsRoleMention(result[x]):
                        mentions += result[x] + " "
                        additionalRoles.append(result[x])
                    else:
                        advertiserNote += result[x] + " "

            if not additionalRoles:
                if keystoneLevel < self.legendaryKeystoneLevel and result[5] != "Any":
                    if result[5] == "Cloth" or result[5] == "Mail":
                        tankRole = self.helper.getRole(ctx.guild, "Tank").mention
                        mentions += tankRole + " "

                    mentions += armor + " "
                else:
                    armor = "Any"

                    if keystoneLevel >= self.legendaryKeystoneLevel:
                        keystoneRole = self.helper.getRole(ctx.guild, "Legendary").mention
                        mentions += keystoneRole + " "
                    else:
                        if keystoneLevel > self.epicKeystoneLevel and keystoneLevel < self.legendaryKeystoneLevel:
                            keystoneRole = self.helper.getRole(ctx.guild, f"Highkey Booster {faction}").mention
                            mentions += keystoneRole + " "
                        elif keystoneLevel <= self.epicKeystoneLevel:
                            keystoneRole = self.helper.getRole(ctx.guild, "Mplus Booster").mention
                            mentions += keystoneRole + " "

                        tankRole = self.helper.getRole(ctx.guild, "Tank").mention
                        healerRole = self.helper.getRole(ctx.guild, "Healer").mention
                        damageRole = self.helper.getRole(ctx.guild, "Damage").mention
                        mentions += tankRole + " " + healerRole + " " + damageRole + " "

            advertiser = f"{ctx.message.author.mention} ({result[0]})"
            result[3] = result[3].lower()

            if "k" in result[3]:
                goldPot = result[3].replace('k', '')
                goldPot = str(goldPot) + "000"
            else:
                goldPot = result[3]
            boosterCut = int(goldPot) * round(((self.taxes["m+"]["boosters"] / 100) / 4), 3)
            advertiserCut = int(goldPot) * round(((self.taxes["m+"]["advertiser"] / 100)), 3)
            managementCut = int(goldPot) * round(((self.taxes["m+"]["management"] / 100)), 3)
            keyholderCut = int(goldPot) * round((self.taxes["m+"]["keyholder"] / 100), 3)

            embed = discord.Embed(title=f"Generating {result[2]} run!", description="Click on the reaction below the post with your assigned roles to join the group.\n" +
                                        "First come first served **but** the bot will **prioritise** a keyholder over those who do not have one.\n", color=0x9013FE)
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/699709321180741642/842730940744466452/Final_Logo_Render.png")
            embed.add_field(name="Gold Pot", value=result[3], inline=True)
            embed.add_field(name="Booster Cut", value=f"{boosterCut:n}", inline=True)
            embed.add_field(name="Advertiser Cut", value=f"{advertiserCut:n}", inline=True)
            embed.add_field(name="Management Cut", value=f"{managementCut:n}", inline=True)
            embed.add_field(name="Keyholder Cut", value=f"{keyholderCut:n}", inline=True)
            embed.add_field(name="Boost Faction", value=f"{faction}", inline=True)
            embed.add_field(name="Payment Realm", value=result[1], inline=True)
            embed.add_field(name="Keystone Level", value=result[2], inline=True)
            embed.add_field(name="Dungeon", value=result[4], inline=True)
            embed.add_field(name="Armor Type", value=armor, inline=True)
            embed.add_field(name="Advertiser", value=advertiser, inline=False)

            if advertiserNote:
                embed.add_field(name="Advertiser Note", value=advertiserNote, inline=False)

            await ctx.message.delete()

            if keystoneLevel > self.epicKeystoneLevel:
                keystoneRole = self.helper.getRole(ctx.guild, f"Highkey Booster {faction}")
            elif keystoneLevel <= self.epicKeystoneLevel:
                keystoneRole = self.helper.getRole(ctx.guild, f"Mplus {faction}")

            mythicplusBannedRole = self.helper.getRole(ctx.guild, "M+ Banned")
            advertiserTrainerRole = self.helper.getRole(ctx.guild, "Advertiser Trainer")
            managementRole = self.helper.getRole(ctx.guild, "Management")
            category = discord.utils.get(ctx.guild.categories, id=self.mplusCategory)
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False, read_messages=False, send_messages=False, add_reactions=False),
                mythicplusBannedRole: discord.PermissionOverwrite(view_channel=False, read_messages=False, send_messages=False, read_message_history=False),
                keystoneRole: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, add_reactions=False, read_message_history=True),
                advertiserTrainerRole: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, add_reactions=False, read_message_history=True),
                managementRole: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, add_reactions=False, read_message_history=True),
                ctx.author: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, add_reactions=False, read_message_history=True),
            }

            await ctx.channel.edit(name=f"{faction}-{result[4].replace("-", "")}-{result[2]}-{'Any' if armor == 'Any' else self.helper.getRoleById(ctx.guild, armor).name}-boost", overwrites=overwrites, reason="Automatic M+ booking made.")
            await ctx.channel.purge(limit=None, check=lambda msg: not msg.pinned)
            msg = await ctx.channel.send(content=mentions, embed=embed)
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

        else:
            # Needs more/less fields
            await ctx.message.channel.send(':x: The command you have entered is invalid. Please check if the command you entered is valid. :x:', delete_after=10.0)

    async def cancelGroup(self, guild, message):
        group = list(dict.fromkeys(filter(None, self.getGroup(message))))

        for i in range(len(group)):
            user = self.helper.getMemberByMention(guild, group[i])
            await user.send("Your group was cancelled by the advertiser.")

    async def updateGroup(self, message):
        group = self.getGroup(message)
        tank = group[0]
        healer = group[1]
        dpsOne = group[2]
        dpsTwo = group[3]
        keystone = group[4]

        if tank and healer and dpsOne and dpsTwo and keystone:
            await self.createGroup(message, group)
            return

        embed = message.embeds[0]
        embed.description = (f"Click on the reaction below the post with your assigned roles to join the group. First come first serve.\n\n" +
                             f"{self.tankEmoji} {tank}\n{self.healerEmoji} {healer}\n{self.dpsEmoji} {dpsOne}\n{self.dpsEmoji} {dpsTwo}\n\n{self.keystoneEmoji} {keystone}")
        await message.edit(embed=embed)

    def getGroup(self, message):
        id = message.id

        allBoostersQuery = f"SELECT * FROM mythicplus.booster WHERE groupid = '{id}'"
        allBoosters = self.dbc.select(allBoostersQuery, True)
        tanks = [booster for booster in allBoosters if booster['role'] == "Tank"]
        healers = [booster for booster in allBoosters if booster['role'] == "Healer"]
        dps = [booster for booster in allBoosters if booster['role'] == "Damage"]
        keystoneQuery = f"SELECT * FROM mythicplus.keystone where groupid = '{id}' AND has_keystone = 1 LIMIT 1;"
        keystone = self.dbc.select(keystoneQuery)
        keystone = "" if keystone == None else keystone['user']

        try:
            keystoneUser = [booster for booster in tanks if booster['user'] == keystone][0]['user']
            role = 'Tank'
        except:
            try:
                keystoneUser = [booster for booster in healers if booster['user'] == keystone][0]['user']
                role = 'Healer'
            except:
                try:
                    keystoneUser = [booster for booster in dps if booster['user'] == keystone][0]['user']
                    role = 'DPS'
                except:
                    keystoneUser = None
                    role = ''

        return self.getBoosters(tanks, healers, dps, keystoneUser, role)

    def getBoosters(self, tanks, healers, dps, keystoneUser, role):
        tank = next((booster['user'] for booster in tanks), "")
        healer = next((booster['user'] for booster in healers if booster['user'] != tank), "")
        try:
            dpsOne = [booster['user'] for booster in dps if booster['user'] != healer and booster['user'] != tank][0]
        except:
            dpsOne = ""
        try:
            dpsTwo = [booster['user'] for booster in dps if booster['user'] != healer and booster['user'] != tank][1]
        except:
            dpsTwo = ""

        if keystoneUser:
            if role == 'Tank':
                tank = keystoneUser
                healer = next((booster['user'] for booster in healers if booster['user'] != keystoneUser and booster['user'] != dpsOne and booster['user'] != dpsTwo), "")
                inDPS = False

            if role == 'Healer':
                tank = next((booster['user'] for booster in tanks if booster['user'] != keystoneUser and booster['user'] != dpsOne and booster['user'] != dpsTwo), "")
                healer = keystoneUser
                inDPS = False

            if role == 'DPS':
                tank = next((booster['user'] for booster in tanks if booster['user'] != keystoneUser and booster['user'] != healer), "")
                healer = next((booster['user'] for booster in healers if booster['user'] != keystoneUser and booster['user'] != tank), "")
                inDPS = True

            if inDPS:
                if dpsOne != keystoneUser:
                    dpsTwo = dpsOne
                    dpsOne = keystoneUser
            else:
                try:
                    dpsOne = [booster['user'] for booster in dps if booster['user'] != keystoneUser and booster['user'] != healer and booster['user'] != tank][0]
                except:
                    dpsOne = ""
                try:
                    dpsTwo = [booster['user'] for booster in dps if booster['user'] != keystoneUser and booster['user'] != healer and booster['user'] != tank][1]
                except:
                    dpsTwo = ""

        keystone = "" if keystoneUser == None else keystoneUser
        group = [tank, healer, dpsOne, dpsTwo, keystone]
        return group

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

        # Group [5] = advertiser in team take
        if team:
            author = group[5]

        query = f"SELECT keystone_level FROM mythicplus.group WHERE id = '{message.id}'"
        group = self.dbc.select(query)

        advertiser = embed.fields[10].value.split(" ", 1)
        advertiserCharacter = re.findall('\(([^)]+)', advertiser[1])[0]

        embed.title = f"Generated {group['keystone_level']} Group"
        embed.description = (f"{self.tankEmoji} {tank}\n{self.healerEmoji} {healer}\n{self.dpsEmoji} {dpsOne}\n{self.dpsEmoji} {dpsTwo}\n\n{self.keystoneEmoji} {keystoneHolder}\n" +
                             f"Please whisper `/w {advertiserCharacter} invite`")
        embed.set_footer(text=f"{embed.footer.text} Group created at: {datetime.datetime.now().strftime('%H:%M:%S')}")
        editedmsg = await message.edit(embed=embed)

        mentions = f"{self.teamEmoji} {tank}" if team else f"{self.tankEmoji} {tank} {self.healerEmoji} {healer} {self.dpsEmoji} {dpsOne} {self.dpsEmoji} {dpsTwo}"
        createdMessage = (f"{mentions}\nPlease whisper `/w {advertiserCharacter} invite`. See the message above for more details.\n" +
                  f"Group id: {message.id}")
        await message.channel.send(createdMessage)

        reactions = message.reactions
        for reaction in reactions[:]:
            await reaction.clear()

        # Done if group is not a team
        if not team:
            await message.add_reaction(self.doneEmoji)
            await message.add_reaction(self.trashEmoji)
        else:
            query = f"""UPDATE mythicplus.group
                   SET completed = 1
                   WHERE id = {message.id}"""
            self.dbc.insert(query)

            await author.send(content="Here's a backup of the run, incase the channel gets deleted before the completed run was posted.", embed=embed)
            msg = await message.channel.send(f"{advertiser[0]}, click the {self.trashEmoji} to delete this channel. **Make sure to post the completed run FIRST before deleting this channel.**")
            await msg.add_reaction(self.trashEmoji)

    async def checkRoles(self, guild, channel, data):
        isValid = False
        keystoneLevel = int(data["keystone_level"].partition("+")[2])

        if keystoneLevel > self.epicKeystoneLevel:
            if data["faction"] == "Horde":
                factionRole = self.helper.getRole(guild, "Highkey Booster Horde")
            elif data["faction"] == "Alliance":
                factionRole = self.helper.getRole(guild, "Highkey Booster Alliance")
        else:
            factionRole = self.helper.getRole(guild, "Mplus Booster")

        keystoneRole = self.getKeystoneRole(guild, keystoneLevel)

        userRoles = data["user"].roles

        if data["additional_roles"]:
            allRoles = ""

            for additionalRole in data["additional_roles"]:
                additionalRole = self.helper.getRoleById(guild, additionalRole["role"])
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
                await data['user'].send(f"You do **NOT** have any of the required {allRoles[:-2]} role(s) to join this group. Head to <#700676105387901038> and pick your roles.")
                return False


        if factionRole in userRoles:
            isValid = True
        else:
            await data['user'].send(f"You do **NOT** have the required `{factionRole}` role to join this group. Please open a ticket regarding the faction role.")
            return False

        if keystoneRole in userRoles:
            isValid = True
        else:
            await data['user'].send(f"You do **NOT** have the required `{keystoneRole}` role to join this group. Head to <#728994402122465330> and upgrade your roles.")
            return False

        if data["role"] != "Any" and data["role"] != "All":
            role = self.helper.getRole(guild, data["role"])
            if role in userRoles:
                isValid = True
            else:
                await data['user'].send(f"You do **NOT** have the required `{role}` role to join this group. Head to <#700676105387901038> and pick your roles.")
                return False

        if data["armor_type"] != "Any":
            armorRole = self.helper.getRoleById(guild, data["armor_type"])
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
                    await data['user'].send(f"You do **NOT** have the required `{armorRole}` role to join this group. Head to <#700676105387901038> and pick your roles.")
                    return False

        if "team" in data:
            teamRole = self.helper.getRole(guild, "M+ TEAM LEADER")
            if teamRole in userRoles:
                isValid = True
            else:
                await data['user'].send(f"You do **NOT** have the required `{teamRole}` role to join this group. However, if you are in a team, then your team leader must sign.")
                return False

        return isValid

    def getKeystoneRole(self, guild, keystoneLevel):
        if keystoneLevel >= self.legendaryKeystoneLevel:
            keystoneRole = self.helper.getRole(guild, "Legendary")
        if keystoneLevel > self.epicKeystoneLevel and keystoneLevel < self.legendaryKeystoneLevel:
            keystoneRole = self.helper.getRole(guild, "Epic")
        if keystoneLevel <= self.epicKeystoneLevel:
            keystoneRole = self.helper.getRole(guild, "Rare")

        return keystoneRole

    async def createTranscript(self, channel, user):
        embed = discord.Embed(title="M+ Transcript", color=0x9013FE)
        embed.set_thumbnail(url="https://cdn.discordapp.com/icons/629729313520091146/a_c708c65e803287d010ea489dd43383be.gif?size=1024")
        embed.add_field(name="Advertiser", value=user.mention, inline=True)
        embed.add_field(name="Advertiser ID", value=user.id, inline=True)
        embed.add_field(name="Section", value=channel.category, inline=True)
        embed.add_field(name="Deleted By", value=user.mention, inline=True)
        embed.add_field(name="Channel Name", value=channel.name, inline=True)

        transcript = await chat_exporter.export(channel, set_timezone="Europe/Amsterdam")

        if transcript is None:
            await self.bookingLogsChannel.send(f"Transcript could not be created for channel: {channel.name}")
            return

        transcript_file = discord.File(io.BytesIO(transcript.encode()),
                                        filename=f"transcript-{channel.name}.html")

        msg = await self.bookingLogsChannel.send(embed=embed, file=transcript_file)
        embed.add_field(name="Transcript", value=f"[Click Here]({msg.attachments[0].url})", inline=True)
        await msg.edit(embed=embed)

def setup(client):
    client.add_cog(Mythicplus(client))
