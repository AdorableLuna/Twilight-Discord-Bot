import discord
import os.path
import re

from cogs.maincog import Maincog
from cryptography.fernet import Fernet
from discord.ext import commands

class Cryptography(Maincog):

    def __init__(self, client):
        Maincog.__init__(self, client, whitelistedChannels = [741460284887269401])

        if not os.path.exists('secret.key'):
            self.generate_key()

    def generate_key(self):
        """
        Generates a key and save it into a file
        """
        key = Fernet.generate_key()
        with open("secret.key", "wb") as key_file:
            key_file.write(key)

    def load_key(self):
        """
        Load the previously generated key
        """
        return open("secret.key", "rb").read()

    @commands.command(aliases=['enc'])
    async def encrypt(self, ctx):
        """
        Encrypts a message
        """

        if isinstance(ctx.message.channel, discord.DMChannel):
            key = self.load_key()
            message = ctx.message.content.split(" ", 1)[1]
            encoded_message = message.encode()
            f = Fernet(key)
            encrypted_message = f.encrypt(encoded_message)

            await ctx.message.channel.send(encrypted_message.decode())
            return

    @commands.command(aliases=['dec'])
    async def decrypt(self, ctx):
        """
        Decrypts a message
        """
        if isinstance(ctx.message.channel, discord.DMChannel): return
        if not self.checkIfAllowedChannel(ctx.channel.id): return

        key = self.load_key()
        f = Fernet(key)
        content = re.split(r'[\n ]', ctx.message.content)
        content.pop(0)

        decoded_message = ""

        for message in content:
            encrypted_message = message.encode()
            decrypted_message = f.decrypt(encrypted_message)
            decoded_message += decrypted_message.decode() + "\n"

        await ctx.message.channel.send(decoded_message)
        return

def setup(client):
    client.add_cog(Cryptography(client))
