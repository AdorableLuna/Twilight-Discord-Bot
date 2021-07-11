import discord
import random
import re
import requests
import json
import asyncio

from cogs.maincog import Maincog
from discord.utils import get
from discord.ext import commands
from db import dbconnection as dbc

class BookingsPvP(Maincog):

    def __init__(self, client):
        Maincog.__init__(self, client, whitelistedChannels = [862767690656645121, 862802913797603378, 862802944273154058, 862802969648431154])
        self.dbc = dbc.DBConnection()
        self.boostEmoji = "\U0001F3CB"
        self.linkEmoji = "\U0001F517"
        self.idEmoji = "\U0001F194"
        self.notesEmoji = "\U0001F5D2"
        self.cancelEmoji = "\U0000274C"
        self.doneEmoji = "\U00002705"
        self.moneybagEmoji = "\U0001F4B0"

        with open('taxes.json', 'r') as taxesFile:
            self.taxes = json.load(taxesFile)
            taxesFile.close()

        self.client.loop.create_task(self.on_ready_init())

    async def on_ready_init(self):
        await self.client.wait_until_ready()
        self.bookingChannel = self.client.get_channel(862767690656645121)
        self.completedChannel = self.client.get_channel(731479403862949928)
        self.twosChannel = self.client.get_channel(862802913797603378)
        self.treesChannel = self.client.get_channel(862802944273154058)
        self.rbgChannel = self.client.get_channel(862802969648431154)
        self.goldEmoji = self.client.get_emoji(405027836647440384)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if self.checkIfUserIsItself(payload.member): return
        if not self.checkIfAllowedChannel(payload.channel_id): return
        user = payload.member
        channel = self.client.get_channel(payload.channel_id)
        if not channel: return
        if isinstance(channel, discord.DMChannel): return

        message = await channel.fetch_message(payload.message_id)
        if not message.embeds: return

        bookingQuery = f"SELECT * FROM pvp.booking WHERE runid = '{message.id}'"
        booking = self.dbc.select(bookingQuery)

        if str(payload.emoji) == str(self.moneybagEmoji):

            if booking['timer_expired'] and not booking['booster']:
                await self.setBooster(message, payload.member)

        if not booking['completed']:
            if str(payload.emoji) == str(self.doneEmoji) and payload.member.mention == booking['advertiser']:
                ctx = await self.client.get_context(message)
                ctx.author = get(ctx.guild.members, mention=booking['advertiser'])
                result = await ctx.invoke(self.client.get_command('completed'), 'PvP', booking['boost_faction'], booking['total_pot'], f"{booking['total_pot_realm']}-{'h' if booking['total_pot_faction'] == 'Horde' else 'a'}", booking['advertiser'], booking['booster'])

                if result[0]:
                    await channel.send(f"{self.doneEmoji} Succesfully added the PvP run to the sheets!\n"
                                       f"Group id: {message.id}\n"
                                       f"{result[1].jump_url}")

                    reactions = message.reactions
                    for reaction in reactions[:]:
                        await reaction.clear()
                else:
                    await result[1].delete()
                    await channel.send(f"{self.cancelEmoji} Something went wrong when trying to add the PvP run to the sheets. Please add it manually in {self.completedChannel.mention}\n"
                                       f"Group id: {message.id}")

                query = f"""UPDATE pvp.booking
                       SET completed = 1
                       WHERE runid = {message.id}"""
                self.dbc.insert(query)

        if str(payload.emoji) == str(self.cancelEmoji):
            if not booking['completed'] and payload.member.mention == booking['advertiser']:
                if booking['booster']:
                    guild = self.client.get_guild(payload.guild_id)
                    booster = self.helper.getMemberByMention(guild, booking['booster'])
                    await booster.send("Your booking was cancelled by the advertiser.")

                await message.delete()

    @commands.Cog.listener()
    async def on_message(self, message):
        if self.checkIfUserIsItself(message.author): return
        if isinstance(message.channel, discord.DMChannel): return
        if message.channel.id != self.bookingChannel.id: return

        if not len(message.content.splitlines()) >= 6:
            await self.delete_message(message)
            return

        try:
            category = re.search(r'Category:([^\>]*)Gold:', message.content).group(1).strip()
            goldAndRealm = re.search(r'Gold:([^\>]*)Boost:', message.content).group(1).lstrip()
            gold = goldAndRealm.split(" ", 1)[0]
            goldRealmFaction = goldAndRealm.split(" ", 1)[1].rsplit("-", 1)
            goldRealm = goldRealmFaction[0]
            goldFaction = goldRealmFaction[1].strip()
            goldFaction = "Horde" if goldFaction.lower() == "h" else "Alliance"
            boost = re.search(r'Boost:([^\>]*)Check-PvP Link:', message.content).group(1).lstrip()
            check_pvp_link = re.search(r'Check-PvP Link:([^\>]*)Spec:', message.content).group(1).lstrip()
            spec = re.search(r'Spec:([^\>]*)Notes:', message.content).group(1).lstrip()
            notes = re.search(r'Notes:([^\>]*)', message.content).group(1).lstrip()

            link = re.search("([^/]+)/([^/]+)/?$", check_pvp_link)
            realm = link.group(1)
            character = link.group(2)

            response = requests.get(f"https://raider.io/api/v1/characters/profile?region=eu&realm={realm}&name={character}&fields=gear,covenant")

            if response.ok:
                data = json.loads(response.content)

            channel = None
            mentions = None
            if category.lower() == "2s":
                channel = self.twosChannel
                mentions = self.helper.getRole(message.guild, "PvP Booster").mention
            elif category.lower() == "3s":
                channel = self.treesChannel
                mentions = self.helper.getRole(message.guild, "PvP Booster").mention
            elif category.lower() == "rbg":
                channel = self.rbgChannel
                mentions = self.helper.getRole(message.guild, "RBG Booster").mention

            mentions += f" {message.author.mention}"

            gold = gold.lower()

            if "k" in gold:
                gold = gold.replace('k', '')
                gold = str(gold) + "000"
            gold = int(gold)

            advertiserFee = int(gold) * (self.taxes["pvp"]["advertiser"] / 100)
            boosterFee = int(gold) * (self.taxes["pvp"]["boosters"] / 100)

            embed = discord.Embed(color=0x9013FE)
            embed.set_author(name=f"New {data['faction'].capitalize()} PvP Booking", icon_url=str(message.author.avatar_url))
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/632910453269463070.png?v=1" if data['faction'] == 'horde' else "https://cdn.discordapp.com/emojis/632910801425924106.png?v=1")
            embed.add_field(name="Advertiser", value=message.author.mention, inline=False)
            embed.add_field(name="Booster", value="TBA", inline=False)
            embed.add_field(name="Total Pot", value=f"{self.goldEmoji} {format(int(gold),',d')}", inline=False)
            embed.add_field(name="Total Pot Realm & Faction", value=f"{self.goldEmoji} {goldRealm}-{goldFaction}", inline=False)
            embed.add_field(name="Booster Pot", value=f"{self.goldEmoji} {format(int(boosterFee),',d')}", inline=True)
            embed.add_field(name="Advertiser Pot", value=f"{self.goldEmoji} {format(int(advertiserFee),',d')}", inline=True)
            embed.add_field(name="Boost", value=f"{self.boostEmoji} {boost}", inline=True)
            embed.add_field(name="Client Name", value=data['name'], inline=True)
            embed.add_field(name="Class", value=f"{data['class']} {data['active_spec_name']}", inline=True)
            embed.add_field(name="iLvl & Covenant", value=f"{data['gear']['item_level_equipped']}, {data['covenant']['name']}", inline=True)
            embed.add_field(name="Check-pvp Link", value=f"{self.linkEmoji} [{data['name']}-{data['realm']}]({check_pvp_link})", inline=True)
            if notes:
                embed.add_field(name="Notes", value=f"{self.notesEmoji} `{notes}`", inline=False)
            embed.set_footer(text=f"React with {self.moneybagEmoji} to sign up for the boost. A booster is randomly drawn within 2 minutes of posting. If no one signs within 2 minutes, the first person to sign will automatically win.")

            msg = await channel.send(content=mentions, embed=embed)

            query = """INSERT INTO pvp.booking (runid, category, advertiser, total_pot, total_pot_realm, total_pot_faction, booster_pot, advertiser_pot, boost, boost_faction, client_name, class, spec, ilvl, covenant, check_pvp_link, notes)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            values = (msg.id, category.lower(), message.author.mention, gold, goldRealm, goldFaction, boosterFee, advertiserFee, boost, data['faction'].capitalize(), data['name'], data['class'], data['active_spec_name'], data['gear']['item_level_equipped'], data['covenant']['name'], check_pvp_link, notes)
            self.dbc.insert(query, values)

            await msg.add_reaction(self.moneybagEmoji)
            await msg.add_reaction(self.cancelEmoji)

            asyncio.create_task(self.randomlyAssignBoosterCountdown(msg))

            await message.delete()

        except:
            await self.delete_message(message)
            return

        await self.client.process_commands(message)

    async def delete_message(self, message: discord.Message):
        await message.author.send(f"Please use the correct format when trying to make a booking.")
        await message.delete()

    async def randomlyAssignBoosterCountdown(self, message: discord.Message):
        await asyncio.sleep(15)

        try:
            message = await message.channel.fetch_message(message.id)
        except:
            return

        users = await message.reactions[0].users().flatten()
        users.pop(0)

        if users:
            booster = random.choice(users)
        else:
            booster = None

        query = f"""UPDATE pvp.booking
               SET timer_expired = 1
               WHERE runid = {message.id}"""
        self.dbc.insert(query)

        if booster:
            await self.setBooster(message, booster)

    async def setBooster(self, message: discord.Message, booster: discord.Member):
        query = f"""UPDATE pvp.booking
               SET booster = '{booster.mention}'
               WHERE runid = {message.id}"""
        self.dbc.insert(query)
        embed = message.embeds[0]
        embed.set_field_at(index=1, name="Booster", value=booster.mention, inline=False)

        bookingQuery = f"SELECT * FROM pvp.booking WHERE runid = '{message.id}'"
        booking = self.dbc.select(bookingQuery)

        if booking['notes']:
            index = len(embed.fields) - 1
        else:
            index = len(embed.fields)

        embed.insert_field_at(index=index, name="ID", value=f"{self.idEmoji} `{message.id}`", inline=True)
        embed.set_footer(text="")
        await message.edit(embed=embed)

        reactions = message.reactions
        for reaction in reactions[:]:
            await reaction.clear()

        await message.add_reaction(self.doneEmoji)
        await message.add_reaction(self.cancelEmoji)

        await message.channel.send(f"{booster.mention} picked as booster for {booking['advertiser']}'s run with the ID: `{message.id}`.\n"
                           f"Please remember to react with {self.doneEmoji}, {booking['advertiser']}.")

def setup(client):
    client.add_cog(BookingsPvP(client))
