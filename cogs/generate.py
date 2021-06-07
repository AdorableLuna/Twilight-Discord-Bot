import discord
import re

from cogs.maincog import Maincog
from cogs.mythicplus import Mythicplus
from discord.ext import commands

class Generate(Maincog):

    def __init__(self, client):
        Maincog.__init__(self, client)
        self.trashEmoji = "\U0001F5D1"
        self.categories = {
            "m+": {
                "name": "mplus",
                "category_id": 843473846400843797,
                "command": ("```.generate Name-Server Server-H/A 1x+15 ---k Any Any [Notes] [Extra Pings]```"
                "or"
                "```\n"
                ".generate\n"
                "Name-Server\n"
                "Server-H/A\n"
                "1x+15\n"
                "---k\n"
                "Any\n"
                "Any\n"
                "[Notes]\n"
                "[Extra Pings]```\n")
            },
            "torghast": {
                "name": "torghast",
                "category_id": 848661179768242176,
                "command": ("```.generate Name-Server Server-H/A 1xL8 ---k```"
                "or"
                "```\n"
                ".generate\n"
                "Name-Server\n"
                "Server-H/A\n"
                "1xL8\n"
                "---k```\n")
            }
        }

        self.client.loop.create_task(self.on_ready_init())

    async def on_ready_init(self):
        await self.client.wait_until_ready()
        self.bookingChannel = self.client.get_channel(843826350464696332)
        self.hordeEmoji = self.client.get_emoji(843829365799911455)
        self.allianceEmoji = self.client.get_emoji(843829376486998037)

    def check_if_pre_mplus_boost_channel(self, channel_name):
        reg = re.compile("new-mplus-\w*-boost")
        return re.match(reg, channel_name)

    def check_if_pre_torghast_boost_channel(self, channel_name):
        reg = re.compile("new-torghast-\w*-boost")
        return re.match(reg, channel_name)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if self.checkIfUserIsItself(payload.member): return
        channel = self.client.get_channel(payload.channel_id)
        if not channel: return
        if isinstance(channel, discord.DMChannel): return

        if channel == self.bookingChannel:
            if str(payload.emoji) == str(self.hordeEmoji) or str(payload.emoji) == str(self.allianceEmoji):
                await self.createNewBoostChannel(payload, channel)
                message = await channel.fetch_message(payload.message_id)
                await message.remove_reaction(payload.emoji, payload.member)
            return

        # Remove new boost channel which is only viewable by the advertiser and staff
        if str(payload.emoji) == str(self.trashEmoji):
            if self.check_if_pre_mplus_boost_channel(channel.name) or self.check_if_pre_torghast_boost_channel(channel.name):
                await channel.delete()
                return

    @commands.command()
    @commands.has_any_role("Trainee Advertiser", "Advertiser", "Management", "Council")
    async def generate(self, ctx, *args):
        channel = ctx.message.channel.name
        if self.check_if_pre_mplus_boost_channel(channel):
            await ctx.invoke(self.client.get_command("generate_mythic_plus"))
        if self.check_if_pre_torghast_boost_channel(channel):
            await ctx.invoke(self.client.get_command("generate_torghast"), ctx.args[2], ctx.args[3], ctx.args[4], ctx.args[5])

    async def createNewBoostChannel(self, payload, channel):
        guild = self.client.get_guild(payload.guild_id)
        message = await channel.fetch_message(payload.message_id)
        embed = message.embeds[0]
        boostType = embed.title.split(" ")[0].lower()

        advertiserTrainerRole = self.helper.getRole(guild, "Advertiser Trainer")
        managementRole = self.helper.getRole(guild, "Management")
        category = discord.utils.get(guild.categories, id=self.categories[boostType]["category_id"])
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            advertiserTrainerRole: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, add_reactions=False, read_message_history=True),
            managementRole: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, add_reactions=False, read_message_history=True),
            payload.member: discord.PermissionOverwrite(read_messages=True),
        }

        boost_channel = await guild.create_text_channel(f"new-{self.categories[boostType]['name']}-{'horde' if str(payload.emoji) == str(self.hordeEmoji) else 'alliance'}-boost", overwrites=overwrites, category=category)
        msg = await boost_channel.send(
        (f"{payload.member.mention}\n\n{self.categories[boostType]['command']}"

        f"Click {self.trashEmoji} to delete this channel."))
        await msg.add_reaction(self.trashEmoji)

def setup(client):
    client.add_cog(Generate(client))
