import discord
import re
import datetime
import json
import chat_exporter
import io

from cogs.maincog import Maincog
from discord.utils import get
from discord.ext import commands
from db import dbconnection as dbc

class Torghast(Maincog):

    def __init__(self, client):
        Maincog.__init__(self, client)
        self.dbc = dbc.DBConnection()
        self.cancelEmoji = "\U0000274C"
        self.doneEmoji = "\U00002705"
        self.trashEmoji = "\U0001F5D1"
        self.miscCategory = 848661179768242176

        with open('taxes.json', 'r') as taxesFile:
            self.taxes = json.load(taxesFile)
            taxesFile.close()

        self.client.loop.create_task(self.on_ready_init())

    async def on_ready_init(self):
        await self.client.wait_until_ready()
        self.completedChannel = self.client.get_channel(731479403862949928)
        self.bookingLogsChannel = self.client.get_channel(848935122802966578)
        self.torghastEmoji = self.client.get_emoji(848693646088994866)

    def check_if_active_boost_channel(self, channel_name):
        reg = re.compile("(horde|alliance)-\w*-(boost)")
        return re.match(reg, channel_name)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if self.checkIfUserIsItself(payload.member): return
        user = payload.member
        channel = self.client.get_channel(payload.channel_id)
        if not channel: return
        if isinstance(channel, discord.DMChannel): return
        if not self.check_if_active_boost_channel(channel.name): return

        if str(payload.emoji) == str(self.trashEmoji):
            messages = await channel.history().flatten()
            group_id = messages[-1].id

            groupQuery = f"SELECT `advertiser` FROM torghast.group WHERE id = '{group_id}'"
            author = self.dbc.select(groupQuery)
            author = author["advertiser"].split(" ", 1)[0]

            if user.mention == author:
                await self.createTranscript(channel, user)
                await channel.delete()
            return

        message = await channel.fetch_message(payload.message_id)

        if not message.embeds: return
        id = message.id
        guild = self.client.get_guild(payload.guild_id)

        groupQuery = f"SELECT * FROM torghast.group WHERE id = '{id}'"
        group = self.dbc.select(groupQuery)

        if group is None: return
        author = group["advertiser"]
        author = author.split(" ", 1)[0]

        if group["created"] and not group["completed"]:
            if str(payload.emoji) == str(self.doneEmoji) and user.mention == author:
                realmFaction = group['payment_realm'].rsplit("-", 1)

                # If faction is specified, then overwrite the default channel faction
                if(len(realmFaction) == 2):
                    if "horde" in realmFaction[1].lower():
                        paymentFaction = "H"
                    elif "h" in realmFaction[1].lower():
                        paymentFaction = "H"
                    elif "alliance" in realmFaction[1].lower():
                        paymentFaction = "A"
                    elif "a" in realmFaction[1].lower():
                        paymentFaction = "A"

                # Otherwise, just use default channel faction
                else:
                    if "horde" in channel.name:
                        paymentFaction = "H"
                    elif "alliance" in channel.name:
                        paymentFaction = "A"

                paymentRealm = realmFaction[0]

                gold_pot = group["gold_pot"]
                if "k" in gold_pot:
                    gold_pot = gold_pot.replace('k', '')
                    gold_pot = str(gold_pot) + "000"

                usernameRegex = "<@.*?>"
                nicknameRegex = "<@!.*?>"
                party = re.compile("(%s|%s)" % (usernameRegex, nicknameRegex)).findall(message.embeds[0].description)

                ctx = await self.client.get_context(message)
                ctx.author = get(ctx.guild.members, mention=author)
                result = await ctx.invoke(self.client.get_command('completed'), 'Torghast', group['faction'], gold_pot, f"{paymentRealm}-{paymentFaction}", author, party[0])

                if result[0]:
                    await channel.send(f"{self.doneEmoji} Succesfully added the Torghast run to the sheets!\n"
                                       f"Group id: {id}\n"
                                       f"{result[1].jump_url}")
                    await message.clear_reaction(self.doneEmoji)

                    msg = await channel.send(f"{author}, click the {self.trashEmoji} to delete this channel.")
                    await msg.add_reaction(self.trashEmoji)
                else:
                    await result[1].delete()
                    await channel.send(f"{self.cancelEmoji} Something went wrong when trying to add the Torghast run to the sheets. Please add it manually in {self.completedChannel.mention}\n"
                                       f"Group id: {id}")

                query = f"""UPDATE torghast.group
                       SET completed = 1
                       WHERE id = {id}"""
                self.dbc.insert(query)

            return

        if str(payload.emoji) == str(self.torghastEmoji):
            data = {"user": user, "faction": group["faction"]}
            if not await self.checkRoles(guild, data):
                await message.remove_reaction(payload.emoji, user)
                return

            query = f"""INSERT INTO torghast.booster (groupid, `user`)
                       VALUES ('{id}', '{user.mention}')"""
            self.dbc.insert(query)

            await self.createGroup(message, user.mention)

        if str(payload.emoji) == str(self.cancelEmoji):
            if user.mention == author:
                if group["created"]:
                    await user.send(content="Don't forget to post the completed run.", embed=message.embeds[0])
                else:
                    await self.cancelGroup(guild, message)
                    await self.createTranscript(channel, user)

                await message.channel.delete()

    @commands.check(lambda ctx: False)
    @commands.command()
    @commands.has_any_role("Trainee Advertiser", "Advertiser", "Management", "Council")
    async def generate_torghast(self, ctx, advertiserNameRealm: str, paymentRealm: str, layer: str, pot: str):
        channel = ctx.message.channel.name

        if "horde" in channel:
            faction = "Horde"
        elif "alliance" in channel:
            faction = "Alliance"

        advertiser = f"{ctx.message.author.mention} ({advertiserNameRealm})"
        layer = layer.replace("l", "L")
        pot = pot.lower()

        if "k" in pot:
            goldPot = pot.replace('k', '')
            goldPot = str(goldPot) + "000"
        else:
            goldPot = pot
        boosterCut = int(goldPot) * round(((self.taxes["torghast"]["boosters"] / 100)), 3)
        advertiserCut = int(goldPot) * round(((self.taxes["torghast"]["advertiser"] / 100)), 3)
        managementCut = int(goldPot) * round(((self.taxes["torghast"]["management"] / 100)), 3)

        embed = discord.Embed(title=f"Generating {layer} run!", description="Click on the reaction below the post to accept this boost.\n" +
                                    "First come first served.\n", color=0x9013FE)
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/699709321180741642/842730940744466452/Final_Logo_Render.png")
        embed.add_field(name="Gold Pot", value=pot, inline=True)
        embed.add_field(name="Booster Cut", value=f"{boosterCut:n}", inline=True)
        embed.add_field(name="Advertiser Cut", value=f"{advertiserCut:n}", inline=True)
        embed.add_field(name="Management Cut", value=f"{managementCut:n}", inline=True)
        embed.add_field(name="Boost Faction", value=f"{faction}", inline=True)
        embed.add_field(name="Payment Realm", value=paymentRealm, inline=True)
        embed.add_field(name="Layer", value=layer, inline=True)
        embed.add_field(name="Advertiser", value=advertiser, inline=False)

        await ctx.message.delete()

        torghastRole = self.helper.getRole(ctx.guild, f"Torghast {faction}")
        advertiserTrainerRole = self.helper.getRole(ctx.guild, "Advertiser Trainer")
        managementRole = self.helper.getRole(ctx.guild, "Management")
        category = discord.utils.get(ctx.guild.categories, id=self.miscCategory)
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False, read_messages=False, send_messages=False, add_reactions=False),
            torghastRole: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, add_reactions=False, read_message_history=True),
            advertiserTrainerRole: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, add_reactions=False, read_message_history=True),
            managementRole: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, add_reactions=False, read_message_history=True),
            ctx.author: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, add_reactions=False, read_message_history=True),
        }

        await ctx.channel.edit(name=f"{faction}-{layer}-boost", overwrites=overwrites, reason="Automatic Torghast booking made.")
        await ctx.channel.purge(limit=None, check=lambda msg: not msg.pinned)
        msg = await ctx.channel.send(content=torghastRole.mention, embed=embed)
        embed.set_footer(text=f"Group id: {msg.id}.")
        await msg.edit(embed=embed)

        query = """INSERT INTO torghast.group (id, title, faction, payment_realm, gold_pot, booster_cut, layer, advertiser, footer)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        values = (msg.id, embed.title, faction, paymentRealm, pot, boosterCut, layer, advertiser, embed.footer.text)
        self.dbc.insert(query, values)

        # Accept
        await msg.add_reaction(self.torghastEmoji)

        # Cancel
        await msg.add_reaction(self.cancelEmoji)

    async def cancelGroup(self, guild, message):
        booster = self.getGroup(message)

        if booster:
            user = self.helper.getMemberByMention(guild, booster)
            await user.send("Your group was cancelled by the advertiser.")

    def getGroup(self, message):
        id = message.id

        boosterQuery = f"SELECT * FROM torghast.booster WHERE groupid = '{id}'"
        booster = self.dbc.select(boosterQuery, True)
        return booster[0]['user'] if booster else ''

    async def createGroup(self, message, booster):
        query = f"""UPDATE torghast.group
                SET created = 1
                WHERE id = {message.id}"""
        self.dbc.insert(query)

        embed = message.embeds[0]

        query = f"SELECT layer FROM torghast.group WHERE id = '{message.id}'"
        group = self.dbc.select(query)

        advertiser = embed.fields[7].value.split(" ", 1)
        advertiserCharacter = re.findall('\(([^)]+)', advertiser[1])[0]

        embed.title = f"Generated {group['layer']} Group"
        embed.description = (f"{self.torghastEmoji} {booster}\n\n" +
                             f"Please whisper `/w {advertiserCharacter} invite`")
        embed.set_footer(text=f"{embed.footer.text} Group created at: {datetime.datetime.now().strftime('%H:%M:%S')}")
        editedmsg = await message.edit(embed=embed)

        createdMessage = (f"{self.torghastEmoji} {booster}\nPlease whisper `/w {advertiserCharacter} invite`. See the message above for more details.\n" +
                  f"Group id: {message.id}")
        await message.channel.send(createdMessage)

        reactions = message.reactions
        for reaction in reactions[:]:
            await reaction.clear()

        await message.add_reaction(self.doneEmoji)
        await message.add_reaction(self.trashEmoji)

    async def checkRoles(self, guild, data):
        isValid = False
        userRoles = data["user"].roles

        torghastRole = self.helper.getRole(guild, f"Torghast {data['faction']}")
        if torghastRole in userRoles:
            isValid = True
        else:
            await data['user'].send(f"You do **NOT** have the required `{torghastRole}` role to accept this boost.")
            return False

        return isValid

    async def createTranscript(self, channel, user):
        embed = discord.Embed(title="Torghast Transcript", color=0x9013FE)
        embed.set_thumbnail(url="https://cdn.discordapp.com/icons/629729313520091146/a_c708c65e803287d010ea489dd43383be.gif?size=1024")
        embed.add_field(name="Advertiser", value=user.mention, inline=True)
        embed.add_field(name="Advertiser ID", value=user.id, inline=True)
        embed.add_field(name="Section", value=channel.category, inline=True)
        embed.add_field(name="Deleted By", value=user.mention, inline=True)
        embed.add_field(name="Channel Name", value=channel.name, inline=True)

        transcript = await chat_exporter.export(channel, set_timezone="Europe/Amsterdam")

        if transcript is None:
            await self.bookingLogsChannel.send(f"Transcript could not be created for channel: {channel.name}")
            return

        transcript_file = discord.File(io.BytesIO(transcript.encode()),
                                        filename=f"transcript-{channel.name}.html")

        msg = await self.bookingLogsChannel.send(embed=embed, file=transcript_file)
        embed.add_field(name="Transcript", value=f"[Click Here]({msg.attachments[0].url})", inline=True)
        await msg.edit(embed=embed)

def setup(client):
    client.add_cog(Torghast(client))
