import discord
import json

from helpers import helper
from discord.ext import commands
from datetime import datetime
from pytz import timezone
from gsheet import *

with open('./config.json', 'r') as cjson:
    config = json.load(cjson)

sheet = gsheet()

class Completed(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.helper = helper.Helper(self.client)
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
                "boosters": 75,
                "advertiser": 15,
                "management": 10
            },
            "vision": {
                "boosters": 75,
                "advertiser": 15,
                "management": 10
            },
            "duo": {
                "boosters": 71.2,
                "advertiser": 17.3,
                "management": 11.5
            }
        }

    @commands.command()
    async def completed(self, ctx, *args):
        if ctx.message.channel == self.channel:
            await self.channel.send('This boost has been processed by our bot.', delete_after=5.0)

        created_at = datetime.now(timezone('Europe/Paris')).strftime("%d-%m %H:%M:%S")
        DATA = args
        if DATA[0].islower():
            type = DATA[0].title()
        else:
            type = DATA[0]

        SPREADSHEET_ID = config["SPREADSHEET_ID"]
        if type == 'M+':
            RANGE_NAME = "'Completed M+ Logs'!A12:K"
        else:
            RANGE_NAME = "'MISC'!A3:N"

        pot = DATA[1].lower()

        if "k" in pot:
            pot = pot.replace('k', '')
            pot = str(pot) + "000"
        else:
            pot = DATA[1]
        epot = int(pot)

        realmFaction = DATA[2].split("-", 1)
        try:
            potrealm = realmFaction[0]
            faction = "Horde" if realmFaction[1].lower() == 'h' else 'Alliance'
        except:
            raise commands.BadArgument("Realm or faction is not defined.")

        author = ctx.author
        advertiser = DATA[3]
        eadv = DATA[3]
        booster1 = DATA[4]
        eb1 = DATA[4]
        totalBoosters = 1

        if self.helper.containsUserMention(potrealm):
            raise commands.BadArgument("Realm is not defined.")

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

        advertiser = self.helper.checkName(ctx.guild, advertiser)
        booster1 = self.helper.checkName(ctx.guild, booster1)
        if booster2:
            booster2 = self.helper.checkName(ctx.guild, booster2)
        if booster3:
            booster3 = self.helper.checkName(ctx.guild, booster3)
        if booster4:
            booster4 = self.helper.checkName(ctx.guild, booster4)

        adfee = int(pot) * (self.taxes[type.lower()]["advertiser"] / 100)
        boosterfee = int(pot) * round(((self.taxes[type.lower()]["boosters"] / 100) / totalBoosters), 3)
        guildfee = int(pot) * (self.taxes[type.lower()]["management"] / 100)
        type = type.replace('_', ' ')

        if type == 'M+':
            TRUEDATA = [epot, potrealm, faction, advertiser, booster1, booster2, booster3, booster4, created_at]
        else:
            TRUEDATA = [epot, potrealm, faction, type, advertiser, booster1, booster2, booster3, booster4, adfee, boosterfee, created_at]

        allRows = sheet.getAllRows(SPREADSHEET_ID, f"{RANGE_NAME}")

        embed = discord.Embed(title=f"{type} Completed!", color=0x00ff00)
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/632628531528073249/644669381451710495/TwilightDiscIocn.jpg")
        embed.add_field(name="Type", value=type, inline=False)
        embed.add_field(name="Booster 1", value=eb1, inline=False)
        if booster2:
            embed.add_field(name="Booster 2", value=eb2, inline=False)
        if booster3:
            embed.add_field(name="Booster 3", value=eb3, inline=False)
        if booster4:
            embed.add_field(name="Booster 4", value=eb4, inline=False)
        embed.add_field(name="Gold Pot", value=format(epot,',d'), inline=False)
        embed.add_field(name="Booster Cut", value=format(int(boosterfee),',d'), inline=False)
        embed.add_field(name="Advertiser Cut", value=format(int(adfee),',d'), inline=False)
        embed.add_field(name="Guild Cut", value=format(int(guildfee),',d'), inline=False)
        embed.add_field(name="Location of the Gold", value=potrealm, inline=False)
        embed.add_field(name="Faction", value=faction, inline=False)
        embed.add_field(name="Advertiser", value=eadv, inline=False)
        msg = await self.channel.send(embed=embed)
        embed.set_footer(text=f"Run id: {msg.id}.")
        await msg.edit(embed=embed)
        if ctx.message.channel == self.channel:
            await ctx.message.delete()

        TRUEDATA.insert(0, str(msg.id))

        # Count starts at 11 or 2, because the first 11 or 2 rows are irrelevant
        rowCount = 11 if type == 'M+' else 2
        updated = False

        # Loop through all the 'filled' rows (rows with only a checkmark are seen as filled)
        for i in range(len(allRows)):
            rowCount += 1

            if type == 'M+':
                UPDATE_RANGE = f"'Completed M+ Logs'!A{rowCount}"
                emptyRow = (not allRows[i] or not allRows[i][0] and not allRows[i][1] and not allRows[i][2] and not allRows[i][3] and not allRows[i][4] and not allRows[i][5]
                    and not allRows[i][6] and not allRows[i][7] and not allRows[i][8] and not allRows[i][9])
            else:
                UPDATE_RANGE = f"'MISC'!A{rowCount}"
                emptyRow = (not allRows[i] or not allRows[i][0] and not allRows[i][1] and not allRows[i][2] and not allRows[i][3] and not allRows[i][4] and not allRows[i][5]
                    and not allRows[i][6] and not allRows[i][7] and not allRows[i][8] and not allRows[i][9] and not allRows[i][10] and not allRows[i][11] and not allRows[i][12])

            # If the encountered row is completely empty, but does have a checkmark
            if emptyRow:

                # Update that row
                sheet.update(SPREADSHEET_ID, UPDATE_RANGE, TRUEDATA)
                updated = True;
                break

        # If no rows were updated, then add it
        if not updated:
            sheet.add(SPREADSHEET_ID, RANGE_NAME, TRUEDATA)

        receipt = discord.Embed(title=f"{type} receipt",
                                description=(f"{msg.id}\n"
                                            f"{format(epot,',d')}\n"
                                            f"{potrealm}\n"
                                            f"{faction}\n"
                                            f"{type}\n"
                                            f"{advertiser}\n"
                                            f"{booster1}\n"
                                            f"{booster2 if booster2 else ''}\n"
                                            f"{booster3 if booster3 else ''}\n"
                                            f"{booster4 if booster4 else ''}"),
                                color=0x00ff00)
        receipt.set_thumbnail(url="https://cdn.discordapp.com/attachments/632628531528073249/644669381451710495/TwilightDiscIocn.jpg")
        await author.send("Please copy and paste this information into the message body when sending the mail.", embed=receipt)

        return msg

    @completed.error
    async def completed_error(self, ctx, error):
        created_at = datetime.now(timezone('Europe/Paris')).strftime("%d-%m %H:%M:%S")
        await self.channel.send(f'{ctx.message.author.mention}, there was an error with your command. Please check the pins for the correct format.')
        print(f"{created_at} .completed:", error)

        return

def setup(client):
    client.add_cog(Completed(client))
