import discord
import re

from discord.ext import commands

class Admin(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.cogsFolder = 'cogs'

    @commands.group(name='load', hidden=True, invoke_without_command=True)
    @commands.has_any_role("Staff", "Management", "Council")
    async def load(self, ctx, *, module):
        """Loads a module."""
        try:
            self.client.load_extension(f'{self.cogsFolder}.{module}')
            await ctx.send(f'Succesfully loaded `{module}`')
        except commands.ExtensionError as e:
            await ctx.send(f'{e.__class__.__name__}: {e}')

    @commands.group(name='unload', hidden=True, invoke_without_command=True)
    @commands.has_any_role("Staff", "Management", "Council")
    async def unload(self, ctx, *, module):
        """Unloads a module."""
        try:
            self.client.unload_extension(f'{self.cogsFolder}.{module}')
            await ctx.send(f'Succesfully unloaded `{module}`')
        except commands.ExtensionError as e:
            await ctx.send(f'{e.__class__.__name__}: {e}')

    @commands.group(name='reload', hidden=True, invoke_without_command=True)
    @commands.has_any_role("Staff", "Management", "Council")
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

def setup(client):
    client.add_cog(Admin(client))
