from datetime import datetime
from discord.ext import commands
from helpers import helper
from pytz import timezone

class Maincog(commands.Cog):

    def __init__(self, client, whitelistedChannels = [], whitelistedUsers = []):
        self.client = client
        self.helper = helper.Helper(self.client)
        self.whitelistedChannels = whitelistedChannels
        self.whitelistedUsers = whitelistedUsers

    async def cog_command_error(self, ctx, error):
        created_at = datetime.now(timezone('Europe/Paris')).strftime("%d-%m %H:%M:%S")
        await ctx.send(f'{ctx.author.mention}, there was an error with your command. Please check if your command has the correct format, otherwise notify the staff.')
        print(f"{created_at} .{ctx.command.name}:", error)

    def checkIfAllowedChannel(self, channel_id):
        if channel_id in self.whitelistedChannels:
            return True
        else:
            return False

    def checkIfAllowedUser(self, user_id):
        if user_id in self.whitelistedUsers:
            return True
        else:
            return False

    def checkIfUserIsItself(self, author):
        if author == self.client.user:
            return True
        else:
            return False

def setup(client):
    client.add_cog(Maincog(client))
