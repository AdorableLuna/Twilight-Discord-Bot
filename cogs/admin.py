import discord
import re

from discord.ext import commands
from helpers import helper

class Admin(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.helper = helper.Helper(self.client)
        self.cogsFolder = 'cogs'

    def is_developer():
        def predicate(ctx):
            return ctx.message.author.id == 251424390275661824
        return commands.check(predicate)

    @commands.group(name='load', hidden=True, invoke_without_command=True)
    @is_developer()
    async def load(self, ctx, *, module):
        """Loads a module."""
        try:
            self.client.load_extension(f'{self.cogsFolder}.{module}')
            await ctx.send(f'Succesfully loaded `{module}`')
        except commands.ExtensionError as e:
            await ctx.send(f'{e.__class__.__name__}: {e}')

    @commands.group(name='unload', hidden=True, invoke_without_command=True)
    @is_developer()
    async def unload(self, ctx, *, module):
        """Unloads a module."""
        try:
            self.client.unload_extension(f'{self.cogsFolder}.{module}')
            await ctx.send(f'Succesfully unloaded `{module}`')
        except commands.ExtensionError as e:
            await ctx.send(f'{e.__class__.__name__}: {e}')

    @commands.group(name='reload', hidden=True, invoke_without_command=True)
    @is_developer()
    async def reload(self, ctx, *, module):
        """Reloads a module."""
        try:
            self.client.reload_extension(f'{self.cogsFolder}.{module}')
            await ctx.send(f'Succesfully reloaded `{module}`')
        except commands.ExtensionError as e:
            await ctx.send(f'{e.__class__.__name__}: {e}')

    @commands.command()
    @commands.dm_only()
    async def activity(self, ctx, *, activity):
        if ctx.author.id == 251424390275661824:
            await self.client.change_presence(activity=discord.Game(name=activity))

    @commands.group(name='post', hidden=True, invoke_without_command=True)
    @commands.has_any_role("Staff", "Management", "Council")
    async def post(self, ctx, *, text):
        """Posts a message."""
        channelRegex = "<#.*?>"
        channelIdRegex = "\d+"

        channelString = re.findall(channelRegex, text)[0]
        channelId = re.search(channelIdRegex, channelString).group()
        channel = await self.client.fetch_channel(channelId)

        if ctx.message.attachments:
            image = await ctx.message.attachments[0].to_file()

            result = text.replace(channelString, '', 1)
            if result != '':
                if result[0].isspace():
                    result = result.replace(' ', '', 1)

            await ctx.message.delete()
            await channel.send(content=result, file=image)
        else:
            result = text.replace(channelString, '', 1)
            if result != '':
                if result[0].isspace():
                    result = result.replace(' ', '', 1)

                await ctx.message.delete()
                await channel.send(result)

    @commands.group(name='editPost', hidden=True, invoke_without_command=True)
    @commands.has_any_role("Council")
    async def editPost(self, ctx, channel_id, message_id, *, text):
        """Updates the post."""
        channel = await self.client.fetch_channel(channel_id)
        message = await channel.fetch_message(message_id)

        await message.edit(content=text)
        await ctx.message.delete()

    @commands.group(name='updatePrices', hidden=True, invoke_without_command=True)
    @commands.has_any_role("Council")
    async def updatePrices(self, ctx, *, category):
        """Updates the prices."""
        SPREADSHEET_ID = self.client.config["SPREADSHEET_ID"]["PRICES"]
        allRows = self.client.sheet.getAllRows(SPREADSHEET_ID, f"'{category} Pricelist'")
        footerRows = self.client.sheet.getAllRows(SPREADSHEET_ID, f"'Footer'")[2:]
        channel = await self.client.fetch_channel(int(allRows[2][0]))

        mention = ""
        firstPost = True

        if category.lower() == "deal":
            dealMessage = self.client.sheet.getAllRows(SPREADSHEET_ID, f"'Deal Message'")[2][0]
            mention += dealMessage + " @everyone"

        # Prices
        # Start at every 3rd item in list
        for i in range(2, len(allRows), 3):
            color = int(allRows[i][3].replace('#', '0x'), 0)

            if allRows[i][1]:
                imageEmbed = discord.Embed(color=color)
                imageEmbed.set_image(url=allRows[i][1])

            embed = discord.Embed(color=color, title=allRows[i][4])

            if allRows[i][2]:
                embed.set_image(url=allRows[i][2])

            for j in range(5, len(allRows[i]), 2):
                embed.add_field(name=''.join(allRows[i][j].replace(r'\n', '\n')) or '\u200b',
                                value=''.join(allRows[i][j+1].replace(r'\n', '\n')) or '\u200b',
                                inline=allRows[i+1][j] == 'TRUE')

            if allRows[i][1]:
                await channel.send(content=mention if firstPost else "", embed=imageEmbed)
                firstPost = False

            await channel.send(content=mention if firstPost else "", embed=embed)
            firstPost = False

        # Footer
        color = int(footerRows[0][2].replace('#', '0x'), 0)
        footerEmbed = discord.Embed(color=color, title=footerRows[0][3])

        if footerRows[0][1]:
            footerEmbed.set_image(url=footerRows[0][1])

        if footerRows[0][5]:
            footerEmbed.set_footer(text=footerRows[0][5], icon_url=footerRows[0][4] if footerRows[0][4] else "")

        for k in range(6, len(footerRows[0]), 2):
            footerEmbed.add_field(name=''.join(footerRows[0][k].replace(r'\n', '\n')) or '\u200b',
                            value=''.join(footerRows[0][k+1].replace(r'\n', '\n')) or '\u200b',
                            inline=footerRows[0][k] == 'TRUE')

        await channel.send(embed=footerEmbed)
        await ctx.message.delete()

    @commands.group(name='editDeals', hidden=True, invoke_without_command=True)
    @commands.has_any_role("Council")
    async def editDeals(self, ctx, *, message_id):
        """Updates the prices."""
        SPREADSHEET_ID = self.client.config["SPREADSHEET_ID"]["PRICES"]
        allRows = self.client.sheet.getAllRows(SPREADSHEET_ID, f"'Deal Pricelist'")

        dealMessage = self.client.sheet.getAllRows(SPREADSHEET_ID, f"'Deal Message'")[2][0]
        mention = dealMessage + " @everyone"
        message = await ctx.fetch_message(message_id)

        # Prices
        # Start at 3rd item in list
        color = int(allRows[2][3].replace('#', '0x'), 0)

        embed = discord.Embed(color=color, title=allRows[2][4])

        if allRows[2][2]:
            embed.set_image(url=allRows[2][2])

        for j in range(5, len(allRows[2]), 2):
            embed.add_field(name=''.join(allRows[2][j].replace(r'\n', '\n')) or '\u200b',
                            value=''.join(allRows[2][j+1].replace(r'\n', '\n')) or '\u200b',
                            inline=allRows[2+1][j] == 'TRUE')

        await message.edit(content=mention, embed=embed)
        await ctx.message.delete()

def setup(client):
    client.add_cog(Admin(client))
