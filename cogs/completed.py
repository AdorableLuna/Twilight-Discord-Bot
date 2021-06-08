import discord
import json
import re

from cogs.maincog import Maincog
from discord.ext import commands
from datetime import datetime
from pytz import timezone

class Completed(Maincog):

    def __init__(self, client):
        Maincog.__init__(self, client, whitelistedChannels = [731479403862949928])
        self.cancelEmoji = "\U0000274C"
        self.doneEmoji = "\U00002705"

        with open('taxes.json', 'r') as taxesFile:
            self.taxes = json.load(taxesFile)
            taxesFile.close()

        self.client.loop.create_task(self.on_ready_init())

    async def on_ready_init(self):
        await self.client.wait_until_ready()
        self.channel = self.client.get_channel(731479403862949928)

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
                guild = self.client.get_guild(self.client.config['GUILD_ID'])
                embed = message.embeds[0]
                fields = embed.fields
                type = fields[0].value
                match = re.search(r'\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2}', embed.footer.text)
                fake_context = discord.Object(id = 0)
                fake_context.bot = self.client
                fake_context.guild = guild

                id = embed.footer.text.split("Run id: ", 1)[1]
                pot = next((field.value for field in fields if field.name == 'Gold Pot')).replace(',', '')
                goldRealmFaction = next((field.value for field in fields if field.name == 'Location of the Gold')).split("-")
                goldRealm = goldRealmFaction[0]
                goldFaction = goldRealmFaction[1]
                boostFaction = next((field.value for field in fields if field.name == 'Faction of the Boost'))
                advertiser = next((field.value.split(" ", 1) for field in fields if field.name == 'Advertiser'))[0]
                booster1 = next((field.value.split(" ", 1) for field in fields if field.name == 'Booster 1'))[0]
                try:
                    booster2 = next((field.value.split(" ", 1) for field in fields if field.name == 'Booster 2'), "")[0]
                    embed.set_field_at(index=2, name='Booster 2', value=booster2, inline=False)
                    booster2 = await self.convertMember(fake_context, booster2)
                except:
                    booster2 = None
                try:
                    booster3 = next((field.value.split(" ", 1) for field in fields if field.name == 'Booster 3'), "")[0]
                    embed.set_field_at(index=3, name='Booster 3', value=booster3, inline=False)
                    booster3 = await self.convertMember(fake_context, booster3)
                except:
                    booster3 = None
                try:
                    booster4 = next((field.value.split(" ", 1) for field in fields if field.name == 'Booster 4'), "")[0]
                    embed.set_field_at(index=4, name='Booster 4', value=booster4, inline=False)
                    booster4 = await self.convertMember(fake_context, booster4)
                except:
                    booster4 = None
                try:
                    keyholder = next((field.value.split(" ", 1) for field in fields if field.name == 'Keyholder'), "")[0]
                    embed.set_field_at(index=5, name='Keyholder', value=keyholder, inline=False)
                    keyholder = await self.convertMember(fake_context, keyholder)
                except:
                    keyholder = None
                advertiserFee = next((field.value for field in fields if field.name == 'Advertiser Cut')).replace(',', '')
                boosterFee = next((field.value for field in fields if field.name == 'Booster Cut')).replace(',', '')
                managementFee = next((field.value for field in fields if field.name == 'Management Cut')).replace(',', '')
                created_at = match.group()

                embed.set_field_at(index=len(fields) - 1, name='Advertiser', value=advertiser, inline=False)
                embed.set_field_at(index=1, name='Booster 1', value=booster1, inline=False)
                advertiser = await self.convertMember(fake_context, advertiser)
                booster1 = await self.convertMember(fake_context, booster1)

                completedRun = {
                    "id": id,
                    "type": type,
                    "pot": pot,
                    "goldRealm": goldRealm,
                    "goldFaction": goldFaction,
                    "boostFaction": boostFaction,
                    "advertiser": advertiser,
                    "booster1": booster1,
                    "booster2": booster2,
                    "booster3": booster3,
                    "booster4": booster4,
                    "keyholder": keyholder,
                    "advertiserFee": advertiserFee,
                    "boosterFee": boosterFee,
                    "managementFee": managementFee,
                    "created_at": created_at,
                }

                await message.delete()
                added = await self.addToSheets(guild, user, completedRun)

                if added:
                    await self.channel.send(embed=message.embeds[0])

    @commands.command()
    async def completed(self, ctx, type: str, boostFaction: str, pot: str, goldRealmFaction: str, advertiser: discord.Member, booster1: discord.Member,
                        booster2: discord.Member = None, booster3: discord.Member = None, booster4: discord.Member = None, keyholder: discord.Member = None):
        if ctx.message.channel == self.channel:
            invoked = False
            await self.channel.send('This boost has been processed by our bot.', delete_after=5.0)
        else:
            invoked = True

        # Manual inline converting because of invoked command.
        if advertiser and not isinstance(advertiser, discord.Member):
            advertiser = await self.convertMember(ctx, advertiser)
        if booster1 and not isinstance(booster1, discord.Member):
            booster1 = await self.convertMember(ctx, booster1)
        if booster2 and not isinstance(booster2, discord.Member):
            booster2 = await self.convertMember(ctx, booster2)
        if booster3 and not isinstance(booster3, discord.Member):
            booster3 = await self.convertMember(ctx, booster3)
        if booster4 and not isinstance(booster4, discord.Member):
            booster4 = await self.convertMember(ctx, booster4)
        if keyholder and not isinstance(keyholder, discord.Member):
            keyholder = await self.convertMember(ctx, keyholder)

        created_at = datetime.now(timezone('Europe/Paris')).strftime("%d-%m-%Y %H:%M:%S")
        type = type.title()
        boostFaction = boostFaction.capitalize()
        pot = pot.lower()

        if "k" in pot:
            pot = pot.replace('k', '')
            pot = str(pot) + "000"
        pot = int(pot)

        goldRealmFaction = goldRealmFaction.rsplit("-", 1)
        try:
            goldRealm = goldRealmFaction[0]
            goldFaction = "Horde" if goldRealmFaction[1].lower() == 'h' else 'Alliance'
        except:
            raise commands.BadArgument("Realm or faction is not defined.")

        totalBoosters = 1

        if booster2:
            totalBoosters += 1
        if booster3:
            totalBoosters += 1
        if booster4:
            totalBoosters += 1

        adfee = int(pot) * (self.taxes[type.lower()]["advertiser"] / 100)
        boosterfee = int(pot) * round(((self.taxes[type.lower()]["boosters"] / 100) / totalBoosters), 3)
        managementfee = int(pot) * (self.taxes[type.lower()]["management"] / 100)

        if type == "M+":
            keyholderfee = int(pot) * (self.taxes[type.lower()]["keyholder"] / 100)

        type = type.replace('_', ' ')

        embed = discord.Embed(title=f"{type} Completed!", color=0x9013FE)
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/699709321180741642/842730940744466452/Final_Logo_Render.png")
        embed.add_field(name="Type", value=type, inline=False)
        embed.add_field(name="Booster 1", value=f"{booster1.mention} {'' if invoked else f'({booster1.display_name})'}", inline=False)
        if booster2:
            embed.add_field(name="Booster 2", value=f"{booster2.mention} {'' if invoked else f'({booster2.display_name})'}", inline=False)
        if booster3:
            embed.add_field(name="Booster 3", value=f"{booster3.mention} {'' if invoked else f'({booster3.display_name})'}", inline=False)
        if booster4:
            embed.add_field(name="Booster 4", value=f"{booster4.mention} {'' if invoked else f'({booster4.display_name})'}", inline=False)
        if type == 'M+':
            embed.add_field(name="Keyholder", value=f"{keyholder.mention} {'' if invoked else f'({keyholder.display_name})'}", inline=False)
        embed.add_field(name="Gold Pot", value=format(pot,',d'), inline=False)
        embed.add_field(name="Booster Cut", value=format(int(boosterfee),',d'), inline=False)
        embed.add_field(name="Advertiser Cut", value=format(int(adfee),',d'), inline=False)
        embed.add_field(name="Management Cut", value=format(int(managementfee),',d'), inline=False)
        if type == 'M+':
            embed.add_field(name="Keyholder Cut", value=format(int(keyholderfee),',d'), inline=False)
        embed.add_field(name="Faction of the Boost", value=boostFaction, inline=False)
        embed.add_field(name="Location of the Gold", value=f"{goldRealm}-{goldFaction}", inline=False)
        embed.add_field(name="Advertiser", value=f"{advertiser.mention} {'' if invoked else f'({advertiser.display_name})'}", inline=False)
        if not invoked:
            msg = await ctx.author.send(content=f"This is a preview of the completed {type} run. Do you want to post this run?", embed=embed)
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
            completedRun = {
                "id": str(msg.id),
                "type": type,
                "pot": pot,
                "goldRealm": goldRealm,
                "goldFaction": goldFaction,
                "boostFaction": boostFaction,
                "advertiser": advertiser,
                "booster1": booster1,
                "booster2": booster2,
                "booster3": booster3,
                "booster4": booster4,
                "keyholder": keyholder,
                "advertiserFee": adfee,
                "boosterFee": boosterfee,
                "managementFee": managementfee,
                "created_at": created_at,
            }

            added = await self.addToSheets(ctx.guild, ctx.author, completedRun)
            return added, msg

    async def addToSheets(self, guild, author, completedRun: json):
        if completedRun['type'] == 'M+':
            RANGE_NAME = "'Completed M+ Logs'!A12:M"
            VALUES = [completedRun['id'], completedRun['pot'], completedRun['goldRealm'], completedRun['goldFaction'], completedRun['advertiser'].display_name,
                    completedRun['booster1'].display_name, completedRun['booster2'].display_name, completedRun['booster3'].display_name,
                    completedRun['booster4'].display_name, completedRun['created_at'], completedRun['boostFaction'], completedRun['keyholder'].display_name]
        else:
            RANGE_NAME = "'MISC'!A3:O"
            VALUES = [completedRun['id'], completedRun['pot'], completedRun['goldRealm'], completedRun['goldFaction'], completedRun['type'], completedRun['advertiser'].display_name,
                    completedRun['booster1'].display_name, completedRun['booster2'].display_name if completedRun['booster2'] else "", completedRun['booster3'].display_name if completedRun['booster3'] else "",
                    completedRun['booster4'].display_name if completedRun['booster4'] else "", completedRun['advertiserFee'], completedRun['boosterFee'], completedRun['created_at'], completedRun['boostFaction']]

        SPREADSHEET_ID = self.client.config["SPREADSHEET_ID"]["MAIN"]
        allRows = self.client.sheet.getAllRows(SPREADSHEET_ID, f"{RANGE_NAME}")

        if not allRows:
            await author.send("Something went wrong with retrieving data from the sheets, please try again. If this continues please contact someone from Council or Management.")
            return False

        # Count starts at 11 or 2, because the first 11 or 2 rows are irrelevant
        rowCount = 11 if completedRun['type'] == 'M+' else 2
        updated = False

        # Loop through all the 'filled' rows (rows with only a checkmark are seen as filled)
        for i in range(len(allRows)):
            rowCount += 1

            if completedRun['type'] == 'M+':
                UPDATE_RANGE = f"'Completed M+ Logs'!A{rowCount}"
                emptyRow = (not allRows[i] or not allRows[i][0] and not allRows[i][1] and not allRows[i][2] and not allRows[i][3] and not allRows[i][4] and not allRows[i][5]
                    and not allRows[i][6] and not allRows[i][7] and not allRows[i][8] and not allRows[i][9] and not allRows[i][10] and not allRows[i][11])
            else:
                UPDATE_RANGE = f"'MISC'!A{rowCount}"
                emptyRow = (not allRows[i] or not allRows[i][0] and not allRows[i][1] and not allRows[i][2] and not allRows[i][3] and not allRows[i][4] and not allRows[i][5]
                    and not allRows[i][6] and not allRows[i][7] and not allRows[i][8] and not allRows[i][9] and not allRows[i][10] and not allRows[i][11] and not allRows[i][12] and not allRows[i][13])

            # If the encountered row is completely empty, but does have a checkmark
            if emptyRow:

                # Update that row
                result = self.client.sheet.update(SPREADSHEET_ID, UPDATE_RANGE, VALUES)
                updated = True;
                break

        # If no rows were updated, then add it
        if not updated:
            result = self.client.sheet.add(SPREADSHEET_ID, RANGE_NAME, VALUES)

        if result:
            receipt = discord.Embed(title=f"{completedRun['type']} receipt",
                                    description=(f"{completedRun['id']}\n"
                                                f"{format(int(completedRun['pot']),',d')}\n"
                                                f"{completedRun['goldFaction']}\n"
                                                f"{completedRun['goldRealm']}\n"
                                                f"{completedRun['type']}\n"
                                                f"{completedRun['advertiser'].display_name}\n"
                                                f"{completedRun['booster1'].display_name}\n"
                                                f"{completedRun['booster2'].display_name if completedRun['booster2'] else ''}\n"
                                                f"{completedRun['booster3'].display_name if completedRun['booster3'] else ''}\n"
                                                f"{completedRun['booster4'].display_name if completedRun['booster4'] else ''}"),
                                    color=0x9013FE)
            receipt.set_thumbnail(url="https://cdn.discordapp.com/attachments/699709321180741642/842730940744466452/Final_Logo_Render.png")
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

def setup(client):
    client.add_cog(Completed(client))
