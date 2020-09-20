import discord
import json

from cogs.maincog import Maincog
from discord.ext import commands
from gsheet import *

sheet = gsheet()

with open('./config.json', 'r') as cjson:
    config = json.load(cjson)

class Balance(Maincog):

    def __init__(self, client):
        Maincog.__init__(self, client, whitelistedChannels = [756884303580758086])

    @commands.command()
    async def balance(self, ctx):
        if not self.checkIfAllowedChannel(ctx.channel.id): return
        if isinstance(ctx.message.channel, discord.DMChannel):
            await ctx.message.channel.send("This feature is, sadly, not supported. Type the command in the correct channel and I will DM your balance.")
            return

        embed = discord.Embed(color=0x3090d9, title="Balance Check")
        embed.description = "Please check private messages for balance details."
        await ctx.message.channel.send(embed=embed)

        author = ctx.message.author
        SPREADSHEET_ID = config["SPREADSHEET_ID"]
        allRows = sheet.getAllRows(SPREADSHEET_ID, "'Balance'!A2:D")

        if not allRows:
            await author.send("Something went wrong with retrieving data from the sheets, please try again. If this continues please contact someone from Council or Management.")
            return

        for i in range(len(allRows)):
            if not allRows[i]: continue
            if allRows[i][0] == author.display_name:
                try:
                    balance = allRows[i][3]
                except:
                    balance = 0

                balanceEmbed = discord.Embed(color=0x3090d9, title="Balance Information")
                balanceEmbed.add_field(name="Current Balance", value=balance)

                await author.send(embed=balanceEmbed)
                return

        print(f"Couldn't retrieve balance of {author.display_name}")
        await author.send("Your balance could not be retrieved. Please message someone from Council or Management.")

def setup(client):
    client.add_cog(Balance(client))
