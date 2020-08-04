import discord
import re
import json

from discord.utils import get

with open('./config.json', 'r') as cjson:
    config = json.load(cjson)

class Helper(object):
    def __init__(self, client):
        self.client = client
        self.guild = self.client.get_guild(config["GUILD_ID"])

    def checkName(self, name):
        if re.search('^<@[0-9>]+$', name):
            name = name[2:-1]
            member = self.guild.get_member(int(name))

            return self.guild.get_member(int(name)).name
        elif re.search('^<@![0-9>]+$', name):
            name = name[3:-1]
            member = self.guild.get_member(int(name))

            return self.guild.get_member(int(name)).display_name
        else:
            return name

    def getRole(self, role):
        return discord.utils.find(lambda r: r.name == role, self.guild.roles)

    def getRoleById(self, role):
        role = re.sub('[<@&>]', '', role)
        return discord.utils.find(lambda r: r.id == int(role), self.guild.roles)

    def containsRoleMention(self, string):
        return re.search('(?=.*<)(?=.*@)(?=.*&)(?=.*>)', string)
