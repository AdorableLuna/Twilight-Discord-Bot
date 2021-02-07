import discord
import requests
import json

from cogs.maincog import Maincog
from discord.ext import commands

class Upgrade(Maincog):

    def __init__(self, client):
        Maincog.__init__(self, client, whitelistedChannels = [728967077381275658])
        self.client.loop.create_task(self.on_ready_init())

    async def on_ready_init(self):
        await self.client.wait_until_ready()
        self.tankEmoji = self.client.get_emoji(714930608266018859)
        self.healerEmoji = self.client.get_emoji(714930600267612181)
        self.dpsEmoji = self.client.get_emoji(714930578461425724)

    @commands.command()
    async def upgrade(self, ctx):
        if not self.checkIfAllowedChannel(ctx.channel.id): return

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
                rareRole = self.helper.getRole(ctx.guild, "Rare")
                epicRole = self.helper.getRole(ctx.guild, "Epic")
                legendaryRole = self.helper.getRole(ctx.guild, "Legendary")
                highKeyRole = self.helper.getRole(ctx.guild, f"Highkey Booster {faction}")

                rareRoleOld = self.helper.getRole(ctx.guild, "Rare (old)")
                epicRoleOld = self.helper.getRole(ctx.guild, "Epic (old)")
                legendaryRoleOld = self.helper.getRole(ctx.guild, "Legendary (old)")

                role = ""

                # Remove old roles
                await author.remove_roles(rareRoleOld)
                await author.remove_roles(epicRoleOld)
                await author.remove_roles(legendaryRoleOld)

                # Remove highkey role if not epic or legendary
                if epicRole not in userRoles:
                    await author.remove_roles(highKeyRole)

                if rareRole in userRoles and epicRole in userRoles and legendaryRole in userRoles:
                    description = "You already have all the roles."
                else:
                    if allScore > 1100 and faction == "Alliance" or allScore > 1100 and faction == "Horde":
                        role = rareRole
                        await author.add_roles(role)
                    if allScore > 1500 and faction == "Alliance" or allScore > 1500 and faction == "Horde":
                        role = epicRole
                        await author.add_roles(role, highKeyRole)
                    if allScore > 1800 and faction == "Alliance" or allScore > 1800 and faction == "Horde":
                        role = legendaryRole
                        await author.add_roles(role, highKeyRole)

                    if role:
                        description = f"You have been granted the role {role.mention}.\n\n"
                    else:
                        description = "Your character is not yet eligible for any other roles.\n\n"

                    description += f"""**Required RaiderIO Score Per Rank:**
                                   {legendaryRole.mention}: {"1800" if faction == "Alliance" else "1800"}
                                   {epicRole.mention}: {"1500" if faction == "Alliance" else "1500"}
                                   {rareRole.mention}: {"1100" if faction == "Alliance" else "1100"}"""

                embed=discord.Embed(title=f"{data['name']}-{data['realm']}", description=description, color=0x5cf033)
                embed.set_thumbnail(url=data["thumbnail_url"])
                embed.add_field(name=self.tankEmoji, value=tankScore, inline=True)
                embed.add_field(name=self.healerEmoji, value=healerScore, inline=True)
                embed.add_field(name=self.dpsEmoji, value=dpsScore, inline=True)
                embed.set_footer(text="Data retrieved with Raider.IO API")
                await ctx.message.channel.send(embed=embed)
        else:
            await ctx.message.channel.send("Could not retrieve Raider.IO character. Make sure the name-realm is correct and exists.")

def setup(client):
    client.add_cog(Upgrade(client))
