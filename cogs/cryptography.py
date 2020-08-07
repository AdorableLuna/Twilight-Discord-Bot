import discord
import os.path

from cryptography.fernet import Fernet
from discord.ext import commands

class Cryptography(commands.Cog):

    def __init__(self, client):
        self.client = client

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
    @commands.has_any_role("Staff", "Management", "Council")
    async def decrypt(self, ctx):
        """
        Decrypts a message
        """

        key = self.load_key()
        f = Fernet(key)
        encrypted_message = ctx.message.content.split(" ", 1)[1].encode()
        decrypted_message  = f.decrypt(encrypted_message)

        await ctx.message.channel.send(decrypted_message.decode())
        return

def setup(client):
    client.add_cog(Cryptography(client))
