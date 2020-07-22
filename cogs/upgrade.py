import discord
import requests
import json

from discord.utils import get
from discord.ext import commands

with open('./config.json', 'r') as cjson:
    config = json.load(cjson)

class Upgrade(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        self.guild = self.client.get_guild(config["GUILD_ID"])
        self.channelID = 728967077381275658
        self.tankEmoji = self.client.get_emoji(714930608266018859)
        self.healerEmoji = self.client.get_emoji(714930600267612181)
        self.dpsEmoji = self.client.get_emoji(714930578461425724)

    @commands.command()
    async def upgrade(self, ctx):
        if ctx.message.channel.id != self.channelID: return

        author = ctx.message.author
        character = ctx.message.content[9:].split('-')
        name = character[0]
        realm = character[1]
        link = f"https://raider.io/api/v1/characters/profile?region=eu&realm={realm}&name={name}&fields=mythic_plus_scores_by_season%3Acurrent"

        response = requests.get(link)

        if response.ok:
            data = json.loads(response.content)

            if "mythic_plus_scores_by_season" in data:
                scores = data["mythic_plus_scores_by_season"][0]["scores"]
                faction = data['faction'].capitalize()
                allScore = scores["all"]
                tankScore = scores["tank"]
                healerScore = scores["healer"]
                dpsScore = scores["dps"]

                userRoles = author.roles
                rareRole = self.getRole("Rare")
                epicRole = self.getRole("Epic")
                legendaryRole = self.getRole("Legendary")
                highKeyRole = self.getRole(f"Highkey Booster {faction}")
                role = ""

                if rareRole in userRoles and epicRole in userRoles and legendaryRole in userRoles:
                    description = "You already have all the roles."
                else:
                    if allScore > 2400 and faction == "Alliance" or allScore > 2500 and faction == "Horde":
                        role = rareRole
                        await author.add_roles(role)
                    if allScore > 2700 and faction == "Alliance" or allScore > 2900 and faction == "Horde":
                        role = epicRole
                        await author.add_roles(role, highKeyRole)
                    if allScore > 3500 and faction == "Alliance" or allScore > 3900 and faction == "Horde":
                        role = legendaryRole
                        await author.add_roles(role, highKeyRole)

                    if role:
                        description = f"You have been granted the role {role.mention}.\n\n"
                    else:
                        description = "Your character is not yet eligible for any other roles.\n\n"

                    description += f"""**Required RaiderIO Score Per Rank:**
                                   {legendaryRole.mention}: {"3500" if faction == "Alliance" else "3900"}
                                   {epicRole.mention}: {"2700" if faction == "Alliance" else "2900"}
                                   {rareRole.mention}: {"2400" if faction == "Alliance" else "2500"}"""

                embed=discord.Embed(title=f"{data['name']}-{data['realm']}", description=description, color=0x5cf033)
                embed.set_thumbnail(url=data["thumbnail_url"])
                embed.add_field(name=self.tankEmoji, value=tankScore, inline=True)
                embed.add_field(name=self.healerEmoji, value=healerScore, inline=True)
                embed.add_field(name=self.dpsEmoji, value=dpsScore, inline=True)
                embed.set_footer(text="Data retrieved with Raider.IO API")
                await ctx.message.channel.send(embed=embed)
        else:
            await ctx.message.channel.send("Could not retrieve Raider.IO character. Make sure the name-realm is correct and exists.")

    def getRole(self, role):
        return discord.utils.find(lambda r: r.name == role, self.guild.roles)

def setup(client):
    client.add_cog(Upgrade(client))
