from discord.ext import commands
from helpers import helper

class Maincog(commands.Cog):

    def __init__(self, client, whitelistedChannels = [], whitelistedUsers = []):
        self.client = client
        self.helper = helper.Helper(self.client)
        self.whitelistedChannels = whitelistedChannels
        self.whitelistedUsers = whitelistedUsers

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

    async def convertMember(self, ctx, member):
        return await commands.MemberConverter().convert(ctx, member)

def setup(client):
    client.add_cog(Maincog(client))
