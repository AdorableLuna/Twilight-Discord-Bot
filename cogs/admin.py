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

def setup(client):
    client.add_cog(Admin(client))
