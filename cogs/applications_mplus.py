import discord
import re
import requests
import json

from cogs.maincog import Maincog
from discord.ext import commands

class ApplicationsMythicPlus(Maincog):

    def __init__(self, client):
        Maincog.__init__(self, client, whitelistedChannels = [864847086393884732])
        self.declineEmoji = "\U0000274C"
        self.referralEmoji = "\U0001F4AD"
        self.advertisementEmoji = "\U0001F4B0"
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
        self.mplusChannel = self.client.get_channel(864847052034408459)
        self.mplusAppsChannel = self.client.get_channel(864847086393884732)
        self.acceptEmoji = self.client.get_emoji(862363079336525824)
        self.tankEmoji = self.client.get_emoji(714930608266018859)
        self.healerEmoji = self.client.get_emoji(714930600267612181)
        self.dpsEmoji = self.client.get_emoji(714930578461425724)
        self.twilightEmoji = self.client.get_emoji(862443835370897428)
        self.receivedMessage = (f"{self.twilightEmoji} **Twilight Application Received: M+** {self.twilightEmoji}\n\n"

        "Thank you for choosing Twilight and applying as a M+ Booster. This message serves as a confirmation that we have successfully received your application.")
        self.acceptMessage = (f"{self.twilightEmoji} **Welcome to Twilight!** {self.twilightEmoji}\n\n"

        "After careful consideration your M+ Boosting Application has been accepted within Twilight Boosting Community.\n\n"

        "**1)** Head to <#700676105387901038> and pick your roles for any alts. Be sure to only pick alt roles that you are able to play near main level and able to trade gear in all slots.\n"
        "**2)** Go to <#662766480068182026> to learn our rules.\n"
        "**3)** We do pay-outs every 2 weeks, usually on a Friday. This is done via in game mail.\n"
        "**4)** Any offensive or abusive behaviour toward buyers, members or staff will not be tolerated.\n"
        "**5)** You can also advertise for runs and post them yourself in order to 'secure' yourself a spot into the group and benefit from our 20% fee, provided you've been accepted as an advertiser in Twilight.\n"
        "**6)** We only accept GOLD for boosts. Should you plan to accept a boost that is not paid with gold, will end with removal from the community and loss of balance.\n"
        "**7)** Once you've been entered in to our sheet and you've completed your first run, you can head to our <#701182254122270720> channel and type .balance to check your current balance.\n\n"

        "Lastly, your name in the discord should ALWAYS match the name of the character you are wanting to get paid on so we know where to send the gold! If this is not the case, please open a ticket.\n\n"

        "Happy boosting!\n\n")
        self.declineMessage = (f"{self.twilightEmoji} **Twilight Application Declined: M+** {self.twilightEmoji}\n\n"

        "We're sorry to say you have been declined as a M+ Booster to Twilight. Once you have improved your score to match our score milestones, feel free to reapply.")

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

        response = requests.get(f"https://raider.io/api/v1/characters/profile?region=eu&realm={realm}&name={character}&fields=mythic_plus_scores_by_season:current")
        if response.ok:
            data = json.loads(response.content)

            factionRole = self.helper.getRole(guild, f"Mplus {data['faction'].capitalize()}")
            classRole = self.helper.getRole(guild, data['class'])
            legendaryRole = None
            epicRole = None
            rareRole = None

            if data['faction'] == 'horde':
                if data['mythic_plus_scores_by_season'][0]['scores']['all'] >= 2200:
                    highkeyBoosterRole = self.helper.getRole(guild, f"Highkey Booster {data['faction'].capitalize()}")
                    legendaryRole = self.helper.getRole(guild, "Legendary")
                    epicRole = self.helper.getRole(guild, "Epic")
                    rareRole = self.helper.getRole(guild, "Rare")
                elif data['mythic_plus_scores_by_season'][0]['scores']['all'] >= 2000 and data['mythic_plus_scores_by_season'][0]['scores']['all'] < 2200:
                    highkeyBoosterRole = self.helper.getRole(guild, f"Highkey Booster {data['faction'].capitalize()}")
                    epicRole = self.helper.getRole(guild, "Epic")
                    rareRole = self.helper.getRole(guild, "Rare")
                elif data['mythic_plus_scores_by_season'][0]['scores']['all'] >= 1500 and data['mythic_plus_scores_by_season'][0]['scores']['all'] < 2000:
                    rareRole = self.helper.getRole(guild, "Rare")
            elif data['faction'] == 'alliance':
                if data['mythic_plus_scores_by_season'][0]['scores']['all'] >= 2200:
                    highkeyBoosterRole = self.helper.getRole(guild, f"Highkey Booster {data['faction'].capitalize()}")
                    legendaryRole = self.helper.getRole(guild, "Legendary")
                    epicRole = self.helper.getRole(guild, "Epic")
                    rareRole = self.helper.getRole(guild, "Rare")
                elif data['mythic_plus_scores_by_season'][0]['scores']['all'] >= 2000 and data['mythic_plus_scores_by_season'][0]['scores']['all'] < 2200:
                    highkeyBoosterRole = self.helper.getRole(guild, f"Highkey Booster {data['faction'].capitalize()}")
                    epicRole = self.helper.getRole(guild, "Epic")
                    rareRole = self.helper.getRole(guild, "Rare")
                elif data['mythic_plus_scores_by_season'][0]['scores']['all'] >= 1500 and data['mythic_plus_scores_by_season'][0]['scores']['all'] < 2000:
                    rareRole = self.helper.getRole(guild, "Rare")

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
        mplusBoosterRole = self.helper.getRole(guild, "Mplus Booster")

        with open('access.json', 'r') as accessFile:
            access = json.load(accessFile)
            accessFile.close()

        if payload.member.mention in access['mplus']['users']:
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
                await author.add_roles(twilightBoosterRole, mplusBoosterRole, armorRole, classRole, factionRole)

                if legendaryRole:
                    await author.add_roles(highkeyBoosterRole, legendaryRole, epicRole, rareRole)
                elif epicRole:
                    await author.add_roles(highkeyBoosterRole, epicRole, rareRole)
                elif rareRole:
                    await author.add_roles(rareRole)

                SPREADSHEET_ID = self.client.config["SPREADSHEET_ID"]["MAIN"]
                self.client.sheet.add(SPREADSHEET_ID, "'Applications'!J3:L", [f"{data['name']}-{data['realm'].replace(' ', '')}", data['realm'].replace(' ', ''), data['faction'].capitalize()])

                await author.send(self.acceptMessage)
                await message.delete()

            if str(payload.emoji) == str(self.declineEmoji):
                await author.send(self.declineMessage)
                await message.delete()

    @commands.Cog.listener()
    async def on_message(self, message):
        if self.checkIfUserIsItself(message.author): return
        if isinstance(message.channel, discord.DMChannel): return
        if message.channel.id != self.mplusChannel.id: return

        try:
            rio_link = re.search(r'Raider.io Link:([^\>]*)Did someone refer you\? If so, who\?', message.content).group(1).strip()
            referral = re.search(r'Did someone refer you\? If so, who\?([\s\S]+)Would you also like\/learn how to advertise for us\? \(20% Adv Cut\)', message.content).group(1).strip()
            advertisement = re.search(r'Would you also like\/learn how to advertise for us\? \(20% Adv Cut\)([^\>]*)', message.content).group(1).strip()

            link = re.search("([^/]+)/([^/]+)/?$", rio_link.split("?")[0])
            realm = link.group(1)
            character = link.group(2)

            response = requests.get(f"https://raider.io/api/v1/characters/profile?region=eu&realm={realm}&name={character}&fields=gear,covenant,mythic_plus_scores_by_season:current:previous")

            if response.ok:
                data = json.loads(response.content)

                embed = discord.Embed(color=0x9c59b6)
                embed.set_author(name=f"New {data['faction'].capitalize()} Mythic+ Application", icon_url=str(message.author.avatar_url))
                embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/632910453269463070.png?v=1" if data['faction'] == 'horde' else "https://cdn.discordapp.com/emojis/632910801425924106.png?v=1")
                embed.add_field(name="Username", value=message.author.name, inline=True)
                embed.add_field(name="Usertag", value=message.author.mention, inline=True)
                embed.add_field(name="UserID", value=message.author.id, inline=True)
                embed.add_field(name="Name", value=f"[{data['name']}]({data['profile_url']})", inline=True)
                embed.add_field(name="Class", value=f"{data['class']}", inline=True)
                embed.add_field(name="Covenant", value=f"{data['covenant']['name'] if data['covenant'] else 'Not found'}", inline=True)
                embed.add_field(name="Current Season", value=f"{data['mythic_plus_scores_by_season'][0]['scores']['all']}", inline=True)
                if len(data['mythic_plus_scores_by_season']) > 1:
                    embed.add_field(name="Last Season", value=f"{data['mythic_plus_scores_by_season'][1]['scores']['all']}", inline=True)
                embed.add_field(name="iLvl", value=f"{data['gear']['item_level_equipped']}", inline=True)
                if len(data['mythic_plus_scores_by_season']) == 1:
                    embed.add_field(name="\u200b", value="\u200b", inline=True)
                embed.add_field(name="Tank Score", value=f"{self.tankEmoji} {data['mythic_plus_scores_by_season'][0]['scores']['tank']}", inline=True)
                embed.add_field(name="Heal Score", value=f"{self.healerEmoji} {data['mythic_plus_scores_by_season'][0]['scores']['healer']}", inline=True)
                embed.add_field(name="DPS Score", value=f"{self.dpsEmoji} {data['mythic_plus_scores_by_season'][0]['scores']['dps']}", inline=True)
                embed.add_field(name="Referral", value=f"{self.referralEmoji} {referral}", inline=False)
                embed.add_field(name="Advertisement?", value=f"{self.advertisementEmoji} {advertisement}", inline=False)

                await message.delete()
                msg = await self.mplusAppsChannel.send(embed=embed)

                try:
                    await message.author.send(self.receivedMessage)
                except Exception:
                    pass

                await msg.add_reaction(self.acceptEmoji)
                await msg.add_reaction(self.declineEmoji)
                await msg.add_reaction(self.tankEmoji)
                await msg.add_reaction(self.healerEmoji)
                await msg.add_reaction(self.dpsEmoji)
            else:
                await message.delete()
                await message.author.send(f"Your Raider.IO profile could not be retrieved. Please apply with an existing EU profile, as Twilight is an EU community.")
        except:
            await self.delete_message(message)
            return

        await self.client.process_commands(message)

    async def delete_message(self, message):
        await message.author.send(f"Please use the correct format when trying to apply.")
        await message.delete()

def setup(client):
    client.add_cog(ApplicationsMythicPlus(client))
