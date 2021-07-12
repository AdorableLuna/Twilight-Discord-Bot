import discord
import re
import requests
import json

from cogs.maincog import Maincog
from discord.ext import commands

class ApplicationsPvP(Maincog):

    def __init__(self, client):
        Maincog.__init__(self, client, whitelistedChannels = [864189821063921684])
        self.arenaEmoji = "\U00002694"
        self.declineEmoji = "\U0000274C"
        self.trashEmoji = "\U0001F5D1"
        self.client.loop.create_task(self.on_ready_init())

    async def on_ready_init(self):
        await self.client.wait_until_ready()
        self.pvpChannel = self.client.get_channel(864189784859344926)
        self.pvpAppsChannel = self.client.get_channel(864189821063921684)
        self.rbgEmoji = self.client.get_emoji(864190766192263168)
        self.twilightEmoji = self.client.get_emoji(862443835370897428)
        self.acceptMessage = (f"{self.twilightEmoji} **Twilight Application Accepted: PvP** {self.twilightEmoji}\n\n"

        "We are pleased to announce your that your PvP Application to Twilight has been accepted. For an introduction on how our systems work, please contact <@213003286196781056> or <@218472898124447744>.\n\n"

        "Welcome to Twilight!")
        self.declineMessage = (f"{self.twilightEmoji} **Twilight Application Declined: PvP** {self.twilightEmoji}\n\n"

        "We're sorry to say you have been declined as a PvP Booster to Twilight. If you feel the decline was unjustified, you can reach out to <@213003286196781056>.")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if self.checkIfUserIsItself(payload.member): return
        if not self.checkIfAllowedChannel(payload.channel_id): return
        channel = self.client.get_channel(payload.channel_id)
        guild = self.client.get_guild(payload.guild_id)

        message = await channel.fetch_message(payload.message_id)
        if not message.embeds: return
        embed = message.embeds[0]
        fields = embed.fields

        fake_context = discord.Object(id = 0)
        fake_context.bot = self.client
        fake_context.guild = guild
        author = next((field.value for field in fields if field.name == 'Usertag'))
        author = await self.convertMember(fake_context, author)

        url = re.search('\[.+?\]\((.*)\)', next((field.value for field in fields if field.name == 'Check-PvP Link'))).group(1)

        link = re.search("([^/]+)/([^/]+)/?$", url)
        realm = link.group(1)
        character = link.group(2)

        response = requests.get(f"https://raider.io/api/v1/characters/profile?region=eu&realm={realm}&name={character}")
        if response.ok:
            data = json.loads(response.content)

            arenaBoosterRole = self.helper.getRole(guild, f"PvP {data['faction'].capitalize()}")

        twilightBoosteeRole = self.helper.getRole(guild, "Twilight Boostee")
        pvpBoosterRole = self.helper.getRole(guild, "PvP Booster")
        rbgBoosterRole = self.helper.getRole(guild, "RBG Booster")
        twilightBoosterRole = self.helper.getRole(guild, "Twilight Booster")

        with open('access.json', 'r') as accessFile:
            access = json.load(accessFile)
            accessFile.close()

        if payload.member.mention in access['pvp']['users']:
            if str(payload.emoji) == str(self.arenaEmoji) or str(payload.emoji) == str(self.rbgEmoji):
                display_name = f"{data['name']}-{data['realm'].replace(' ', '')}"
                await author.edit(nick=display_name)

                await author.remove_roles(twilightBoosteeRole)

                if str(payload.emoji) == str(self.arenaEmoji):
                    await author.add_roles(arenaBoosterRole)
                elif str(payload.emoji) == str(self.rbgEmoji):
                    await author.add_roles(rbgBoosterRole)

                await author.add_roles(twilightBoosterRole, pvpBoosterRole)

                SPREADSHEET_ID = self.client.config["SPREADSHEET_ID"]["MAIN"]
                self.client.sheet.add(SPREADSHEET_ID, "'Applications'!F3:H", [f"{data['name']}-{data['realm'].replace(' ', '')}", data['realm'].replace(' ', ''), data['faction'].capitalize()])

                await author.send(self.acceptMessage)
                await message.delete()

            if str(payload.emoji) == str(self.trashEmoji):
                await message.delete()

            if str(payload.emoji) == str(self.declineEmoji):
                await author.send(self.declineMessage)
                await message.delete()

    @commands.Cog.listener()
    async def on_message(self, message):
        if self.checkIfUserIsItself(message.author): return
        if isinstance(message.channel, discord.DMChannel): return
        if message.channel.id != self.pvpChannel.id: return

        try:
            link = re.search("([^/]+)/([^/]+)/?$", message.content)
            realm = link.group(1)
            character = link.group(2)

            response = requests.get(f"https://raider.io/api/v1/characters/profile?region=eu&realm={realm}&name={character}&fields=gear")

            if response.ok:
                data = json.loads(response.content)

                embed = discord.Embed(color=0x9c59b6)
                embed.set_author(name=f"New PvP Application - {data['faction'].capitalize()}", icon_url=str(message.author.avatar_url))
                embed.set_thumbnail(url=data['thumbnail_url'])
                embed.add_field(name="Username", value=message.author.name, inline=True)
                embed.add_field(name="Usertag", value=message.author.mention, inline=True)
                embed.add_field(name="UserID", value=message.author.id, inline=True)
                embed.add_field(name="Check-PvP Link", value=f"[Click Here](https://check-pvp.fr/eu/{realm}/{character})", inline=True)
                embed.add_field(name="Race", value=f"{data['race']}", inline=True)
                embed.add_field(name="iLvl", value=f"{data['gear']['item_level_equipped']}", inline=True)
                embed.add_field(name="Class", value=f"{data['class']}", inline=False)

                await message.delete()
                msg = await self.pvpAppsChannel.send(embed=embed)

                await msg.add_reaction(self.arenaEmoji)
                await msg.add_reaction(self.rbgEmoji)
                await msg.add_reaction(self.trashEmoji)
                await msg.add_reaction(self.declineEmoji)
        except:
            await self.delete_message(message)
            return

        await self.client.process_commands(message)

    async def delete_message(self, message):
        await message.author.send(f"Please use the correct format when trying to apply.")
        await message.delete()

def setup(client):
    client.add_cog(ApplicationsPvP(client))
