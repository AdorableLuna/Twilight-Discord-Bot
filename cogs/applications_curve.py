import discord
import re
import requests
import json

from cogs.maincog import Maincog
from discord.ext import commands

class ApplicationsCurve(Maincog):

    def __init__(self, client):
        Maincog.__init__(self, client, whitelistedChannels = [862340669887610920])
        self.declineEmoji = "\U0000274C"
        self.armors = {
            "cloth": {
                "type": "Cloth",
                "classes": [
                    "Mage",
                    "Priest",
                    "Warlock",
                ],
            },
            "leather": {
                "type": "Leather",
                "classes": [
                    "Druid",
                    "Monk",
                    "Demon Hunter",
                    "Rogue",
                ],
            },
            "mail": {
                "type": "Mail",
                "classes": [
                    "Hunter",
                    "Shaman",
                ],
            },
            "plate": {
                "type": "Plate",
                "classes": [
                    "Warrior",
                    "Paladin",
                    "Death Knight",
                ],
            },
        }
        self.client.loop.create_task(self.on_ready_init())

    async def on_ready_init(self):
        await self.client.wait_until_ready()
        self.acceptEmoji = self.client.get_emoji(862363079336525824)
        self.tankEmoji = self.client.get_emoji(714930608266018859)
        self.healerEmoji = self.client.get_emoji(714930600267612181)
        self.dpsEmoji = self.client.get_emoji(714930578461425724)
        self.twilightEmoji = self.client.get_emoji(862443835370897428)
        self.acceptMessage = (f"{self.twilightEmoji} **Twilight Application Accepted: Curve** {self.twilightEmoji}\n\n"

        "After careful consideration, we have decided to accept your application to join Twilight as a Curve Booster. Down below you will find a list of things to do before you start boosting in our community.\n\n"

        "**1)** Head to <#700676105387901038> and pick your roles for potential alts. Be sure to only pick alt roles that you are able to play read main level, and is able to trade a sufficient level of gear.\n"
        "**2)** We do payouts every 2 weeks, usually on a Friday. Payouts are sent to your in-game mailbox.\n"
        "**3)** Any offensive or abusive behaviour toward buyers, members or staff will not be tolerated.\n"
        "**4)** You can also advertise for runs and post them yourself in order to 'secure' yourself a spot into the group and benefit from our 20% Advertisement Fee. Talk to an Advertisement Manager to get started!\n"
        "**5)** We only accept GOLD as boost payments. Should you plan to accept a boost that is not paid with gold, you will be removed from the community and forfeit your remaining balance.\n"
        "**6)** Once you have completed your first run, simply head over to <#701182254122270720> and type .balance to check your current balance.\n\n"

        "Last but not least, Welcome to Twilight!")
        self.declineMessage = (f"{self.twilightEmoji} **Twilight Application Declined: Curve** {self.twilightEmoji}\n\n"

        "We're sorry to inform you that we have declined your Curve Application over at Twilight. Feel free to re-apply when your logs increased sufficiently in regards to the requirements.")

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

        url = re.search('\[.+?\]\((.*)\)', next((field.value for field in fields if field.name == 'Name'))).group(1)

        link = re.search("([^/]+)/([^/]+)/?$", url)
        realm = link.group(1)
        character = link.group(2)

        response = requests.get(f"https://raider.io/api/v1/characters/profile?region=eu&realm={realm}&name={character}")
        if response.ok:
            data = json.loads(response.content)

            curveRole = self.helper.getRole(guild, f"SoD Curve {data['faction'].capitalize()}")
            classRole = self.helper.getRole(guild, data['class'])

            for key, value in self.armors.items():
                for playerClass in value['classes']:
                    if playerClass == data['class']:
                        armorRole = self.helper.getRole(guild, value['type'])
                        break

        tankRole = self.helper.getRole(guild, "Tank")
        healerRole = self.helper.getRole(guild, "Healer")
        dpsRole = self.helper.getRole(guild, "Damage")
        twilightBoosteeRole = self.helper.getRole(guild, "Twilight Boostee")
        twilightBoosterRole = self.helper.getRole(guild, "Twilight Booster")
        twilightRaidBoosterRole = self.helper.getRole(guild, "Twilight Raid Booster")

        with open('access.json', 'r') as accessFile:
            access = json.load(accessFile)
            accessFile.close()

        if payload.member.mention in access['curves']['users']:
            if str(payload.emoji) == str(self.tankEmoji):
                await author.add_roles(tankRole)

            if str(payload.emoji) == str(self.healerEmoji):
                await author.add_roles(healerRole)

            if str(payload.emoji) == str(self.dpsEmoji):
                await author.add_roles(dpsRole)

            if str(payload.emoji) == str(self.acceptEmoji):
                display_name = f"{data['name']}-{data['realm'].replace(' ', '')}"
                await author.edit(nick=display_name)

                await author.remove_roles(twilightBoosteeRole)
                await author.add_roles(twilightBoosterRole, twilightRaidBoosterRole, armorRole, classRole, curveRole)

                SPREADSHEET_ID = self.client.config["SPREADSHEET_ID"]["MAIN"]
                self.client.sheet.add(SPREADSHEET_ID, "'Applications'!N3:P", [f"{data['name']}-{data['realm'].replace(' ', '')}", data['realm'].replace(' ', ''), data['faction'].capitalize()])

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
            link = re.search("([^/]+)/([^/]+)/?$", message.content)
            realm = link.group(1)
            character = link.group(2)

            response = requests.get(f"https://raider.io/api/v1/characters/profile?region=eu&realm={realm}&name={character}&fields=covenant,raid_progression,mythic_plus_scores_by_season:current")

            if response.ok:
                data = json.loads(response.content)
                currentRaid = list(data['raid_progression'].keys())[-1]

                embed = discord.Embed(color=0x9c59b6)
                embed.set_author(name=f"{data['faction'].capitalize()} Curve Application", icon_url=str(message.author.avatar_url))
                embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/632910453269463070.png?v=1" if data['faction'] == 'horde' else "https://cdn.discordapp.com/emojis/632910801425924106.png?v=1")
                embed.add_field(name="Username", value=message.author.name, inline=True)
                embed.add_field(name="Usertag", value=message.author.mention, inline=True)
                embed.add_field(name="UserID", value=message.author.id, inline=True)
                embed.add_field(name="Name", value=f"[{data['name']}]({data['profile_url']})", inline=True)
                embed.add_field(name="Class", value=f"{data['class']}", inline=True)
                embed.add_field(name="Covenant", value=f"{data['covenant']['name']}", inline=True)
                embed.add_field(name="Mythic", value=f"{data['raid_progression'][currentRaid]['mythic_bosses_killed']}/{data['raid_progression'][currentRaid]['total_bosses']}", inline=True)
                embed.add_field(name="Heroic", value=f"{data['raid_progression'][currentRaid]['heroic_bosses_killed']}/{data['raid_progression'][currentRaid]['total_bosses']}", inline=True)
                embed.add_field(name="Logs", value=f"[Click](https://www.warcraftlogs.com/character/eu/{realm}/{character})", inline=True)
                embed.add_field(name="\u200b", value=f"{self.tankEmoji} {data['mythic_plus_scores_by_season'][0]['scores']['tank']}", inline=True)
                embed.add_field(name="\u200b", value=f"{self.healerEmoji} {data['mythic_plus_scores_by_season'][0]['scores']['healer']}", inline=True)
                embed.add_field(name="\u200b", value=f"{self.dpsEmoji} {data['mythic_plus_scores_by_season'][0]['scores']['dps']}", inline=True)

                await message.delete()
                msg = await message.channel.send(embed=embed)

                await msg.add_reaction(self.acceptEmoji)
                await msg.add_reaction(self.declineEmoji)
                await msg.add_reaction(self.tankEmoji)
                await msg.add_reaction(self.healerEmoji)
                await msg.add_reaction(self.dpsEmoji)
        except:
            await self.delete_message(message)
            return

        await self.client.process_commands(message)

    async def delete_message(self, message):
        await message.author.send(f"Please use the correct format when trying to apply.")
        await message.delete()

def setup(client):
    client.add_cog(ApplicationsCurve(client))
