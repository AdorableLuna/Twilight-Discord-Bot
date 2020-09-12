import discord
import json
import re

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
        self.cancelEmoji = "\U0000274C"
        self.doneEmoji = "\U00002705"
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

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if self.client.user.id == payload.user_id: return
        channel = await self.client.fetch_channel(payload.channel_id)

        if isinstance(channel, discord.DMChannel):
            message = await channel.fetch_message(payload.message_id)
            if not message.embeds: return

            if str(payload.emoji) == str(self.cancelEmoji):
                await message.delete()

            if str(payload.emoji) == str(self.doneEmoji):
                user = self.client.get_user(payload.user_id)
                guild = self.client.get_guild(config['GUILD_ID'])
                embed = message.embeds[0]
                fields = embed.fields
                type = fields[0].value
                TRUEDATA = []

                TRUEDATA.append(next((field.value for field in fields if field.name == 'Gold Pot')).replace(',', ''))
                TRUEDATA.append(next((field.value for field in fields if field.name == 'Location of the Gold')))
                TRUEDATA.append(next((field.value for field in fields if field.name == 'Faction')))
                adv = next((field.value.split(" ", 1) for field in fields if field.name == 'Advertiser'))
                b1 = next((field.value.split(" ", 1) for field in fields if field.name == 'Booster 1'))
                b2 = next((field.value.split(" ", 1) for field in fields if field.name == 'Booster 2'), "")
                b3 = next((field.value.split(" ", 1) for field in fields if field.name == 'Booster 3'), "")
                b4 = next((field.value.split(" ", 1) for field in fields if field.name == 'Booster 4'), "")

                reg_exp = r"\(([^)]+)"
                TRUEDATA.append(re.search(reg_exp, adv[1])[1])
                TRUEDATA.append(re.search(reg_exp, b1[1])[1])
                embed.set_field_at(index=len(fields) - 1, name='Advertiser', value=adv[0], inline=False)
                embed.set_field_at(index=1, name='Booster 1', value=b1[0], inline=False)

                try:
                    TRUEDATA.append(re.search(reg_exp, b2[1])[1])
                    embed.set_field_at(index=2, name='Booster 2', value=b2[0], inline=False)
                except:
                    TRUEDATA.append("")
                try:
                    TRUEDATA.append(re.search(reg_exp, b3[1])[1])
                    embed.set_field_at(index=3, name='Booster 3', value=b3[0], inline=False)
                except:
                    TRUEDATA.append("")
                try:
                    TRUEDATA.append(re.search(reg_exp, b4[1])[1])
                    embed.set_field_at(index=4, name='Booster 4', value=b4[0], inline=False)
                except:
                    TRUEDATA.append("")

                match = re.search(r'\d{2}-\d{2} \d{2}:\d{2}:\d{2}', embed.footer.text)
                created_at = match.group()

                if type != 'M+':
                    TRUEDATA.insert(3, type)
                    TRUEDATA.append(next((field.value for field in fields if field.name == 'Advertiser Cut')).replace(',', ''))
                    TRUEDATA.append(next((field.value for field in fields if field.name == 'Booster Cut')).replace(',', ''))

                TRUEDATA.append(created_at)
                id = embed.footer.text.split("Run id: ", 1)[1]
                TRUEDATA.insert(0, str(id))

                await message.delete()
                added = await self.addToSheets(guild, user, type, TRUEDATA)

                if added:
                    await self.channel.send(embed=message.embeds[0])

    @commands.command()
    async def completed(self, ctx, *args):
        if ctx.message.channel == self.channel:
            invoked = False
            await self.channel.send('This boost has been processed by our bot.', delete_after=5.0)
        else:
            invoked = True

        created_at = datetime.now(timezone('Europe/Paris')).strftime("%d-%m %H:%M:%S")
        DATA = args
        if DATA[0].islower():
            type = DATA[0].title()
        else:
            type = DATA[0]

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
        eadv = DATA[3]
        eb1 = DATA[4]
        totalBoosters = 1

        if self.helper.containsUserMention(potrealm):
            raise commands.BadArgument("Realm is not defined.")

        try:
            eb2 = DATA[5]
            totalBoosters += 1
        except:
            eb2 = ""
        try:
            eb3 = DATA[6]
            totalBoosters += 1
        except:
            eb3 = ""
        try:
            eb4 = DATA[7]
            totalBoosters += 1
        except:
            eb4 = ""

        advertiser = self.helper.checkName(ctx.guild, eadv)
        booster1 = self.helper.checkName(ctx.guild, eb1)
        if eb2:
            booster2 = self.helper.checkName(ctx.guild, eb2)
        if eb3:
            booster3 = self.helper.checkName(ctx.guild, eb3)
        if eb4:
            booster4 = self.helper.checkName(ctx.guild, eb4)

        adfee = int(pot) * (self.taxes[type.lower()]["advertiser"] / 100)
        boosterfee = int(pot) * round(((self.taxes[type.lower()]["boosters"] / 100) / totalBoosters), 3)
        guildfee = int(pot) * (self.taxes[type.lower()]["management"] / 100)
        type = type.replace('_', ' ')

        embed = discord.Embed(title=f"{type} Completed!", color=0x00ff00)
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/632628531528073249/644669381451710495/TwilightDiscIocn.jpg")
        embed.add_field(name="Type", value=type, inline=False)
        embed.add_field(name="Booster 1", value=f"{eb1} {'' if invoked else f'({booster1})'}", inline=False)
        if eb2:
            embed.add_field(name="Booster 2", value=f"{eb2} {'' if invoked else f'({booster2})'}", inline=False)
        if eb3:
            embed.add_field(name="Booster 3", value=f"{eb3} {'' if invoked else f'({booster3})'}", inline=False)
        if eb4:
            embed.add_field(name="Booster 4", value=f"{eb4} {'' if invoked else f'({booster4})'}", inline=False)
        embed.add_field(name="Gold Pot", value=format(epot,',d'), inline=False)
        embed.add_field(name="Booster Cut", value=format(int(boosterfee),',d'), inline=False)
        embed.add_field(name="Advertiser Cut", value=format(int(adfee),',d'), inline=False)
        embed.add_field(name="Guild Cut", value=format(int(guildfee),',d'), inline=False)
        embed.add_field(name="Location of the Gold", value=potrealm, inline=False)
        embed.add_field(name="Faction", value=faction, inline=False)
        embed.add_field(name="Advertiser", value=f"{eadv} {'' if invoked else f'({advertiser})'}", inline=False)
        if not invoked:
            msg = await author.send(content=f"This is a preview of the completed {type} run. Do you want to post this run?", embed=embed)
            await msg.add_reaction(self.cancelEmoji)
            await msg.add_reaction(self.doneEmoji)
        else:
            msg = await self.channel.send(embed=embed)
        embed.set_footer(text=f"Time: {created_at}\nRun id: {msg.id}")
        await msg.edit(embed=embed)

        if not invoked:
            await ctx.message.delete()

            return msg
        else:
            # If not invoked by .generate command, skip DM
            if type == 'M+':
                TRUEDATA = [str(msg.id), epot, potrealm, faction, eadv, eb1, eb2, eb3, eb4, created_at]
            else:
                TRUEDATA = [str(msg.id), epot, potrealm, faction, type, eadv, eb1, eb2, eb3, eb4, adfee, boosterfee, created_at]

            added = await self.addToSheets(ctx.guild, author, type, TRUEDATA)
            return added, msg

    async def addToSheets(self, guild, author, type, TRUEDATA):
        index = 1 if type != 'M+' else 0

        advertiserResults = self.getNameIfUserMention(guild, TRUEDATA[4 + index])
        advertiser = advertiserResults
        TRUEDATA[4 + index] = advertiserResults

        booster1Results = self.getNameIfUserMention(guild, TRUEDATA[5 + index])
        booster1 = booster1Results
        TRUEDATA[5 + index] = booster1Results

        booster2Results = self.getNameIfUserMention(guild, TRUEDATA[6 + index])
        booster2 = booster2Results
        TRUEDATA[6 + index] = booster2Results

        booster3Results = self.getNameIfUserMention(guild, TRUEDATA[7 + index])
        booster3 = booster3Results
        TRUEDATA[7 + index] = booster3Results

        booster4Results = self.getNameIfUserMention(guild, TRUEDATA[8 + index])
        booster4 = booster4Results
        TRUEDATA[8 + index] = booster4Results

        if type == 'M+':
            RANGE_NAME = "'Completed M+ Logs'!A12:K"
        else:
            RANGE_NAME = "'MISC'!A3:N"

        SPREADSHEET_ID = config["SPREADSHEET_ID"]
        allRows = sheet.getAllRows(SPREADSHEET_ID, f"{RANGE_NAME}")

        if not allRows:
            await author.send("Something went wrong with retrieving data from the sheets, please try again. If this continues please contact someone from Council or Management.")
            return False

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
                result = sheet.update(SPREADSHEET_ID, UPDATE_RANGE, TRUEDATA)
                updated = True;
                break

        # If no rows were updated, then add it
        if not updated:
            result = sheet.add(SPREADSHEET_ID, RANGE_NAME, TRUEDATA)

        if result:
            receipt = discord.Embed(title=f"{type} receipt",
                                    description=(f"{TRUEDATA[0]}\n"
                                                f"{format(int(TRUEDATA[1]),',d')}\n"
                                                f"{TRUEDATA[2]}\n"
                                                f"{TRUEDATA[3]}\n"
                                                f"{type}\n"
                                                f"{advertiser}\n"
                                                f"{booster1}\n"
                                                f"{booster2}\n"
                                                f"{booster3}\n"
                                                f"{booster4}"),
                                    color=0x00ff00)
            receipt.set_thumbnail(url="https://cdn.discordapp.com/attachments/632628531528073249/644669381451710495/TwilightDiscIocn.jpg")
            await author.send("Please copy and paste this information into the message body when sending the mail.", embed=receipt)
            return True
        else:
            await author.send("Something went wrong while adding the run to the sheets and nothing was added, please try again. If this continues please contact someone from Council or Management.")
            return False

    def getNameIfUserMention(self, guild, mention):
        try:
            if self.helper.containsUserMention(mention):
                name = self.helper.checkName(guild, mention)
            else:
                name = mention
        except:
            name = ""

        return name

    @completed.error
    async def completed_error(self, ctx, error):
        created_at = datetime.now(timezone('Europe/Paris')).strftime("%d-%m %H:%M:%S")
        await self.channel.send(f'{ctx.message.author.mention}, there was an error with your command. Please check the pins for the correct format.')
        print(f"{created_at} .completed:", error)

        return

def setup(client):
    client.add_cog(Completed(client))
