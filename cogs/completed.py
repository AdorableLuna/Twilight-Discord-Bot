import discord
import json
import re

from discord.utils import get
from discord.ext import commands
from gsheet import *

with open('./config.json', 'r') as cjson:
    config = json.load(cjson)

sheet = gsheet()

class Completed(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command()
    async def completed(self, ctx):
        guild = self.client.get_guild(config["GUILD_ID"])
        channel = ctx.message.channel
        await channel.send('This run has been processed by our bot.', delete_after=10.0)
        SPREADSHEET_ID = config["SPREADSHEET_ID"]
        RANGE_NAME = 'B12'
        FIELDS = 7

        msg = ctx.message.content[11:]
        result = [x.strip() for x in re.split(' ', msg)]

        if len(result) == FIELDS:
            print(ctx.message.created_at)
            DATA = result
            pot = DATA[0]
            epot = int(DATA[0])
            potrealm = DATA[1]
            advertiser = DATA[2]
            eadv = DATA[2]
            booster1 = DATA[3]
            eb1 = DATA[3]
            booster2 = DATA[4]
            eb2 = DATA[4]
            booster3 = DATA[5]
            eb3 = DATA[5]
            booster4 = DATA[6]
            eb4 = DATA[6]

            advertiser = checkName(guild, advertiser)
            booster1 = checkName(guild, booster1)
            booster2 = checkName(guild, booster2)
            booster3 = checkName(guild, booster3)
            booster4 = checkName(guild, booster4)

            adfee = int(pot) * 0.173
            boosterfee = int(pot) * 0.178
            guildfee = int(pot) * 0.115

            TRUEDATA = [epot, potrealm, advertiser, booster1, booster2, booster3, booster4]

            allRows = sheet.getAllRows(SPREADSHEET_ID, f"{RANGE_NAME}:I")
            # Count starts at 11, because the first 11 rows are irrelevant
            rowCount = 11
            updated = False

            # Loop through all the 'filled' rows (rows with only a checkmark are seen as filled)
            for i in range(len(allRows)):
                rowCount += 1

                # If the encountered row is completely empty, but does have a checkmark
                if not allRows[i][0] and not allRows[i][1] and not allRows[i][2] and not allRows[i][3] and not allRows[i][4] and not allRows[i][5] and not allRows[i][6]:

                    # Update that row
                    sheet.update(SPREADSHEET_ID, f"B{rowCount}", TRUEDATA)
                    updated = True;
                    break

            # If no rows were updated, then add it
            if not updated:
                sheet.add(SPREADSHEET_ID, RANGE_NAME, TRUEDATA)

            embed = discord.Embed(title="M+ Completed!", color=0x00ff00)
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/632628531528073249/644669381451710495/TwilightDiscIocn.jpg")
            embed.add_field(name="Booster1", value=eb1, inline=False)
            embed.add_field(name="Booster2", value=eb2, inline=False)
            embed.add_field(name="Booster3", value=eb3, inline=False)
            embed.add_field(name="Booster4", value=eb4, inline=False)
            embed.add_field(name="Gold Pot", value=format(epot,',d'), inline=False)
            embed.add_field(name="Booster Cut", value=format(int(boosterfee),',d'), inline=False)
            embed.add_field(name="Advertiser Cut", value=format(int(adfee),',d'), inline=False)
            embed.add_field(name="Guild Cut", value=format(int(guildfee),',d'), inline=False)
            embed.add_field(name="Location of the Gold", value=potrealm, inline=False)
            embed.add_field(name="Advertiser", value=eadv, inline=False)
            await ctx.message.channel.send(embed=embed)
            await ctx.message.delete()
        else:
            # Needs more/less fields
            await ctx.message.channel.send(':x: The command you have entered is invalid. Please check the correct formatting in the pins. :x:', delete_after=10.0)

def checkName(guild, name):
    if name.startswith('<'):
        name = name[3:-1]

        return guild.get_member(int(name)).nick
    else:
        return name

def setup(client):
    client.add_cog(Completed(client))
