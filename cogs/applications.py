import discord
import requests
import json

from cogs.maincog import Maincog
from discord.ext import commands

class Applications(Maincog):

    def __init__(self, client):
        Maincog.__init__(self, client, whitelistedChannels = [740272368211066981, 740272404416430100],
                                       whitelistedUsers = [152894585662603265])
        self.legendaryEmoji = "\U0001F7E7"
        self.epicEmoji = "\U0001F7EA"
        self.rareEmoji = "\U0001F7E6"
        self.declineEmoji = "\U0000274C"
        self.client.loop.create_task(self.on_ready_init())

    async def on_ready_init(self):
        await self.client.wait_until_ready()
        self.twilightEmoji = self.client.get_emoji(740282389682454540)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if self.checkIfUserIsItself(payload.member): return
        if not self.checkIfAllowedChannel(payload.channel_id): return
        channel = self.client.get_channel(payload.channel_id)
        guild = self.client.get_guild(payload.guild_id)

        if "horde" in channel.name:
            faction = "Horde"
        elif "alliance" in channel.name:
            faction = "Alliance"

        message = await channel.fetch_message(payload.message_id)
        userRoles = payload.member.roles
        councilRole = self.helper.getRole(guild, "Council")
        legendaryRole = self.helper.getRole(guild, "Legendary")
        epicRole = self.helper.getRole(guild, "Epic")
        rareRole = self.helper.getRole(guild, "Rare")
        highKeyRole = self.helper.getRole(guild, f"Highkey Booster {faction}")
        mplusBoosterFactionRole = self.helper.getRole(guild, f"Mplus {faction}")
        mplusBoosterRole = self.helper.getRole(guild, "Mplus Booster")
        boosteeRole = self.helper.getRole(guild, "Twilight Boostee")
        boosterRole = self.helper.getRole(guild, "Twilight Booster")

        if councilRole in userRoles:
            if str(payload.emoji) == str(self.legendaryEmoji) or str(payload.emoji) == str(self.epicEmoji) or str(payload.emoji) == str(self.rareEmoji):
                await message.author.remove_roles(boosteeRole)
                await message.author.add_roles(boosterRole, mplusBoosterRole, mplusBoosterFactionRole)

                acceptedMessage = (f"{self.twilightEmoji} **Welcome to Twilight!** {self.twilightEmoji}\n\n"

                "After careful consideration your M+ Boosting Application has been accepted within Twilight Boosting Community.\n\n"

                "**1)** Head to <#700676105387901038> and pick your roles. Be sure to only pick alt roles that you are able to play near main level and able to trade 210+ gear in all slots.\n"
                "**2)** Go to <#662766480068182026> to learn our rules.\n"
                "**3)** We do pay-outs every 2 weeks, usually on a Friday. This is done via in game mail.\n"
                "**4)** Any offensive or abusive behaviour toward buyers, members or staff will not be tolerated.\n"
                "**5)** You can also advertise for runs and post them yourself in order to 'secure' yourself a spot into the group and benefit from our 17.3% fee, provided you've been accepted as an advertiser in Twilight.\n"
                "**6)** We only accept GOLD for boosts. Should you plan to accept a boost that is not paid with gold, will end with removal from the community and loss of balance.\n"
                "**7)** Once you've been entered in to our sheet and you've completed your first run, you can head to our <#701182254122270720> channel and type .balance to check your current balance. M+ runs can take up to 24-48 hours to process before it's added to your balance.\n\n"

                "Lastly, your name in the discord should ALWAYS match the name of the character you are wanting to get paid on so we know where to send the gold! If this is not the case, please open a ticket.\n\n"

                "Happy boosting!")

                if str(payload.emoji) == str(self.legendaryEmoji):
                    await message.author.add_roles(rareRole, epicRole, legendaryRole, highKeyRole)

                if str(payload.emoji) == str(self.epicEmoji):
                    await message.author.add_roles(rareRole, epicRole, highKeyRole)

                if str(payload.emoji) == str(self.rareEmoji):
                    await message.author.add_roles(rareRole)

                nameRealm = message.content.splitlines()[0].replace(" ", "").split(":", 1)[1].split("-")
                name = nameRealm[0].title()
                realm = nameRealm[1].title()

                link = f"https://raider.io/api/v1/characters/profile?region=eu&realm={realm}&name={name}"

                response = requests.get(link)

                if response.ok:
                    data = json.loads(response.content)
                    realm = data["realm"].replace(" ", "")

                display_name = f"{name}-{realm}"

                await message.author.edit(nick=display_name)
                await message.author.send(acceptedMessage)

            if str(payload.emoji) == str(self.declineEmoji):
                declineMessage = ("Unfortunately after processing your application, we've come to the decision that you're not suitable to boost Mythic Plus with the <Twilight Community>.\n\n"

                "Feel free to apply again once you meet the requirements. Contact anyone from management or simply open a support ticket for further inquiries.")

                await message.author.send(declineMessage)

    @commands.Cog.listener()
    async def on_message(self, message):
        if isinstance(message.channel, discord.DMChannel): return
        if not self.checkIfAllowedChannel(message.channel.id): return
        if self.checkIfAllowedUser(message.author.id): return

        if not len(message.content.splitlines()) >= 4:
            await self.delete_message(message)
            return

        try:
            nameRealm = message.content.splitlines()[0].replace(" ", "").split(":", 1)[1].split("-")
            name = nameRealm[0].title()
            realm = nameRealm[1].title()
        except:
            await self.delete_message(message)
            return

        await message.add_reaction(self.legendaryEmoji)
        await message.add_reaction(self.epicEmoji)
        await message.add_reaction(self.rareEmoji)
        await message.add_reaction(self.declineEmoji)

        await self.client.process_commands(message)

    async def delete_message(self, message):
        await message.author.send(f"Please use the correct format given in the pins when trying to apply.")
        await message.delete()

def setup(client):
    client.add_cog(Applications(client))
