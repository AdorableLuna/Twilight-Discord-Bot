import discord
import re

from discord.utils import get

class Helper(object):
    def __init__(self, client):
        self.client = client

    def checkName(self, guild, name):
        if re.search('^<@[0-9>]+$', name):
            name = name[2:-1]
            member = guild.get_member(int(name))

            return member.name
        elif re.search('^<@![0-9>]+$', name):
            name = name[3:-1]
            member = guild.get_member(int(name))

            return member.nick
        else:
            return name

    def getMemberByMention(self, guild, name):
        if re.search('^<@[0-9>]+$', name):
            name = name[2:-1]
            member = guild.get_member(int(name))

            return member
        elif re.search('^<@![0-9>]+$', name):
            name = name[3:-1]
            member = guild.get_member(int(name))
            return member

    def getRole(self, guild, role):
        return discord.utils.find(lambda r: r.name == role, guild.roles)

    def getRoleById(self, guild, role):
        role = re.sub('[<@&>]', '', role)
        return discord.utils.find(lambda r: r.id == int(role), guild.roles)

    def containsUserMention(self, string):
        return re.search('(?=.*<)(?=.*@)(?=.*!)(?=.*>)', string)

    def containsRoleMention(self, string):
        return re.search('(?=.*<)(?=.*@)(?=.*&)(?=.*>)', string)
