import discord
import re
import requests
import json

from cogs.maincog import Maincog
from discord.ext import commands

class ApplicationsAdvertiser(Maincog):

    def __init__(self, client):
        Maincog.__init__(self, client, whitelistedChannels = [863851581128966214])
        self.declineEmoji = "\U0000274C"
        self.client.loop.create_task(self.on_ready_init())

    async def on_ready_init(self):
        await self.client.wait_until_ready()
        self.advertiserAppsChannel = self.client.get_channel(863851614300274748)
        self.acceptEmoji = self.client.get_emoji(862363079336525824)
        self.twilightEmoji = self.client.get_emoji(862443835370897428)
        self.dotEmoji = self.client.get_emoji(863866968975867914)
        self.receivedMessage = (f"{self.twilightEmoji} **Twilight Application Received: Advertiser** {self.twilightEmoji}\n\n"

        "Thank you for choosing Twilight and applying as an Advertiser. This message serves as a confirmation that we have successfully received your application.")
        self.acceptMessage = (f"{self.twilightEmoji} **Twilight Application Accepted: Advertiser** {self.twilightEmoji}\n\n"

        "We are pleased to announce that your Advertiser application has been accepted. Down below you will find additional information about your newfound role.\n\n"

        f"{self.dotEmoji} Payouts happen every 2 weeks through in-game mail.\n"
        f"{self.dotEmoji} Twilight is a professional community and we expect our boosters and advertisers to represent the community at its best at all times. Any offensive/abusive behaviour towards buyers, other members or staff will not be tolerated.\n"
        f"{self.dotEmoji} As an advertiser you are responsible for making sure all gold is mailed or collected by a Gold Collector.\n"
        f"{self.dotEmoji} Please read <#857308467945275442>. It fully explains how to advertise all runs.\n"
        f"{self.dotEmoji} Upon making your first sale, please contact <@140899006866915329>, an Advertiser Trainee or any other Management member should you have any doubts or concerns about the process.\n"
        f"{self.dotEmoji} Please forward your gmail to <@140899006866915329> or <@152894585662603265> for booking sheet access.\n"
        f"{self.dotEmoji} Your name on our discord is the character we're sending your payments to. If you wish to alter your payment character, please open a ticket through <#862344658872959026>.\n\n"

        "The management team thanks you for choosing Twilight and welcomes you to ask any questions you may have should they arise.")
        self.declineMessage = (f"{self.twilightEmoji} **Twilight Application Declined: Advertiser** {self.twilightEmoji}\n\n"
        "We're sorry to inform you that your application as an Advertiser to the Twilight Community has been declined. If you would like to know why, please contact an Advertiser Manager. You are always welcome to re-apply again at a later stage, should you feel you have something to offer.\n"
        "Have a nice day and stay safe!")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if self.checkIfUserIsItself(payload.member): return
        if payload.channel_id != self.advertiserAppsChannel.id: return
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

        rio_link = next((field.value for field in fields if field.name == 'Raider.io Link'))

        link = re.search("([^/]+)/([^/]+)/?$", rio_link)
        realm = link.group(1)
        character = link.group(2)

        response = requests.get(f"https://raider.io/api/v1/characters/profile?region=eu&realm={realm}&name={character}")
        if response.ok:
            data = json.loads(response.content)

        twilightBoosteeRole = self.helper.getRole(guild, "Twilight Boostee")
        twilightBoosterRole = self.helper.getRole(guild, "Twilight Booster")
        advertiserRole = self.helper.getRole(guild, "Advertiser")
        traineeAdvertiserRole = self.helper.getRole(guild, "Trainee Advertiser")

        with open('access.json', 'r') as accessFile:
            access = json.load(accessFile)
            accessFile.close()

        if payload.member.mention in access['advs']['users']:
            if str(payload.emoji) == str(self.acceptEmoji):
                display_name = f"{data['name']}-{data['realm'].replace(' ', '')}"
                await author.edit(nick=display_name)

                await author.remove_roles(twilightBoosteeRole)
                await author.add_roles(twilightBoosterRole, advertiserRole, traineeAdvertiserRole)

                SPREADSHEET_ID = self.client.config["SPREADSHEET_ID"]["MAIN"]
                self.client.sheet.add(SPREADSHEET_ID, "'Applications'!R3:T", [f"{data['name']}-{data['realm'].replace(' ', '')}", data['realm'].replace(' ', ''), data['faction'].capitalize()])

                await author.send(self.acceptMessage)
                await message.delete()

            if str(payload.emoji) == str(self.declineEmoji):
                await author.send(self.declineMessage)
                await message.delete()

    @commands.Cog.listener()
    async def on_message(self, message):
        if self.checkIfUserIsItself(message.author): return
        if isinstance(message.channel, discord.DMChannel): return
        if not self.checkIfAllowedChannel(message.channel.id): return

        try:
            rio_link = re.search(r'Raider.io Link:([^\>]*)Battle Tag:', message.content).group(1).strip()
            battle_tag = re.search(r'Battle Tag:([^\>]*)Access to Allied races\?', message.content).group(1).strip()
            allied_race = re.search(r'Access to Allied races\?([^\>]*)Are you good at speaking English\? Do you know any other languages\?', message.content).group(1).strip()
            languages = re.search(r'Are you good at speaking English\? Do you know any other languages\?([^\>]*)Do you have experience advertising\?', message.content).group(1).strip()
            experience = re.search(r'Do you have experience advertising\?([^\>]*)Are you advertising for any other communities\?', message.content).group(1).strip()
            about_us = re.search(r'Are you advertising for any other communities\?([^\>]*)How did you hear about us\?', message.content).group(1).strip()
            other_communities = re.search(r'How did you hear about us\?([^\>]*)Anything else we should know\?', message.content).group(1).strip()
            anything_else = re.search(r'Anything else we should know\?([^\>]*)', message.content).group(1).strip()

            embed = discord.Embed(color=0x9c59b6)
            embed.set_author(name=f"New Advertiser Application", icon_url=str(message.author.avatar_url))
            embed.set_thumbnail(url="https://cdn.discordapp.com/icons/629729313520091146/a_c708c65e803287d010ea489dd43383be.gif?size=1024")
            embed.add_field(name="Username", value=message.author.name, inline=True)
            embed.add_field(name="Usertag", value=message.author.mention, inline=True)
            embed.add_field(name="UserID", value=message.author.id, inline=True)
            embed.add_field(name="Raider.io Link", value=rio_link.split("?")[0], inline=False)
            embed.add_field(name="Battle Tag", value=battle_tag, inline=False)
            embed.add_field(name="Access to Allied races? Yes/No", value=allied_race, inline=False)
            embed.add_field(name="Are you good at speaking English? Do you know any other languages?", value=languages, inline=False)
            embed.add_field(name="Do you have experience advertising?", value=experience, inline=False)
            embed.add_field(name="Are you advertising for any other communities?", value=about_us, inline=False)
            embed.add_field(name="How did you hear about us?", value=other_communities, inline=False)
            embed.add_field(name="Anything else we should know?", value=anything_else, inline=False)

            await message.delete()
            msg = await self.advertiserAppsChannel.send(embed=embed)
            await message.author.send(self.receivedMessage)

            await msg.add_reaction(self.acceptEmoji)
            await msg.add_reaction(self.declineEmoji)
        except:
            await self.delete_message(message)
            return

        await self.client.process_commands(message)

    async def delete_message(self, message):
        await message.author.send(f"Please use the correct format when trying to apply.")
        await message.delete()

def setup(client):
    client.add_cog(ApplicationsAdvertiser(client))
