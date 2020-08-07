import discord
import json

from helpers import helper
from discord.ext import commands
from gsheet import *

with open('./config.json', 'r') as cjson:
    config = json.load(cjson)

sheet = gsheet()

class Completed(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.helper = helper.Helper(self.client)
        self.guild = self.client.get_guild(config["GUILD_ID"])
        self.channel = self.client.get_channel(731479403862949928)
        self.taxes = {
            "m+": {
                "boosters": 71.2,
                "advertiser": 17.3,
                "management": 11.5
            },
            "pvp": {
                "boosters": 80,
                "advertiser": 10,
                "management": 10
            },
            "glad_pvp": {
                "boosters": 85,
                "advertiser": 7.5,
                "management": 7.5
            },
            "leveling": {
                "boosters": 80,
                "advertiser": 10,
                "management": 10
            },
            "ie": {
                "boosters": 80,
                "advertiser": 10,
                "management": 10
            },
            "legacy": {
                "boosters": 80,
                "advertiser": 10,
                "management": 10
            },
            "mount": {
                "boosters": 70,
                "advertiser": 18.5,
                "management": 11.5
            },
            "vision": {
                "boosters": 75,
                "advertiser": 15,
                "management": 10
            }
        }

    @commands.command()
    async def completed(self, ctx, *args):
        if ctx.message.channel == self.channel:
            await self.channel.send('This boost has been processed by our bot.', delete_after=5.0)

        print(ctx.message.created_at)
        DATA = args
        if DATA[0].islower():
            type = DATA[0].title()
        else:
            type = DATA[0]

        SPREADSHEET_ID = config["SPREADSHEET_ID"]
        if type == 'M+':
            RANGE_NAME = "'Completed M+ Logs'!B12:I"
        else:
            RANGE_NAME = "'MISC'!B3:I"

        pot = DATA[1].lower()

        if "k" in pot:
            pot = pot.replace('k', '')
            pot = str(pot) + "000"
        else:
            pot = DATA[1]
        epot = int(pot)

        potrealm = DATA[2]
        advertiser = DATA[3]
        eadv = DATA[3]
        booster1 = DATA[4]
        eb1 = DATA[4]
        totalBoosters = 1
        try:
            booster2 = DATA[5]
            eb2 = DATA[5]
            totalBoosters += 1
        except:
            booster2 = ""
        try:
            booster3 = DATA[6]
            eb3 = DATA[6]
            totalBoosters += 1
        except:
            booster3 = ""
        try:
            booster4 = DATA[7]
            eb4 = DATA[7]
            totalBoosters += 1
        except:
            booster4 = ""

        advertiser = self.helper.checkName(advertiser)
        booster1 = self.helper.checkName(booster1)
        if booster2:
            booster2 = self.helper.checkName(booster2)
        if booster3:
            booster3 = self.helper.checkName(booster3)
        if booster4:
            booster4 = self.helper.checkName(booster4)

        adfee = int(pot) * (self.taxes[type.lower()]["advertiser"] / 100)
        boosterfee = int(pot) * round(((self.taxes[type.lower()]["boosters"] / 100) / totalBoosters), 3)
        guildfee = int(pot) * (self.taxes[type.lower()]["management"] / 100)
        type = type.replace('_', ' ')

        if type == 'M+':
            TRUEDATA = [epot, potrealm, advertiser, booster1, booster2, booster3, booster4]
        else:
            TRUEDATA = [type, epot, potrealm, advertiser, booster1, booster2, booster3, booster4]

        allRows = sheet.getAllRows(SPREADSHEET_ID, f"{RANGE_NAME}")
        # Count starts at 11 or 2, because the first 11 or 2 rows are irrelevant
        rowCount = 11 if type == 'M+' else 2
        updated = False

        # Loop through all the 'filled' rows (rows with only a checkmark are seen as filled)
        for i in range(len(allRows)):
            rowCount += 1

            # If the encountered row is completely empty, but does have a checkmark
            if not allRows[i] or not allRows[i][0] and not allRows[i][1] and not allRows[i][2] and not allRows[i][3] and not allRows[i][4] and not allRows[i][5] and not allRows[i][6]:
                if type == 'M+':
                    UPDATE_RANGE = f"'Completed M+ Logs'!B{rowCount}"
                else:
                    UPDATE_RANGE = f"'MISC'!B{rowCount}"

                # Update that row
                sheet.update(SPREADSHEET_ID, UPDATE_RANGE, TRUEDATA)
                updated = True;
                break

        # If no rows were updated, then add it
        if not updated:
            sheet.add(SPREADSHEET_ID, RANGE_NAME, TRUEDATA)

        embed = discord.Embed(title=f"{type} Completed!", color=0x00ff00)
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/632628531528073249/644669381451710495/TwilightDiscIocn.jpg")
        embed.add_field(name="Type", value=type, inline=False)
        embed.add_field(name="Booster1", value=eb1, inline=False)
        if booster2:
            embed.add_field(name="Booster2", value=eb2, inline=False)
        if booster3:
            embed.add_field(name="Booster3", value=eb3, inline=False)
        if booster4:
            embed.add_field(name="Booster4", value=eb4, inline=False)
        embed.add_field(name="Gold Pot", value=format(epot,',d'), inline=False)
        embed.add_field(name="Booster Cut", value=format(int(boosterfee),',d'), inline=False)
        embed.add_field(name="Advertiser Cut", value=format(int(adfee),',d'), inline=False)
        embed.add_field(name="Guild Cut", value=format(int(guildfee),',d'), inline=False)
        embed.add_field(name="Location of the Gold", value=potrealm, inline=False)
        embed.add_field(name="Advertiser", value=eadv, inline=False)
        msg = await self.channel.send(embed=embed)
        if ctx.message.channel == self.channel:
            await ctx.message.delete()

        return msg

def setup(client):
    client.add_cog(Completed(client))
